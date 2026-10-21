"""Additive schema migrations for the existing SQLite database.

The app relies on db.create_all(), which creates NEW tables but never alters existing
ones. Every column added to models.py after a database already exists must be listed
here. Run from the repo root or from backend/:

    python backend/migrate.py

Idempotent: columns that already exist are skipped, and backfills only touch rows that
still need them, so re-running is always safe. New tables (route_control_points, etc.)
are created by db.create_all() on the next backend boot.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pothole_detection.db')

# (table, column, DDL fragment placed after "ADD COLUMN")
NEW_COLUMNS = [
    # control-point georeferencing
    ('videos', 'position_source', "position_source VARCHAR(20) DEFAULT 'none'"),
    ('detections', 'position_source', "position_source VARCHAR(20)"),
    # user-chosen video labels
    ('videos', 'display_name', "display_name VARCHAR(300)"),
    # why an analysis failed, shown to the user
    ('videos', 'error_message', "error_message VARCHAR(500)"),
    # road band set on the phone (horizon and bonnet lines)
    ('videos', 'road_top', "road_top FLOAT"),
    ('videos', 'road_bottom', "road_bottom FLOAT"),
    # AI check of each detection (services/damage_verifier.py)
    ('detections', 'ai_check_score', "ai_check_score FLOAT"),
]

# (label, SQL) — must be safe to re-run
#
# Damage-code remap: the project originally used a D10/D20/D30/D40 scheme that does not match
# RDD2022's own codes (CRDDC 2022: D00 longitudinal, D10 transverse, D20 alligator, D40 pothole).
# Rows written under the OLD scheme are recognisable by their label, which makes the remap
# idempotent: under the new scheme D10 means Transverse, so a D10 + "Longitudinal Crack" row can
# only be an old one. Applied to both detections and public_reports.
_OLD_CODE_REMAP = (
    "SET damage_type = CASE "
    " WHEN damage_type = 'D10' AND damage_label = 'Longitudinal Crack' THEN 'D00'"
    " WHEN damage_type = 'D20' AND damage_label = 'Transverse Crack'   THEN 'D10'"
    " WHEN damage_type = 'D30'                                         THEN 'D20'"
    " ELSE damage_type END "
    "WHERE (damage_type = 'D10' AND damage_label = 'Longitudinal Crack')"
    "   OR (damage_type = 'D20' AND damage_label = 'Transverse Crack')"
    "   OR  damage_type = 'D30'"
)

BACKFILL = [
    ("detections: old D10/D20/D30 codes -> RDD2022 D00/D10/D20", "UPDATE detections " + _OLD_CODE_REMAP),
    ("public_reports: old D10/D20/D30 codes -> RDD2022 D00/D10/D20", "UPDATE public_reports " + _OLD_CODE_REMAP),
    ("videos.position_source from gps_filename",
     "UPDATE videos SET position_source = 'gps_file' "
     "WHERE gps_filename IS NOT NULL AND (position_source IS NULL OR position_source = 'none')"),
    ("detections.position_source from latitude",
     "UPDATE detections SET position_source = "
     "CASE WHEN latitude IS NOT NULL THEN 'gps_file' ELSE 'none' END "
     "WHERE position_source IS NULL"),
    # Severity scoring was dropped; clear values written before that so nothing can surface them.
    ("detections: clear legacy severity values",
     "UPDATE detections SET severity = NULL, severity_score = NULL "
     "WHERE severity IS NOT NULL OR severity_score IS NOT NULL"),
    # Two system roles (thesis Fig. 3.5.1): every older role is road maintenance personnel.
    ("users: barangay/municipal/provincial/public/inspector -> personnel",
     "UPDATE users SET role = 'personnel' WHERE role IS NULL OR role NOT IN ('personnel', 'admin')"),
    # Self-registration is gone, so an account still waiting for approval can never be used.
    ("users: pending/rejected registrations -> inactive",
     "UPDATE users SET account_status = 'inactive' WHERE account_status IN ('pending', 'rejected')"),
    # The partner office is the LGU of Mendez-Nuñez, not the DPWH central office.
    ("users: DPWH Central Office -> Local Government Unit of Mendez-Nuñez",
     "UPDATE users SET lgu_name = 'Local Government Unit of Mendez-Nuñez', "
     "agency = 'Local Government Unit of Mendez-Nuñez', sector_level = 'municipal' "
     "WHERE lgu_name = 'DPWH Central Office'"),
]


def _has_column(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def migrate(db_path=DB_PATH):
    if not os.path.exists(db_path):
        print(f"[info] No database at {db_path} - nothing to migrate; create_all() will build it fresh.")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for table, column, ddl in NEW_COLUMNS:
        if _has_column(cur, table, column):
            print(f"[skip] {table}.{column} already present")
        else:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
            print(f"[add ] {table}.{column}")

    for label, sql in BACKFILL:
        cur.execute(sql)
        print(f"[fill] {label}: {cur.rowcount} row(s)")

    conn.commit()
    conn.close()
    print("[done] Migration complete")


if __name__ == '__main__':
    migrate()

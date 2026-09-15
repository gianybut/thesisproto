"""Delete raw uploaded survey videos after a retention period (thesis Sec 3.7, Data Handling).

Raw footage can contain faces, plates and house frontages; the detection records, snapshots and
annotated output do not. This removes only the ORIGINAL upload once processing has finished and
the retention period has passed. Detections, snapshots, the annotated video and the database row
are untouched.

    python backend/purge_uploads.py               # dry run: list what would be deleted
    python backend/purge_uploads.py --apply       # actually delete
    python backend/purge_uploads.py --days 14     # override the 30-day default

Run from the repo root or from backend/. Safe to schedule (Task Scheduler / cron).
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

RETENTION_DAYS = 30

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)


def purge(days=RETENTION_DAYS, apply=False):
    from app import create_app
    from models import Video

    app = create_app()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    freed = 0
    hit = 0

    with app.app_context():
        upload_dir = app.config['UPLOAD_FOLDER']
        # Only finished videos; an interrupted one may still need its original for a retry.
        candidates = Video.query.filter(
            Video.status == 'completed',
            Video.processed_date.isnot(None),
        ).all()

        for v in candidates:
            processed = v.processed_date
            if processed.tzinfo is None:
                processed = processed.replace(tzinfo=timezone.utc)
            if processed > cutoff:
                continue

            path = os.path.join(upload_dir, v.filename)
            if not os.path.exists(path):
                continue

            size = os.path.getsize(path)
            hit += 1
            freed += size
            age = (datetime.now(timezone.utc) - processed).days
            print(f"[{'del ' if apply else 'plan'}] video {v.id:>4}  {v.name[:40]:40s}  "
                  f"{size / 1024 / 1024:7.1f} MB  processed {age} days ago")
            if apply:
                os.remove(path)

    verb = 'Deleted' if apply else 'Would delete'
    print(f"\n{verb} {hit} raw upload(s), {freed / 1024 / 1024:.1f} MB, older than {days} days.")
    if not apply and hit:
        print("Re-run with --apply to delete.")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Purge raw uploads past the retention period.')
    p.add_argument('--days', type=int, default=RETENTION_DAYS, help=f'retention in days (default {RETENTION_DAYS})')
    p.add_argument('--apply', action='store_true', help='actually delete; default is a dry run')
    a = p.parse_args()
    purge(days=a.days, apply=a.apply)

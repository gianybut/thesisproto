"""Shared label database for the multi-user annotation site (deploy_annotation_site.md §3-§4).

    python tools/review_labels/annotate_db.py init       # build the frame table (safe to re-run)
    python tools/review_labels/annotate_db.py status     # counts per status / tier / split

Database: data/local/annotate/labels.db (SQLite, WAL), override with LABELS_DB.
Frames are the near-zone crops (data/local/frames_nz, the images yolo_nz trains on); boxes are YOLO
normalised to that crop, so resizing for the browser never changes a label.

Queue pool: train and val frames from data/local/splits.csv that
  - are not in a test group (G05, G13, G15 are frozen; the server refuses them too),
  - were not dropped by the 50 m val/test buffer (dropped_by_location = 0),
  - are not already reviewed in the single-reviewer tool (review_log.csv reviewed = yes),
  - survive thinning: at most one frame per 5 m of GPS track within each recording.
Thinned-out frames are not inserted. Re-running init adds new frames only and never touches labels.

priority (lower first), set by prelabel.py from the model's draft boxes (§4):
  1 train T1 (any D20/D10 draft)   2 val T1   3 train T2 (max conf 0.15-0.5)   4 val T2   5 T3   9 no draft yet
"""

import csv
import math
import os
import random
import sqlite3
import sys
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'local'
ANN = DATA / 'annotate'
DB_PATH = Path(os.environ.get('LABELS_DB') or ANN / 'labels.db')
FRAMES_DIR = Path(os.environ.get('FRAMES_DIR') or DATA / 'frames_nz')
CODES = ['D00', 'D10', 'D20', 'D40']
TEST_GROUPS = {'G05', 'G13', 'G15'}
LOCK_S = 600
THIN_M = 5.0

SCHEMA = """
CREATE TABLE IF NOT EXISTS frames (
  frame_id TEXT PRIMARY KEY, recording TEXT, route_group TEXT, split TEXT,
  tier TEXT, priority INTEGER DEFAULT 9, rnd REAL, status TEXT DEFAULT 'todo',
  locked_by TEXT, lock_expires REAL, version INTEGER DEFAULT 0,
  labeled_by TEXT, labeled_at REAL, max_conf REAL);
CREATE INDEX IF NOT EXISTS frames_queue ON frames(status, priority, rnd);
CREATE TABLE IF NOT EXISTS boxes (
  frame_id TEXT, class_id INTEGER, cx REAL, cy REAL, w REAL, h REAL, source TEXT, conf REAL);
CREATE INDEX IF NOT EXISTS boxes_frame ON boxes(frame_id);
CREATE TABLE IF NOT EXISTS events (
  frame_id TEXT, user TEXT, action TEXT, timestamp REAL, detail TEXT);
CREATE INDEX IF NOT EXISTS events_user ON events(user, timestamp);
"""


def read_csv(p):
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=15, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=NORMAL')
    c.execute('PRAGMA busy_timeout=15000')
    c.executescript(SCHEMA)
    return c


@contextmanager
def tx(c):
    """Write transaction that takes the write lock at once, so two users can never read the same todo
    frame and both claim it."""
    c.execute('BEGIN IMMEDIATE')
    try:
        yield c
        c.execute('COMMIT')
    except BaseException:
        c.execute('ROLLBACK')
        raise


def reviewed_frames():
    p = DATA / 'review_log.csv'
    return {r['frame'] for r in read_csv(p) if r['reviewed'] == 'yes'} if p.exists() else set()


def dist_m(a, b):
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])))


def candidate_frames():
    splits = read_csv(DATA / 'splits.csv')
    man = {r['frame']: r for r in read_csv(DATA / 'manifest.csv')}
    done = reviewed_frames()
    pool = [r for r in splits if r['split'] in ('train', 'val') and r['route_group'] not in TEST_GROUPS
            and r['dropped_by_location'] == '0' and r['frame'] not in done and (FRAMES_DIR / r['frame']).exists()]
    pool.sort(key=lambda r: (r['recording'], int(man[r['frame']]['second'])))
    keep, last = [], {}
    for r in pool:
        m = man[r['frame']]
        if m['lat']:
            p = (float(m['lat']), float(m['lon']))
            if r['recording'] in last and dist_m(p, last[r['recording']]) < THIN_M:
                continue
            last[r['recording']] = p
        keep.append(r)
    return keep, len(pool)


def init():
    keep, before = candidate_frames()
    rng = random.Random(0)
    c = connect()
    with tx(c):
        have = {r[0] for r in c.execute('SELECT frame_id FROM frames')}
        new = [(r['frame'], r['recording'], r['route_group'], r['split'], rng.random()) for r in keep
               if r['frame'] not in have]
        c.executemany('INSERT INTO frames(frame_id, recording, route_group, split, rnd) VALUES (?,?,?,?,?)', new)
    print(f'pool {before} frames, {len(keep)} after {THIN_M:g} m thinning; {len(new)} new rows, '
          f'{len(have)} already in {DB_PATH}')


def release_expired(c, now=None):
    c.execute("UPDATE frames SET status='todo', locked_by=NULL, lock_expires=NULL "
              "WHERE status='in_progress' AND lock_expires < ?", (now or time.time(),))
    c.execute("UPDATE frames SET locked_by=NULL, lock_expires=NULL "
              "WHERE status!='in_progress' AND locked_by IS NOT NULL AND lock_expires < ?", (now or time.time(),))


def frame_payload(c, fid):
    r = c.execute('SELECT * FROM frames WHERE frame_id=?', (fid,)).fetchone()
    if r is None:
        return None
    boxes = [dict(b) for b in c.execute('SELECT class_id, cx, cy, w, h, source, conf FROM boxes WHERE frame_id=?', (fid,))]
    return dict(r) | {'boxes': boxes}


def next_frame(c, user, skip=()):
    """The user's own open frame if they hold one, else the highest-priority todo frame, locked to them."""
    now = time.time()
    with tx(c):
        release_expired(c, now)
        c.execute("UPDATE frames SET locked_by=NULL, lock_expires=NULL WHERE locked_by=? AND status!='in_progress'", (user,))
        r = c.execute("SELECT frame_id FROM frames WHERE status='in_progress' AND locked_by=? "
                      "ORDER BY lock_expires DESC LIMIT 1", (user,)).fetchone()
        if r is None or r[0] in skip:
            if r is not None:   # user moved on from it without saving: hand it back
                c.execute("UPDATE frames SET status='todo', locked_by=NULL, lock_expires=NULL WHERE frame_id=?", (r[0],))
            r = c.execute("SELECT frame_id FROM frames WHERE status='todo' ORDER BY priority, rnd LIMIT 1").fetchone()
            if r is None:
                return None
            c.execute("UPDATE frames SET status='in_progress', locked_by=?, lock_expires=? WHERE frame_id=? AND status='todo'",
                      (user, now + LOCK_S, r[0]))
            c.execute('INSERT INTO events VALUES (?,?,?,?,?)', (r[0], user, 'lock', now, ''))
        else:
            c.execute('UPDATE frames SET lock_expires=? WHERE frame_id=?', (now + LOCK_S, r[0]))
    return frame_payload(c, r[0])


def open_frame(c, user, fid):
    """Reopen a frame the user worked on before (← key). Locks it if nobody else holds it."""
    now = time.time()
    with tx(c):
        release_expired(c, now)
        r = c.execute('SELECT * FROM frames WHERE frame_id=?', (fid,)).fetchone()
        if r is None:
            raise ValueError('unknown frame')
        if r['locked_by'] and r['locked_by'] != user:
            raise PermissionError(f'{r["locked_by"]} has this frame open right now')
        # hand back any other open frame of this user
        c.execute("UPDATE frames SET status='todo', locked_by=NULL, lock_expires=NULL "
                  "WHERE status='in_progress' AND locked_by=? AND frame_id!=?", (user, fid))
        st = 'in_progress' if r['status'] == 'todo' else r['status']
        c.execute('UPDATE frames SET status=?, locked_by=?, lock_expires=? WHERE frame_id=?', (st, user, now + LOCK_S, fid))
        c.execute('INSERT INTO events VALUES (?,?,?,?,?)', (fid, user, 'reopen', now, ''))
    return frame_payload(c, fid)


def heartbeat(c, user, fid):
    now = time.time()
    with tx(c):
        n = c.execute('UPDATE frames SET lock_expires=? WHERE frame_id=? AND locked_by=?', (now + LOCK_S, fid, user)).rowcount
    return n == 1


def save(c, user, fid, version, boxes, action):
    """action: labeled (boxes, may be empty = confirmed negative) or skipped. Optimistic version check."""
    if action not in ('labeled', 'skipped'):
        raise ValueError('bad action')
    clean = []
    for b in boxes if action == 'labeled' else []:
        k = int(b['class_id'])
        if k not in range(4):
            raise ValueError('every box needs a class (1-4)')
        x1, x2 = sorted((min(max(float(b['cx']) - float(b['w']) / 2, 0), 1), min(max(float(b['cx']) + float(b['w']) / 2, 0), 1)))
        y1, y2 = sorted((min(max(float(b['cy']) - float(b['h']) / 2, 0), 1), min(max(float(b['cy']) + float(b['h']) / 2, 0), 1)))
        if x2 - x1 < 0.002 or y2 - y1 < 0.004:
            continue
        clean.append((fid, k, (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1, 'human', None))
    now = time.time()
    with tx(c):
        r = c.execute('SELECT * FROM frames WHERE frame_id=?', (fid,)).fetchone()
        if r is None:
            raise ValueError('unknown frame')
        if r['split'] not in ('train', 'val') or r['route_group'] in TEST_GROUPS:
            raise PermissionError('test frames are frozen')
        if r['version'] != int(version):
            raise LookupError(f'{r["labeled_by"] or "someone"} saved this frame after you opened it; it was reloaded')
        if r['locked_by'] and r['locked_by'] != user:
            raise PermissionError(f'{r["locked_by"]} has this frame open now (your lock expired)')
        c.execute('DELETE FROM boxes WHERE frame_id=?', (fid,))
        c.executemany('INSERT INTO boxes VALUES (?,?,?,?,?,?,?,?)', clean)
        c.execute('UPDATE frames SET status=?, version=version+1, locked_by=NULL, lock_expires=NULL, labeled_by=?, '
                  'labeled_at=? WHERE frame_id=?', (action, user, now, fid))
        c.execute('INSERT INTO events VALUES (?,?,?,?,?)', (fid, user, action, now,
                                                            ' '.join(CODES[x[1]] for x in clean)))


def history(c, user, limit=50):
    return [r[0] for r in c.execute(
        "SELECT frame_id FROM events WHERE user=? AND action IN ('labeled','skipped') "
        "GROUP BY frame_id ORDER BY MAX(timestamp) DESC LIMIT ?", (user, limit))]


def status():
    c = connect()
    print('by status:', dict(Counter(r[0] for r in c.execute('SELECT status FROM frames'))))
    print('todo by priority:', dict(sorted(Counter(r[0] for r in c.execute(
        "SELECT priority FROM frames WHERE status='todo'")).items())))
    print('by split:', dict(Counter(r[0] for r in c.execute('SELECT split FROM frames'))))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    {'init': init, 'status': status}[cmd]()

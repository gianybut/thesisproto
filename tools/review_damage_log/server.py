r"""Review page for the damage log check (RQ2): the 50 sampled R07 records, then the 36 AI-flagged ones.

    python tools/review_damage_log/server.py          # opens http://127.0.0.1:8771 in the browser
    powershell -ExecutionPolicy Bypass -File tools\start_damage_review.ps1   # same, as a hidden process

This computer only (127.0.0.1). Map tiles and Leaflet come from the internet (OpenStreetMap, unpkg).

At start it runs `damage_log_check.prepare` (re-link the sample to the current records, write the
flagged checklist, compute the automatic checks; see tools/damage_log_check.py). Every answer is
saved at once into
    results/damage_log_check/survey3_checklist.csv          (sample: real, type, time, location, duplicate)
    results/damage_log_check/survey3_flagged_checklist.csv  (flagged: real only)
with the reviewer's name and the time, and appended to results/damage_log_check/review_events.csv.
Close the CSVs in Excel while reviewing: Excel locks them and the save fails (the page says so).

Score afterwards: python tools/damage_log_check.py score results/damage_log_check/survey3_checklist.csv
"""

import argparse
import csv
import json
import re
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import damage_log_check as dlc  # noqa: E402

ROOT = dlc.ROOT
VIDEO = 3
PORT = 8771
EVENTS = dlc.OUT / 'review_events.csv'
FIELDS = {'sample': dlc.ANSWERS, 'flagged': ['real_damage']}
VALUES = {'yes', 'no', 'unsure', ''}
lock = threading.Lock()
S = {}


def reviewers():
    p = ROOT / 'tools' / 'review_labels' / 'reviewers.txt'
    return [l.strip() for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]


def load():
    v, recs, gps, rows, frows, auto = dlc.prepare(VIDEO, quiet=True)
    S.update(video=v, recs={r['id']: r for r in recs}, gps=gps, rows={'sample': rows, 'flagged': frows}, auto=auto,
             snaps={r['frame_snapshot'] for r in recs if r['frame_snapshot']})


def data():
    v = S['video']
    recs = {str(i): {k: r[k] for k in ('id', 'frame_number', 'timestamp', 'confidence', 'bbox_x1', 'bbox_y1', 'bbox_x2',
                                        'bbox_y2', 'frame_snapshot', 'damage_type', 'latitude', 'longitude',
                                        'ai_check_score', 'classification_confidence')}
            for i, r in S['recs'].items()}
    return {'reviewers': reviewers(), 'rows': S['rows'], 'records': recs, 'auto': S['auto']['records'],
            'rules': S['auto']['rules'], 'route': [[g['latitude'], g['longitude']] for g in S['gps']],
            'video': {'id': v['id'], 'name': v['original_filename'], 'road': v['road_name'], 'fps': v['fps'],
                      'duration': v['duration'], 'offset': v['time_offset']},
            'names': dlc.NAMES}


def save(p):
    batch, item, reviewer = p.get('batch'), str(p.get('item')), (p.get('reviewer') or '').strip()
    if batch not in FIELDS:
        raise ValueError('unknown batch')
    if reviewer not in reviewers():
        raise ValueError(f'reviewer must be one of {reviewers()}')
    rows = S['rows'][batch]
    row = next((r for r in rows if str(r['item']) == item), None)
    if row is None:
        raise ValueError(f'no item {item}')
    changes = {}
    for k, val in (p.get('set') or {}).items():
        val = '' if val is None else str(val).strip()
        if k in FIELDS[batch]:
            if val not in VALUES:
                raise ValueError(f'{k}: {val!r} is not yes / no / unsure / blank')
        elif batch == 'sample' and k == 'duplicate_of':
            if val and not re.fullmatch(r'\d+', val):
                raise ValueError('duplicate_of must be a record id')
        elif k != 'notes':
            raise ValueError(f'unknown field {k}')
        changes[k] = val
    if batch == 'sample' and changes.get('real_damage') in ('no', 'unsure'):
        changes['type_correct'] = ''               # type is judged only for real damage
    if batch == 'sample' and changes.get('duplicate') in ('no', ''):
        changes['duplicate_of'] = ''
    if batch == 'sample' and changes.get('type_correct') and row.get('real_damage') != 'yes' and changes.get('real_damage') != 'yes':
        raise ValueError('answer "real damage" with yes before the type')
    old = {k: row.get(k, '') for k in changes}
    row.update(changes)
    row['reviewer'] = reviewer
    row['reviewed_at'] = datetime.now().isoformat(timespec='seconds')
    path = dlc.sample_path(VIDEO) if batch == 'sample' else dlc.flagged_path(VIDEO)
    try:
        dlc.write_rows(path, dlc.SAMPLE_COLS if batch == 'sample' else dlc.FLAGGED_COLS, rows)
    except PermissionError:
        row.update(old)
        raise ValueError(f'{path.name} is open in another program (Excel?). Close it and press the key again.')
    new = not EVENTS.exists()
    with open(EVENTS, 'a', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(['time', 'reviewer', 'batch', 'item', 'record_id', 'field', 'old', 'new'])
        for k, val in changes.items():
            w.writerow([row['reviewed_at'], reviewer, batch, item, row['record_id'], k, old[k], val])
    return row


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype='application/json'):
        b = body if isinstance(body, bytes) else (json.dumps(body) if ctype == 'application/json' else body).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(b)

    def file(self, path, ctype):
        size = path.stat().st_size
        rng = self.headers.get('Range')
        start, end = 0, size - 1
        m = re.match(r'bytes=(\d*)-(\d*)', rng or '')
        if m:
            if m.group(1):
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else size - 1
            else:
                start = size - int(m.group(2))
            end = min(end, size - 1)
        self.send_response(206 if m else 200)
        self.send_header('Content-Type', ctype)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        if m:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        try:
            with open(path, 'rb') as fh:
                fh.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = fh.read(min(1 << 20, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/':
            return self.send(200, (HERE / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if path == '/api/data':
            with lock:
                return self.send(200, data())
        if path.startswith('/snap/'):
            name = path[6:]
            if name in S['snaps']:
                return self.file(dlc.SNAPS / name, 'image/jpeg')
        if path == '/video/original':
            return self.file(dlc.UPLOADS / S['video']['filename'], 'video/mp4')
        if path == '/video/annotated' and S['video']['processed_filename']:
            return self.file(ROOT / 'backend' / 'processed' / S['video']['processed_filename'], 'video/mp4')
        self.send(404, {'error': 'not found'})

    def do_POST(self):
        if self.path != '/api/answer':
            return self.send(404, {'error': 'not found'})
        try:
            p = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
            with lock:
                row = save(p)
            self.send(200, {'ok': True, 'row': row})
        except ValueError as e:
            self.send(400, {'error': str(e)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=PORT)
    ap.add_argument('--no-browser', action='store_true')
    a = ap.parse_args()
    load()
    url = f'http://127.0.0.1:{a.port}'
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), H)
    print(f'Damage log review: {url}  ({len(S["rows"]["sample"])} sampled, {len(S["rows"]["flagged"])} flagged records). '
          'Ctrl+C stops it.', flush=True)
    if not a.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

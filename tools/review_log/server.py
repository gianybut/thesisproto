"""Review page for the damage log check (manuscript 5.3) and the AI-flagged records (5.1.6).

    python tools/damage_log_auto.py              # first: the automatic checks (uses the database)
    python tools/review_log/server.py            # then open http://127.0.0.1:8771

Run it on the computer whose backend database holds survey 3 (R07, 20261031T021049-3x76.mov), with
its snapshots and processed video. One record per screen:

  Batch 1, damage log (the 50 records of results/damage_log_check/survey3_checklist.csv):
    mark "damage type correct?" yes/no, and confirm or override the automatic time, location and
    duplicate results (tools/damage_log_auto.py). Nothing but the type is filled in for you: a time,
    location or duplicate answer is only written once you confirm or override it.
  Batch 2, AI-flagged records (every record of the survey with ai_check_score < 0.6, the app's
    VERIFY_THRESHOLD): mark "real road damage?" yes/no.

Every change is saved at once (autosave) to:
  results/damage_log_check/survey3_review_state.json   every answer, auto value, time of the answer
  results/damage_log_check/survey3_checklist.csv        the answer columns (type_correct, time_correct,
                                                         location_correct, duplicate, duplicate_of, notes)
  results/damage_log_check/survey3_flagged_review.csv   one row per flagged record

Then score:
  python tools/damage_log_check.py score results/damage_log_check/survey3_checklist.csv
  python tools/damage_log_check.py flagged results/damage_log_check/survey3_flagged_review.csv

The page reads only this computer's files; it listens on 127.0.0.1 only (the snapshots show people
and plates). The map tiles come from OpenStreetMap, so the browser needs internet for the map.
"""

import argparse
import json
import re
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from eval_common import (DB, NAMES, PROCESSED, R07_VIDEO, RESULTS, SNAPS, UPLOADS, connect, read_csv,  # noqa: E402
                         survey, survey_track, write_csv)

sys.path.insert(0, str(HERE.parents[1] / 'backend'))
try:
    from services.damage_verifier import VERIFY_THRESHOLD  # noqa: E402
except Exception:  # transformers etc. missing: the constant is all that is needed
    VERIFY_THRESHOLD = 0.6

ANSWER_COLS = ['type_correct', 'time_correct', 'location_correct', 'duplicate', 'duplicate_of', 'notes']
lock = threading.Lock()
CTX = {}


def load(a):
    con = connect(a.db)
    v = survey(con, a.video)
    if v is None:
        sys.exit(f'No survey {a.video} in {a.db}.')
    if v['original_filename'] != a.expect_video and not a.any_survey:
        sys.exit(f'Survey {a.video} is {v["original_filename"]}, not {a.expect_video}. Run this on the computer '
                 f'that holds the R07 survey (or pass --any-survey for a test run).')
    recs = {r['id']: dict(r) for r in con.execute('select * from detections where video_id = ? order by timestamp',
                                                   (a.video,))}
    checklist_path = Path(a.checklist)
    checklist = read_csv(checklist_path)
    for row in checklist:
        rid = int(row['record_id'])
        if rid not in recs or recs[rid]['frame_number'] != int(row['frame']):
            sys.exit(f'Checklist record {rid} does not match survey {a.video} (missing or a different frame): the '
                     f'survey was probably analysed again. Stop and decide with the team.')
    auto_path = Path(a.autocheck)
    if not auto_path.exists():
        sys.exit(f'{auto_path} is missing: run python tools/damage_log_auto.py --video {a.video} first.')
    auto = {int(r['record_id']): r for r in read_csv(auto_path)}
    if any(r.get('check_source') != 'database' for r in auto.values()) and not a.any_survey:
        print('WARNING: the automatic checks were not computed from the database (duplicates were looked for among '
              'the 50 sampled records only). Re-run tools/damage_log_auto.py here first.')

    def item(r, extra=None):
        return dict(id=r['id'], frame=r['frame_number'], time_s=r['timestamp'], code=r['damage_type'],
                    name=NAMES.get(r['damage_type'], r['damage_type']), confidence=r['confidence'],
                    ai=r['ai_check_score'], lat=r['latitude'], lon=r['longitude'],
                    box=[r['bbox_x1'], r['bbox_y1'], r['bbox_x2'], r['bbox_y2']],
                    snapshot=r['frame_snapshot'], **(extra or {}))

    log_items = []
    for row in checklist:
        r = recs[int(row['record_id'])]
        au = auto.get(r['id'], {})
        dup_ids = [int(x) for x in re.findall(r'(\d+) \(', au.get('duplicate_candidates', ''))]
        log_items.append(item(r, dict(
            item=int(row['item']), auto=dict(
                time=au.get('time_auto'), time_detail=f"stored {au.get('time_s')} s, frame/FPS {au.get('expected_time_s')} s, "
                                                      f"difference {au.get('time_diff_s')} s",
                location=au.get('location_auto'),
                location_detail=f"{au.get('sync_error_m')} m from the track at its time (tolerance {au.get('sync_tolerance_m')} m), "
                                f"{au.get('route_distance_m')} m from the route, vehicle {au.get('speed_mps')} m/s",
                duplicate=au.get('duplicate_auto'), duplicate_of=au.get('duplicate_of_auto', ''),
                duplicate_detail=au.get('duplicate_candidates') or 'none within 15 m and 5 s',
                source=au.get('check_source')),
            candidates=[item(recs[c]) for c in dup_ids if c in recs])))
    flagged = [item(r) for r in recs.values() if r['ai_check_score'] is not None and r['ai_check_score'] < VERIFY_THRESHOLD]

    out_dir = Path(a.out_dir)
    state_path = out_dir / f'survey{a.video}_review_state.json'
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'log': {}, 'flagged': {}}
    track = [[p[1], p[2]] for p in survey_track(con, a.video)]
    video_file = PROCESSED / v['processed_filename'] if v['processed_filename'] else None
    if not video_file or not video_file.exists() or video_file.suffix.lower() != '.mp4':
        video_file = UPLOADS / v['filename']
    CTX.update(survey=dict(id=v['id'], name=v['original_filename'], road=v['road_name'], fps=v['fps'],
                           video=video_file.name, annotated=video_file.parent == PROCESSED),
               log=log_items, flagged=flagged, track=track, state=state, state_path=state_path,
               checklist=checklist, checklist_path=checklist_path,
               flagged_path=out_dir / f'survey{a.video}_flagged_review.csv',
               video_file=video_file, snaps={i['snapshot'] for i in log_items + flagged if i['snapshot']}
               | {c['snapshot'] for i in log_items for c in i['candidates'] if c['snapshot']},
               threshold=VERIFY_THRESHOLD)
    print(f'Survey {v["id"]} ({v["original_filename"]}): {len(log_items)} checklist records, {len(flagged)} AI-flagged '
          f'records (score < {VERIFY_THRESHOLD}), video {video_file.name}.')


def yn(x):
    return {'yes': 'yes', 'no': 'no', 'unsure': 'unsure'}.get((x or '').lower(), '')


def write_outputs():
    """Answers -> checklist CSV columns and the flagged CSV. Called under the lock."""
    st = CTX['state']
    for row in CTX['checklist']:
        s = st['log'].get(row['record_id'], {})
        for f in ('type_correct', 'time_correct', 'location_correct', 'duplicate'):
            row[f] = yn(s.get(f, {}).get('value')) if isinstance(s.get(f), dict) else ''
        row['duplicate_of'] = s.get('duplicate_of', '') if row['duplicate'] == 'yes' else ''
        row['notes'] = s.get('notes', '')
    fields = list(CTX['checklist'][0].keys())
    write_csv(CTX['checklist_path'], CTX['checklist'], fields, bom=True)
    rows = []
    for i in CTX['flagged']:
        s = st['flagged'].get(str(i['id']), {})
        rows.append(dict(record_id=i['id'], type=f"{i['name']} ({i['code']})", code=i['code'],
                         confidence=f"{i['confidence']:.3f}", ai_check=f"{i['ai']:.3f}", time_s=f"{i['time_s']:.2f}",
                         real_damage=yn(s.get('real_damage', {}).get('value')), notes=s.get('notes', ''),
                         answered_at=s.get('real_damage', {}).get('at', '')))
    write_csv(CTX['flagged_path'], rows, bom=True)
    tmp = CTX['state_path'].with_suffix('.tmp')
    tmp.write_text(json.dumps(st, indent=1), encoding='utf-8')
    tmp.replace(CTX['state_path'])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, ctype='application/json'):
        data = body if isinstance(body, bytes) else (json.dumps(body) if ctype == 'application/json' else body).encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/':
            return self.send(200, (HERE / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if path == '/api/data':
            with lock:
                return self.send(200, {k: CTX[k] for k in ('survey', 'log', 'flagged', 'track', 'state', 'threshold')})
        if path.startswith('/snap/'):
            name = path[len('/snap/'):]
            if name not in CTX['snaps']:
                return self.send(404, {'error': 'not a snapshot of this review'})
            p = SNAPS / name
            return self.send(200, p.read_bytes(), 'image/jpeg') if p.exists() else self.send(404, {'error': 'missing'})
        if path == '/video':
            return self.stream(CTX['video_file'])
        return self.send(404, {'error': 'not found'})

    def stream(self, p):
        size = p.stat().st_size
        rng = self.headers.get('Range')
        start, end = 0, size - 1
        if rng and rng.startswith('bytes='):
            a, _, b = rng[6:].partition('-')
            start = int(a) if a else max(0, size - int(b))
            end = int(b) if a and b else size - 1
        end = min(end, size - 1)
        self.send_response(206 if rng else 200)
        self.send_header('Content-Type', 'video/mp4' if p.suffix.lower() == '.mp4' else 'video/quicktime')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        if rng:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        with open(p, 'rb') as f:
            f.seek(start)
            left = end - start + 1
            try:
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def do_POST(self):
        if urlparse(self.path).path != '/api/answer':
            return self.send(404, {'error': 'not found'})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)))
            batch, rid, field, value = body['batch'], str(body['id']), body['field'], body.get('value')
        except (ValueError, KeyError):
            return self.send(400, {'error': 'bad request'})
        allowed = {'log': {'type_correct', 'time_correct', 'location_correct', 'duplicate', 'duplicate_of', 'notes'},
                   'flagged': {'real_damage', 'notes'}}
        ids = {str(i['id']) for i in CTX[batch]} if batch in allowed else set()
        if batch not in allowed or field not in allowed[batch] or rid not in ids:
            return self.send(400, {'error': 'unknown batch, record or field'})
        now = datetime.now().astimezone().isoformat(timespec='seconds')
        with lock:
            rec = CTX['state'][batch].setdefault(rid, {})
            if field in ('notes', 'duplicate_of'):
                rec[field] = str(value or '')[:2000]
            elif value in (None, ''):
                rec.pop(field, None)
            else:
                if value not in ('yes', 'no', 'unsure'):
                    return self.send(400, {'error': 'value must be yes, no or unsure'})
                entry = {'value': value, 'at': now}
                if batch == 'log' and field != 'type_correct':
                    item = next(i for i in CTX['log'] if str(i['id']) == rid)
                    key = {'time_correct': 'time', 'location_correct': 'location', 'duplicate': 'duplicate'}[field]
                    entry['auto'] = item['auto'][key]
                    entry['how'] = 'confirmed' if value == item['auto'][key] else 'overridden'
                rec[field] = entry
            write_outputs()
            return self.send(200, {'ok': True, 'saved': now, 'record': rec})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', type=int, default=3)
    ap.add_argument('--db', default=str(DB))
    ap.add_argument('--checklist', default=None)
    ap.add_argument('--autocheck', default=None)
    ap.add_argument('--expect-video', default=R07_VIDEO)
    ap.add_argument('--any-survey', action='store_true', help='test run on another survey')
    ap.add_argument('--port', type=int, default=8771)
    ap.add_argument('--out-dir', default=str(RESULTS / 'damage_log_check'),
                    help='where the state JSON and flagged CSV go (the checklist is written in place)')
    a = ap.parse_args()
    a.checklist = a.checklist or str(RESULTS / 'damage_log_check' / f'survey{a.video}_checklist.csv')
    a.autocheck = a.autocheck or str(RESULTS / 'damage_log_check' / f'survey{a.video}_autocheck.csv')
    load(a)
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    print(f'Review page: http://127.0.0.1:{a.port}  (Ctrl+C to stop; every answer is already saved)')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

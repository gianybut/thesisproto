"""Review tool for the val/test frames (Steps 2.4, 2.5). One page, served from this computer.

    python tools/review_labels/server.py            # this computer only: http://127.0.0.1:8770
    python tools/review_labels/server.py --lan      # also other laptops on the same Wi-Fi

Frames: data/local/review_frames.csv (batch 1: select_review.py; batch 2: select_review_more.py).
Reviewer names: tools/review_labels/reviewers.txt (one per line). Every save must name one of them.

One reviewer (team decision 2026-11-10: Gian Paolo Ybut reviews everything).
- Review: accepting a frame (Enter) marks it reviewed and keeps its boxes as first_boxes; an edit
  after that un-accepts it until Enter again.
- Self-check: test frames of batches 1 and 2 that were accepted as "no damage" are looked at again
  (mode "self_check"). The frame stays reviewed; self_check_done / self_check_changed record the
  check and whether the boxes now differ from first_boxes (any box added, removed, re-classed, or
  moved below IoU 0.5). It affects only the final test evaluation, not training.
The current boxes are always the labels (data/local/reviewed/labels/).

Saved at every change:
  data/local/reviewed/state/<frame>.json   boxes, reviewer, times, first_boxes, self-check
  data/local/reviewed/labels/<frame>.txt   YOLO labels (0 D00, 1 D10, 2 D20, 3 D40)
  data/local/review_log.csv                one row per frame (reviewed = first review accepted)
  data/local/review_events.csv             every save, appended
--lan serves the survey frames to the local network: use it only on a trusted network.
"""

import argparse
import csv
import json
import socket
import struct
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'local'
REV = DATA / 'reviewed'
STATE, LABELS = REV / 'state', REV / 'labels'
HERE = Path(__file__).resolve().parent
CODES = ['D00', 'D10', 'D20', 'D40']
NAMES = {'D00': 'Longitudinal crack', 'D10': 'Transverse crack', 'D20': 'Alligator crack', 'D40': 'Pothole'}
RUBRIC = ('Draw any damage the drafts missed, especially cracks. Patches/repairs are not damage unless '
          'they contain an actual pothole or crack.')
GUIDELINE = ('One tight box per continuous crack (D00 along the road, D10 across it). D20: one box around the '
             'whole cracked area. D40: the box follows the edge of the hole. Patches are not damage.')

lock = threading.Lock()


def read_csv(p):
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def reviewers():
    return [l.strip() for l in (HERE / 'reviewers.txt').read_text(encoding='utf-8').splitlines() if l.strip()]


def frames():
    rows = read_csv(DATA / 'review_frames.csv')
    for r in rows:
        r.setdefault('batch', '1')
        r['batch'] = r['batch'] or '1'
    return rows


def by_name():
    return {f['frame']: f for f in frames()}


def drafts():
    """Draft boxes per frame: the stand-in's kept boxes (batches 1 and 2), replaced by the boxes in
    review_drafts.csv (the teacher's, batches "train" and "AL") for the frames listed there."""
    out = {}
    for i, r in enumerate(read_csv(DATA / 'autolabel_log.csv')):
        if r['kept'] == '1':
            out.setdefault(r['frame'], []).append(dict(
                id=f'd{i}', cls=r['code'], x1=float(r['x1']), y1=float(r['y1']), x2=float(r['x2']), y2=float(r['y2']),
                origin='draft', draft_cls=r['code']))
    p = DATA / 'review_drafts.csv'
    if p.exists():
        rows = read_csv(p)
        for f in {r['frame'] for r in rows}:
            out[f] = []
        for i, r in enumerate(rows):
            out[r['frame']].append(dict(id=f't{i}', cls=r['cls'], x1=float(r['x1']), y1=float(r['y1']),
                                        x2=float(r['x2']), y2=float(r['y2']), origin='draft', draft_cls=r['cls']))
    return out


def image_size(name):
    with open(DATA / 'frames' / name, 'rb') as f:   # JPEG SOF marker scan, no image library needed
        f.read(2)
        while True:
            marker, size = struct.unpack('>2sH', f.read(4))
            if marker[1] in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack('>xHH', f.read(5))
                return w, h
            f.seek(size - 2, 1)


def state_path(name):
    return STATE / f'{name[:-4]}.json'


def load_state(name):
    p = state_path(name)
    if p.exists():
        s = json.loads(p.read_text(encoding='utf-8'))
        if s.get('reviewed') and 'first_boxes' not in s:   # saved before first_boxes existed
            s.update(first_reviewer=s.get('reviewer', ''), first_time=s.get('updated', ''),
                     first_boxes=s['boxes'], first_background=s.get('background', False))
        for k in ('second_reviewer', 'second_time', 'second_done', 'second_changed'):   # retired fields
            s.pop(k, None)
        return s
    w, h = image_size(name)
    return dict(frame=name, width=w, height=h, boxes=DRAFTS.get(name, []), background=False, reviewed=False,
                reviewer='', updated='', first_reviewer='', first_time='', first_boxes=[], first_background=False,
                self_check_done=False, self_check_changed=None, self_check_time='')


def iou(a, b):
    ix = max(0, min(a['x2'], b['x2']) - max(a['x1'], b['x1']))
    iy = max(0, min(a['y2'], b['y2']) - max(a['y1'], b['y1']))
    inter = ix * iy
    u = (a['x2'] - a['x1']) * (a['y2'] - a['y1']) + (b['x2'] - b['x1']) * (b['y2'] - b['y1']) - inter
    return inter / u if u > 0 else 0.0


def boxes_differ(a, b):
    """True if the two box lists are not the same damage: same classes matched one-to-one at IoU >= 0.5."""
    if len(a) != len(b):
        return True
    used = set()
    for x in a:
        j = next((j for j, y in enumerate(b) if j not in used and y['cls'] == x['cls'] and iou(x, y) >= 0.5), None)
        if j is None:
            return True
        used.add(j)
    return False


def self_check_eligible(f, s):
    """Test frames of batches 1 and 2 accepted as "no damage"."""
    return (f['split'] == 'test' and f['batch'] in ('1', '2') and bool(s) and bool(s.get('reviewed'))
            and not s.get('first_boxes'))


def write_log():
    rows = []
    for f in frames():
        p = state_path(f['frame'])
        s = load_state(f['frame']) if p.exists() else None
        rows.append(dict(
            frame=f['frame'], split=f['split'], batch=f['batch'], route_group=f['route_group'],
            reviewer=s.get('first_reviewer', '') if s else '',
            reviewed='yes' if s and s.get('reviewed') else 'no', first_time=s.get('first_time', '') if s else '',
            first_no_damage=int(bool(s and s.get('reviewed') and not s.get('first_boxes'))) if s else '',
            self_check_eligible=int(self_check_eligible(f, s)),
            self_check_done='yes' if s and s.get('self_check_done') else 'no',
            self_check_changed='' if not (s and s.get('self_check_done')) else ('yes' if s.get('self_check_changed') else 'no'),
            self_check_time=s.get('self_check_time', '') if s else '',
            boxes=len(s['boxes']) if s else '', no_damage=int(bool(s and s.get('reviewed') and not s['boxes'])) if s else ''))
    tmp = DATA / 'review_log.csv.tmp'
    with open(tmp, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    tmp.replace(DATA / 'review_log.csv')


def save(payload):
    name = payload['frame']
    if name not in by_name():
        raise ValueError('unknown frame')
    who = str(payload.get('reviewer', '')).strip()
    if who not in reviewers():
        raise ValueError('choose your name at the top first')
    accept = bool(payload.get('accept', payload.get('reviewed')))
    mode = payload.get('mode', 'review')
    s = load_state(name)
    if mode == 'self_check' and not self_check_eligible(by_name()[name], s):
        raise ValueError('only test frames of batches 1-2 accepted as "no damage" are self-checked')
    w, h = s['width'], s['height']
    boxes = []
    for b in payload['boxes']:
        if b.get('cls') not in CODES:
            raise ValueError('every box needs a class (1-4) before saving')
        x1, x2 = sorted((min(max(float(b['x1']), 0), w), min(max(float(b['x2']), 0), w)))
        y1, y2 = sorted((min(max(float(b['y1']), 0), h), min(max(float(b['y2']), 0), h)))
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue
        boxes.append(dict(id=str(b.get('id', '')), cls=b['cls'], x1=round(x1, 1), y1=round(y1, 1), x2=round(x2, 1),
                          y2=round(y2, 1), origin=b.get('origin', 'new'), draft_cls=b.get('draft_cls', '')))
    now = datetime.now().isoformat(timespec='seconds')
    s.update(boxes=boxes, background=bool(payload.get('background')) and not boxes, reviewer=who, updated=now)
    if mode == 'self_check':
        # The frame stays reviewed; the check is recorded against the boxes first accepted.
        s['self_check_done'] = accept
        s['self_check_changed'] = boxes_differ(s.get('first_boxes', []), boxes)
        if accept:
            s['self_check_time'] = now
        p = 'self_check'
    else:
        s['reviewed'] = accept
        if accept:
            s.update(first_reviewer=who, first_time=now, first_boxes=boxes, first_background=s['background'])
        p = 'review'
    with lock:
        STATE.mkdir(parents=True, exist_ok=True)
        LABELS.mkdir(parents=True, exist_ok=True)
        state_path(name).write_text(json.dumps(s, indent=1), encoding='utf-8')
        (LABELS / f'{name[:-4]}.txt').write_text(''.join(
            f'{CODES.index(b["cls"])} {(b["x1"] + b["x2"]) / 2 / w:.6f} {(b["y1"] + b["y2"]) / 2 / h:.6f} '
            f'{(b["x2"] - b["x1"]) / w:.6f} {(b["y2"] - b["y1"]) / h:.6f}\n' for b in boxes))
        new_file = not (DATA / 'review_events.csv').exists()
        with open(DATA / 'review_events.csv', 'a', newline='', encoding='utf-8') as fh:
            ev = csv.writer(fh)
            if new_file:
                ev.writerow(['time', 'frame', 'reviewer', 'reviewed', 'boxes', 'background', 'classes', 'pass', 'accepted'])
            ev.writerow([now, name, who, 'yes' if s['reviewed'] else 'no', len(boxes), int(s['background']),
                         ' '.join(b['cls'] for b in boxes), p, int(accept)])
        write_log()
    return s


def listing():
    out = []
    for f in frames():
        p = state_path(f['frame'])
        s = load_state(f['frame']) if p.exists() else None
        out.append(dict(frame=f['frame'], split=f['split'], batch=f['batch'], route_group=f['route_group'],
                        reviewed=bool(s and s.get('reviewed')), started=bool(s),
                        first_no_damage=bool(s and s.get('reviewed') and not s.get('first_boxes')),
                        self_check=self_check_eligible(f, s),
                        self_check_done=bool(s and s.get('self_check_done')),
                        self_check_changed=(s or {}).get('self_check_changed')))
    return dict(frames=out, codes=CODES, names=NAMES, rubric=RUBRIC, guideline=GUIDELINE, reviewers=reviewers(),
                examples=(DATA / 'box_examples.jpg').exists())


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, ctype='application/json'):
        data = body if isinstance(body, bytes) else json.dumps(body).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        known = by_name()
        if u.path in ('/', '/index.html'):
            return self.send(200, (HERE / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if u.path == '/examples.jpg' and (DATA / 'box_examples.jpg').exists():
            return self.send(200, (DATA / 'box_examples.jpg').read_bytes(), 'image/jpeg')
        if u.path == '/api/frames':
            return self.send(200, listing())
        if u.path == '/api/frame':
            name = q.get('name', [''])[0]
            if name not in known:
                return self.send(404, {'error': 'unknown frame'})
            return self.send(200, load_state(name) | {'meta': known[name]})
        if u.path.startswith('/img/'):
            name = u.path[5:]
            if name not in known:   # only the selected frames, never an arbitrary path
                return self.send(404, {'error': 'unknown frame'})
            return self.send(200, (DATA / 'frames' / name).read_bytes(), 'image/jpeg')
        return self.send(404, {'error': 'not found'})

    def do_POST(self):
        if urlparse(self.path).path != '/api/save':
            return self.send(404, {'error': 'not found'})
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
            return self.send(200, save(payload))
        except (ValueError, KeyError, TypeError) as e:
            return self.send(400, {'error': str(e)})


DRAFTS = drafts()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8770)
    ap.add_argument('--lan', action='store_true', help='listen on the local network too (trusted Wi-Fi only)')
    a = ap.parse_args()
    host = '0.0.0.0' if a.lan else '127.0.0.1'
    srv = ThreadingHTTPServer((host, a.port), Handler)
    print(f'Review tool: http://127.0.0.1:{a.port}  ({len(frames())} frames)', flush=True)
    if a.lan:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('10.255.255.255', 1))
            print(f'Other laptops on this Wi-Fi: http://{s.getsockname()[0]}:{a.port}', flush=True)
        except OSError:
            pass
    print('Stop with Ctrl+C. Everything is saved as you go.', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    sys.exit(main())

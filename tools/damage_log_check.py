"""Damage log correctness (RQ2): a random sample of one survey's damage records, checked by hand.

    python tools/damage_log_check.py export --video 3 --n 50     # writes the checklist (seed 42)
    python tools/damage_log_check.py prepare --video 3           # re-link, flagged list, automatic checks
    python tools/damage_log_check.py score results/damage_log_check/survey3_checklist.csv

The answers are entered with the review page (tools/review_damage_log/server.py), which saves them
into the two checklists below at every key press. They can also be typed into the CSVs by hand.

export draws N records of the survey at random (fixed seed), lists them in video order, and writes
results/damage_log_check/survey<id>_checklist.csv (UTF-8 with BOM, opens in Excel).

prepare (run once by the review page at start; safe to repeat):
  1. Re-links the sample to the survey's current records. Survey 3 was analysed again on
     2026-11-12 (fusion + second-stage classifier), after the checklist was drawn on 2026-11-11, so
     the records got new ids. The same 50 detections are found by their snapshot file (same frame,
     box and confidence); record_id, type, confidence and ai_check are updated to the current
     (deployed) record, and the old values are kept in record_id_before_reanalysis /
     type_before_reanalysis. Refused once any answer has been entered.
  2. Writes survey<id>_flagged_checklist.csv: every record of the survey whose AI check score is
     below 0.6 (flagged "likely not road damage"), in video order, to be judged real or not.
  3. Computes the automatic checks into auto_checks.json and the auto_* columns (suggestions only;
     the scorer reads only the answers):
       time      the record's time equals frame / fps, and its snapshot is the video frame at that
                 time (read from the original video in one sequential pass; frame numbers count
                 from 1, so the snapshot is 0-based frame index frame - 1 and the stored time
                 is 1/fps = 0.033 s late)
       location  the stored point equals the GPS position interpolated at that time (Formula 19,
                 with the survey's time offset), and lies on the recorded route
       duplicate another record of the survey (any type) lies within 15 m and 5 s of it and comes
                 earlier in the video (the later record of a pair is the duplicate)

Answer columns of the sample (yes / y / 1, no / n / 0; blank or "unsure" = left out of that rate):

    real_damage       yes = the box shows road damage of any of the four kinds; no = it does not
    type_correct      yes = the kind named is right. Only for real damage (blank when real_damage = no)
    time_correct      yes = the video at that time shows this damage
    location_correct  yes = the coordinates are where this damage is on the road (phone GPS: a few
                      metres off is still yes)
    duplicate         yes = the same physical damage is already an earlier record of this survey
                      (its id in duplicate_of); no = recorded once

Flagged list: real_damage only.

score prints, with counts and 95% Wilson intervals: record precision (real damage among the
answered records), type correctness among the real records, time and location correctness,
the duplicate rate, the share fully correct, per recorded type; and, for the flagged list, the
share that is real damage, overall and per class. It writes <checklist>_score.md beside the file.
"""

import argparse
import csv
import json
import math
import os
import random
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'backend' / 'pothole_detection.db'
SNAPS = ROOT / 'backend' / 'snapshots'
UPLOADS = ROOT / 'backend' / 'uploads'
OUT = ROOT / 'results' / 'damage_log_check'
WEB = 'http://localhost:5173'
SEED = 42
VERIFY_THRESHOLD = 0.6          # backend/services/damage_verifier.py
DUP_M, DUP_S = 15.0, 5.0        # duplicate suggestion: within 15 m and 5 s
ROUTE_OK_M = 5.0                # location suggestion: on the route within 5 m
NAMES = {'D00': 'Longitudinal crack', 'D10': 'Transverse crack', 'D20': 'Alligator crack', 'D40': 'Pothole'}
CHECKS = ['type_correct', 'time_correct', 'location_correct', 'duplicate']
ANSWERS = ['real_damage'] + CHECKS
SAMPLE_COLS = (['item', 'record_id', 'type', 'confidence', 'ai_check', 'video_time', 'time_s', 'frame',
                'latitude', 'longitude', 'position_source', 'snapshot_path', 'survey_link', 'map_link']
               + ANSWERS + ['duplicate_of', 'notes', 'reviewer', 'reviewed_at',
                            'auto_time', 'auto_location', 'auto_duplicate',
                            'record_id_before_reanalysis', 'type_before_reanalysis'])
FLAGGED_COLS = ['item', 'record_id', 'type', 'confidence', 'ai_check', 'video_time', 'time_s', 'frame',
                'latitude', 'longitude', 'snapshot_path', 'in_sample_item', 'real_damage', 'notes',
                'reviewer', 'reviewed_at']
YES, NO = {'yes', 'y', '1', 'true'}, {'no', 'n', '0', 'false'}


def mmss(t):
    return f'{int(t // 60):02d}:{t % 60:04.1f}'


def type_name(code):
    return f'{NAMES.get(code, code)} ({code})'


def sample_path(video):
    return OUT / f'survey{video}_checklist.csv'


def flagged_path(video):
    return OUT / f'survey{video}_flagged_checklist.csv'


def read_rows(path):
    with open(path, newline='', encoding='utf-8-sig') as fh:
        r = csv.DictReader(fh)
        return list(r), r.fieldnames


def write_rows(path, cols, rows):
    """Whole-file rewrite through a temporary file, so a crash never leaves half a checklist."""
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in cols})
    os.replace(tmp, path)


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def survey(con, video):
    v = con.execute('select * from videos where id = ?', (video,)).fetchone()
    if not v:
        sys.exit(f'No survey {video}.')
    recs = [dict(r) for r in con.execute('select * from detections where video_id = ? order by timestamp, id', (video,))]
    gps = [dict(r) for r in con.execute('select timestamp, latitude, longitude from gps_track_points '
                                        'where video_id = ? order by timestamp', (video,))]
    return dict(v), recs, gps


def export(a):
    con = db()
    v, rows, _ = survey(con, a.video)
    rows.sort(key=lambda r: r['id'])
    if len(rows) < a.n:
        sys.exit(f'Survey {a.video} has {len(rows)} records, fewer than {a.n}.')
    pick = sorted(random.Random(SEED).sample(rows, a.n), key=lambda r: (r['timestamp'], r['id']))
    OUT.mkdir(parents=True, exist_ok=True)
    out = sample_path(a.video)
    if out.exists() and not a.force:
        sys.exit(f'{out} exists (it may hold answers already); use --force to overwrite it.')
    write_rows(out, SAMPLE_COLS, [dict(sample_fields(r, a.video), item=i) for i, r in enumerate(pick, 1)])
    print(f'{a.n} of {len(rows)} records of survey {a.video} ({v["original_filename"]}), seed {SEED} -> {out}')


def sample_fields(r, video):
    lat, lon = r['latitude'], r['longitude']
    return {'record_id': r['id'], 'type': type_name(r['damage_type']), 'confidence': f"{r['confidence']:.2f}",
            'ai_check': '' if r['ai_check_score'] is None else f"{r['ai_check_score']:.2f}",
            'video_time': mmss(r['timestamp']), 'time_s': f"{r['timestamp']:.1f}", 'frame': r['frame_number'],
            'latitude': '' if lat is None else f'{lat:.7f}', 'longitude': '' if lon is None else f'{lon:.7f}',
            'position_source': r['position_source'],
            'snapshot_path': str(SNAPS / r['frame_snapshot']) if r['frame_snapshot'] else '',
            'survey_link': f"{WEB}/videos/{video}?t={r['timestamp']:.1f}",
            'map_link': '' if lat is None else
            f'https://www.openstreetmap.org/?mlat={lat:.7f}&mlon={lon:.7f}#map=19/{lat:.6f}/{lon:.6f}'}


# ---------- prepare ----------

def haversine(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def interpolate(gps, t, offset):
    """Same as backend/services/gps_service.interpolate_gps (clamped at both ends)."""
    g = t + offset
    if g <= gps[0]['timestamp']:
        return gps[0]['latitude'], gps[0]['longitude']
    if g >= gps[-1]['timestamp']:
        return gps[-1]['latitude'], gps[-1]['longitude']
    for p, q in zip(gps, gps[1:]):
        if p['timestamp'] <= g <= q['timestamp']:
            k = 0.0 if q['timestamp'] == p['timestamp'] else (g - p['timestamp']) / (q['timestamp'] - p['timestamp'])
            return (round(p['latitude'] + k * (q['latitude'] - p['latitude']), 7),
                    round(p['longitude'] + k * (q['longitude'] - p['longitude']), 7))


def route_distance(pt, gps):
    """Shortest distance (m) from a point to the GPS polyline, on a local flat projection."""
    lat0 = math.radians(pt[0])
    xy = lambda la, lo: (math.radians(lo) * 6371000 * math.cos(lat0), math.radians(la) * 6371000)
    px, py = xy(*pt)
    best = float('inf')
    pts = [xy(g['latitude'], g['longitude']) for g in gps]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        k = 0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
        best = min(best, math.hypot(px - ax - k * dx, py - ay - k * dy))
    return best


def snapshot_match(v, recs):
    """One sequential pass over the original video. For each record, the mean absolute grey-level
    difference (0-255, 240x135) between its snapshot and video frame indexes frame-2 .. frame+2
    (0-based, as OpenCV reads them)."""
    import cv2
    import numpy as np
    small = lambda im: cv2.resize(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), (240, 135), interpolation=cv2.INTER_AREA).astype(np.float32)
    want = {}
    for r in recs:
        snap = cv2.imread(str(SNAPS / r['frame_snapshot'])) if r['frame_snapshot'] else None
        if snap is None:
            continue
        s = small(snap)
        for d in range(-2, 3):
            want.setdefault(r['frame_number'] + d, []).append((r['id'], d, s))
    out = {}
    cap = cv2.VideoCapture(str(UPLOADS / v['filename']))
    last = max(want) if want else -1
    i = 0
    while i <= last:
        if not cap.grab():
            break
        if i in want:
            ok, im = cap.retrieve()
            if ok:
                f = small(im)
                for rid, d, s in want[i]:
                    out.setdefault(rid, {})[d] = round(float(np.abs(f - s).mean()), 2)
        i += 1
    cap.release()
    return out


def auto_checks(v, recs, gps, ids):
    print(f'Automatic checks for {len(ids)} records (reads the original video once, about 2 minutes) ...')
    by_id = {r['id']: r for r in recs}
    match = snapshot_match(v, [by_id[i] for i in ids])
    res = {}
    for i in ids:
        r = by_id[i]
        expect = r['frame_number'] / v['fps']
        m = match.get(i, {})
        best = min(m, key=m.get) if m else None
        # frame_number counts from 1 (video_processor increments after each read), so the snapshot is
        # video frame index frame_number - 1 (offset -1): the stored time is 1/fps (0.033 s) late.
        time_ok = abs(r['timestamp'] - expect) < 0.5 / v['fps'] and best == -1 and m.get(-1, 99) < 3
        pt = (r['latitude'], r['longitude']) if r['latitude'] is not None else None
        if pt and gps:
            ip = interpolate(gps, r['timestamp'], v['time_offset'] or 0.0)
            shift = haversine(pt, ip)
            route = route_distance(pt, gps)
        else:
            shift = route = None
        loc_ok = shift is not None and shift < 1.0 and route < ROUTE_OK_M
        cands = []
        for o in recs:
            if o['id'] == i or o['latitude'] is None or not pt:
                continue
            dt = o['timestamp'] - r['timestamp']
            if abs(dt) <= DUP_S:
                dm = haversine(pt, (o['latitude'], o['longitude']))
                if dm <= DUP_M:
                    cands.append({'id': o['id'], 'type': o['damage_type'], 'dt': round(dt, 1), 'dm': round(dm, 1),
                                  'snapshot': o['frame_snapshot'], 'earlier': dt < 0 or (dt == 0 and o['id'] < i)})
        cands.sort(key=lambda c: abs(c['dt']))
        earlier = [c for c in cands if c['earlier']]
        res[str(i)] = {
            'time': {'suggest': 'yes' if time_ok else 'no', 'timestamp': round(r['timestamp'], 3),
                     'frame_over_fps': round(expect, 3), 'snapshot_diff': m, 'best_offset': best},
            'location': {'suggest': 'yes' if loc_ok else 'no',
                         'gps_shift_m': None if shift is None else round(shift, 2),
                         'route_m': None if route is None else round(route, 2)},
            'duplicate': {'suggest': 'yes' if earlier else 'no', 'candidates': cands,
                          'duplicate_of': earlier[0]['id'] if earlier else ''},
        }
    return res


def prepare(video, quiet=False):
    """Idempotent. Returns (sample rows, flagged rows, auto checks)."""
    con = db()
    v, recs, gps = survey(con, video)
    by_snap = {r['frame_snapshot']: r for r in recs}
    by_id = {r['id']: r for r in recs}
    sp = sample_path(video)
    rows, cols = read_rows(sp)
    changed = False
    if 'record_id_before_reanalysis' not in cols or 'real_damage' not in cols:
        if any((r.get(c) or '').strip() for r in rows for c in ANSWERS if c in r):
            sys.exit(f'{sp} already holds answers; not re-linking it.')
        for r in rows:
            d = by_snap.get(Path(r['snapshot_path']).name)
            if d is None:
                sys.exit(f'Item {r["item"]}: snapshot {r["snapshot_path"]} is not a record of survey {video} any more.')
            old_id, old_type = r['record_id'], r['type']
            r.update(sample_fields(d, video))
            r['record_id_before_reanalysis'], r['type_before_reanalysis'] = old_id, old_type
        changed = True
        n = sum(r['type'] != r['type_before_reanalysis'] for r in rows)
        print(f'Re-linked {len(rows)} sampled records to the current records of survey {video} ({n} now have another type).')
    for r in rows:
        if int(r['record_id']) not in by_id:
            sys.exit(f'Item {r["item"]}: record {r["record_id"]} is not in survey {video}. Was the survey analysed again?')

    fp = flagged_path(video)
    sample_items = {int(r['record_id']): r['item'] for r in rows}
    if fp.exists():
        frows, _ = read_rows(fp)
    else:
        flagged = [r for r in recs if r['ai_check_score'] is not None and r['ai_check_score'] < VERIFY_THRESHOLD]
        frows = []
        for i, d in enumerate(flagged, 1):
            f = sample_fields(d, video)
            frows.append({**{k: f[k] for k in FLAGGED_COLS if k in f}, 'item': i,
                          'in_sample_item': sample_items.get(d['id'], '')})
        write_rows(fp, FLAGGED_COLS, frows)
        print(f'{len(frows)} flagged records (AI check < {VERIFY_THRESHOLD}) -> {fp}')

    ap = OUT / f'survey{video}_auto_checks.json'
    ids = sorted({int(r['record_id']) for r in rows} | {int(r['record_id']) for r in frows})
    auto = json.loads(ap.read_text(encoding='utf-8')) if ap.exists() else {}
    if auto.get('processed_date') != v['processed_date'] or set(auto.get('records', {})) != {str(i) for i in ids}:
        auto = {'video': video, 'processed_date': v['processed_date'], 'computed_at': datetime.now().isoformat(timespec='seconds'),
                'rules': {'time': 'timestamp = frame / fps (within half a frame) and the snapshot is the video frame at that '
                                  'time: smallest grey-level difference (below 3 of 255) at video frame index frame - 1, '
                                  'because frame numbers count from 1 (the stored time is 1/fps = 0.033 s late)',
                          'location': f'stored point within 1 m of the GPS position interpolated at that time, and within '
                                      f'{ROUTE_OK_M:g} m of the route',
                          'duplicate': f'an earlier record of the survey (any type) within {DUP_M:g} m and {DUP_S:g} s'},
                'records': auto_checks(v, recs, gps, ids)}
        ap.write_text(json.dumps(auto, indent=1), encoding='utf-8')
        print(f'Automatic checks -> {ap}')
    for r in rows:
        a = auto['records'][str(r['record_id'])]
        new = (a['time']['suggest'], a['location']['suggest'], a['duplicate']['suggest'])
        if (r.get('auto_time'), r.get('auto_location'), r.get('auto_duplicate')) != new:
            r['auto_time'], r['auto_location'], r['auto_duplicate'] = new
            changed = True
    if changed:
        write_rows(sp, SAMPLE_COLS, rows)
    if not quiet:
        s = auto['records']
        print(f"Suggestions on the sample: time yes {sum(s[str(r['record_id'])]['time']['suggest'] == 'yes' for r in rows)}/{len(rows)}, "
              f"location yes {sum(s[str(r['record_id'])]['location']['suggest'] == 'yes' for r in rows)}/{len(rows)}, "
              f"possible duplicate {sum(s[str(r['record_id'])]['duplicate']['suggest'] == 'yes' for r in rows)}/{len(rows)}")
    return v, recs, gps, rows, frows, auto


# ---------- score ----------

def wilson(k, n, z=1.96):
    if not n:
        return (float('nan'), float('nan'))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def answer(x):
    x = (x or '').strip().lower()
    return True if x in YES else False if x in NO else None


def rate_row(label, vals, total):
    y, n = vals.count(True), vals.count(False)
    lo, hi = wilson(y, y + n)
    return (f'| {label} | {y} | {n} | {total - y - n} | ' + (f'{100 * y / (y + n):.1f}%' if y + n else 'n/a') + ' | '
            + (f'{100 * lo:.1f}% to {100 * hi:.1f}%' if y + n else 'n/a') + ' |'), (y, n, lo, hi)


def score(a):
    path = Path(a.checklist)
    rows, cols = read_rows(path)
    missing = [c for c in ANSWERS if c not in (cols or [])]
    if missing:
        sys.exit(f'Columns missing: {missing} (run "prepare" first)')
    real = [answer(r['real_damage']) for r in rows]
    real_rows = [r for r, t in zip(rows, real) if t]
    md = [f'# Damage log correctness: {path.name}', '', f'{len(rows)} sampled records. '
          'Rates are yes / answered; blank or "unsure" answers are left out of that rate. 95% Wilson intervals.', '',
          '| Measure | Yes | No | Not answered | Rate | 95% CI |', '|---|---|---|---|---|---|']
    res = {}
    for label, key, vals, total in [
            ('Record precision (box shows real road damage)', 'record_precision', real, len(rows)),
            ('Type correct, among real-damage records', 'type_correct', [answer(r['type_correct']) for r in real_rows], len(real_rows)),
            ('Time correct', 'time_correct', [answer(r['time_correct']) for r in rows], len(rows)),
            ('Location correct', 'location_correct', [answer(r['location_correct']) for r in rows], len(rows)),
            ('Duplicate (rate = duplicate rate)', 'duplicate', [answer(r['duplicate']) for r in rows], len(rows))]:
        line, res[key] = rate_row(label, vals, total)
        md.append(line)
    full = [r for r in rows if answer(r['real_damage']) is not None and all(answer(r[c]) is not None for c in CHECKS[1:])
            and (answer(r['real_damage']) is False or answer(r['type_correct']) is not None)]
    ok = sum(1 for r in full if answer(r['real_damage']) and answer(r['type_correct']) and answer(r['time_correct'])
             and answer(r['location_correct']) and not answer(r['duplicate']))
    lo, hi = wilson(ok, len(full))
    md += ['', f'Fully correct (real damage, right type, right time and location, not a duplicate): {ok} of {len(full)} '
           'fully answered records' + (f' = {100 * ok / len(full):.1f}% (95% CI {100 * lo:.1f}% to {100 * hi:.1f}%).' if full else '.')]
    md += ['', 'Per recorded type:', '', '| Recorded type | Records | Real damage | Not damage | Type correct (of real) |', '|---|---|---|---|---|']
    for k in sorted({r['type'] for r in rows}):
        g = [r for r in rows if r['type'] == k]
        y = sum(answer(r['real_damage']) is True for r in g)
        n = sum(answer(r['real_damage']) is False for r in g)
        t = [answer(r['type_correct']) for r in g if answer(r['real_damage'])]
        md.append(f'| {k} | {len(g)} | {y} | {n} | {t.count(True)} of {t.count(True) + t.count(False)} |')
    wrong = [r for r in real_rows if answer(r['type_correct']) is False]
    if wrong:
        md += ['', 'Real damage named with the wrong type: ' + '; '.join(
            f"item {r['item']} (record {r['record_id']}, recorded {r['type']}{', ' + r['notes'] if r['notes'] else ''})" for r in wrong)]
    fp = Path(a.flagged) if a.flagged else path.with_name(path.stem.replace('_checklist', '') + '_flagged_checklist.csv')
    if fp.exists():
        md += ['', f'## Flagged records ({fp.name})', '']
        frows, _ = read_rows(fp)
        f = [answer(r['real_damage']) for r in frows]
        md += [f'{len(frows)} records the AI check flagged as "likely not road damage" (score below {VERIFY_THRESHOLD}).', '',
               '| Recorded type | Records | Real damage | Not damage | Not answered | Real damage rate | 95% CI |', '|---|---|---|---|---|---|---|']
        for k in sorted({r['type'] for r in frows}) + ['All']:
            g = [r for r in frows if k == 'All' or r['type'] == k]
            v = [answer(r['real_damage']) for r in g]
            y, n = v.count(True), v.count(False)
            lo, hi = wilson(y, y + n)
            md.append(f'| {"**All**" if k == "All" else k} | {len(g)} | {y} | {n} | {len(g) - y - n} | '
                      + (f'{100 * y / (y + n):.1f}% | {100 * lo:.1f}% to {100 * hi:.1f}%' if y + n else 'n/a | n/a') + ' |')
        y, n = f.count(True), f.count(False)
        if y + n:
            md += ['', f'The flag was right (not road damage) for {n} of {y + n} answered flagged records '
                   f'({100 * n / (y + n):.1f}%); {y} flagged records show real damage.']
        both = [(r, s) for r in frows for s in rows if r['in_sample_item'] and s['item'] == r['in_sample_item']]
        dis = [(r, s) for r, s in both if answer(r['real_damage']) is not None and answer(s['real_damage']) is not None
               and answer(r['real_damage']) != answer(s['real_damage'])]
        if both:
            md += ['', f'{len(both)} flagged records are also in the 50-record sample; the two answers differ for {len(dis)}'
                   + (': ' + ', '.join(f"record {r['record_id']}" for r, _ in dis) if dis else '') + '.']
    text = '\n'.join(md) + '\n'
    path.with_name(path.stem + '_score.md').write_text(text, encoding='utf-8')
    print(text)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export')
    e.add_argument('--video', type=int, required=True)
    e.add_argument('--n', type=int, default=50)
    e.add_argument('--force', action='store_true')
    p = sub.add_parser('prepare')
    p.add_argument('--video', type=int, default=3)
    s = sub.add_parser('score')
    s.add_argument('checklist')
    s.add_argument('--flagged', help='flagged checklist (default: survey<id>_flagged_checklist.csv beside it)')
    a = ap.parse_args()
    if a.cmd == 'export':
        export(a)
    elif a.cmd == 'prepare':
        prepare(a.video)
    else:
        score(a)


if __name__ == '__main__':
    main()

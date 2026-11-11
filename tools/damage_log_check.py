"""Damage log correctness (RQ2): a random sample of one survey's damage records, checked by hand.

    python tools/damage_log_check.py export --video 3 --n 50     # writes the checklist (seed 42)
    python tools/damage_log_check.py score results/damage_log_check/survey3_checklist.csv

export draws N records of the survey at random (fixed seed), lists them in video order, and writes
results/damage_log_check/survey<id>_checklist.csv (UTF-8 with BOM, opens in Excel) with:
record id, type, time in the video, frame, coordinates, snapshot path, a link to the survey page at
that moment (the web app must be running and signed in: http://localhost:5173/videos/<id>?t=<s>),
a map link at the coordinates, and four blank columns to fill in:

    type_correct      yes = the damage in the snapshot / video is the type named; no = another type,
                      or not road damage at all
    time_correct      yes = the video at that time shows this damage
    location_correct  yes = the coordinates are where this damage is on the road (compare the video
                      with the map link; the GPS track is phone GPS, a few metres off is still "yes")
    duplicate         yes = the same physical damage is already another record of this survey
                      (write that record's id in duplicate_of if known); no = it is recorded once

Accepted answers: yes / y / 1 and no / n / 0 (any case). Leave a cell blank or write "unsure" to
leave that record out of that attribute's rate.

score reads the filled file and prints, per attribute, the correctness rate (yes / (yes + no)) with
a 95% Wilson interval, the duplicate rate, and the share of records correct on all three
attributes and not a duplicate. It also writes <checklist>_score.md beside the file.
"""

import argparse
import csv
import math
import random
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'backend' / 'pothole_detection.db'
SNAPS = ROOT / 'backend' / 'snapshots'
OUT = ROOT / 'results' / 'damage_log_check'
WEB = 'http://localhost:5173'
SEED = 42
NAMES = {'D00': 'Longitudinal crack', 'D10': 'Transverse crack', 'D20': 'Alligator crack', 'D40': 'Pothole'}
CHECKS = ['type_correct', 'time_correct', 'location_correct', 'duplicate']
YES, NO = {'yes', 'y', '1', 'true'}, {'no', 'n', '0', 'false'}


def mmss(t):
    return f'{int(t // 60):02d}:{t % 60:04.1f}'


def export(a):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    v = con.execute('select id, original_filename, status from videos where id = ?', (a.video,)).fetchone()
    if not v:
        sys.exit(f'No survey {a.video}.')
    rows = con.execute('select id, frame_number, timestamp, damage_type, confidence, ai_check_score, latitude, longitude, '
                       'frame_snapshot, position_source from detections where video_id = ? order by id', (a.video,)).fetchall()
    if len(rows) < a.n:
        sys.exit(f'Survey {a.video} has {len(rows)} records, fewer than {a.n}.')
    pick = sorted(random.Random(SEED).sample(list(rows), a.n), key=lambda r: (r['timestamp'], r['id']))
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f'survey{a.video}_checklist.csv'
    if out.exists() and not a.force:
        sys.exit(f'{out} exists (it may hold answers already); use --force to overwrite it.')
    with open(out, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh)
        w.writerow(['item', 'record_id', 'type', 'confidence', 'ai_check', 'video_time', 'time_s', 'frame',
                    'latitude', 'longitude', 'position_source', 'snapshot_path', 'survey_link', 'map_link']
                   + CHECKS + ['duplicate_of', 'notes'])
        for i, r in enumerate(pick, 1):
            lat, lon = r['latitude'], r['longitude']
            w.writerow([i, r['id'], f"{NAMES.get(r['damage_type'], r['damage_type'])} ({r['damage_type']})",
                        f"{r['confidence']:.2f}", '' if r['ai_check_score'] is None else f"{r['ai_check_score']:.2f}",
                        mmss(r['timestamp']), f"{r['timestamp']:.1f}", r['frame_number'],
                        '' if lat is None else f'{lat:.7f}', '' if lon is None else f'{lon:.7f}', r['position_source'],
                        str(SNAPS / r['frame_snapshot']) if r['frame_snapshot'] else '',
                        f"{WEB}/videos/{a.video}?t={r['timestamp']:.1f}",
                        '' if lat is None else f'https://www.openstreetmap.org/?mlat={lat:.7f}&mlon={lon:.7f}#map=19/{lat:.6f}/{lon:.6f}']
                       + [''] * (len(CHECKS) + 2))
    print(f'{a.n} of {len(rows)} records of survey {a.video} ({v["original_filename"]}), seed {SEED} -> {out}')


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


def score(a):
    path = Path(a.checklist)
    with open(path, newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))
    missing = [c for c in CHECKS if c not in (rows[0] if rows else {})]
    if missing:
        sys.exit(f'Columns missing: {missing}')
    md = [f'# Damage log correctness: {path.name}', '', f'{len(rows)} sampled records.', '',
          '| Attribute | Yes | No | Not answered | Rate (yes / answered) | 95% CI |', '|---|---|---|---|---|---|']
    for c in CHECKS:
        v = [answer(r[c]) for r in rows]
        y, n = v.count(True), v.count(False)
        lo, hi = wilson(y, y + n)
        label = 'Duplicate (rate = duplicate rate)' if c == 'duplicate' else c.replace('_', ' ').capitalize()
        rate = f'{100 * y / (y + n):.1f}%' if y + n else 'n/a'
        md.append(f'| {label} | {y} | {n} | {len(v) - y - n} | {rate} | '
                  + (f'{100 * lo:.1f}% to {100 * hi:.1f}%' if y + n else 'n/a') + ' |')
    full = [r for r in rows if all(answer(r[c]) is not None for c in CHECKS)]
    ok = sum(1 for r in full if answer(r['type_correct']) and answer(r['time_correct'])
             and answer(r['location_correct']) and not answer(r['duplicate']))
    lo, hi = wilson(ok, len(full))
    md += ['', f'Fully correct (type, time and location correct, not a duplicate): {ok} of {len(full)} fully answered records'
           + (f' = {100 * ok / len(full):.1f}% (95% CI {100 * lo:.1f}% to {100 * hi:.1f}%).' if full else '.')]
    types = {}
    for r in rows:
        t = answer(r['type_correct'])
        if t is not None:
            k = r['type']
            types.setdefault(k, [0, 0])[0 if t else 1] += 1
    if types:
        md += ['', 'Type correct per recorded type:', '', '| Recorded type | Yes | No | Rate |', '|---|---|---|---|'] + \
              [f'| {k} | {y} | {n} | {100 * y / (y + n):.1f}% |' for k, (y, n) in sorted(types.items())]
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
    s = sub.add_parser('score')
    s.add_argument('checklist')
    a = ap.parse_args()
    export(a) if a.cmd == 'export' else score(a)


if __name__ == '__main__':
    main()

"""Remove recordings from the local dataset, keeping a record of why (team decision 2026-11-09:
the hand-held R01-R03 are dropped so every recording used is mounted).

    python ml/local/exclude_recordings.py --ids R01,R02,R03 --reason excluded_handheld

- recordings.csv / route_groups.csv: rows are KEPT, with status = <reason> (others: used).
- Deleted: the recordings' frames (frames/, frames_full/), draft labels (autolabels/,
  autolabel_parts/), and every derived picture that shows them (contact sheets, band checks).
- Rows removed from manifest.csv, frames_all.csv, splits.csv, autolabel_log.csv, route_overlap.csv,
  and their tracks from route_groups.html.
- Val/test rows and their 50 m location drops are left exactly as they were (the drops are NOT
  recomputed against the smaller train set).
Refuses to touch a recording that has frames in val or test.
"""

import argparse
import json
import re
import sys
from collections import Counter

from common import OUT, read_csv, write_csv

CODES = ['D00', 'D10', 'D20', 'D40']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', required=True)
    ap.add_argument('--reason', required=True)
    a = ap.parse_args()
    ids = {x.strip() for x in a.ids.split(',') if x.strip()}

    splits = read_csv(OUT / 'splits.csv')
    bad = sorted({r['recording'] for r in splits if r['recording'] in ids and r['split'] != 'train'})
    if bad:
        sys.exit(f'{bad} have val/test frames: not removed (val/test must stay as reviewed).')

    for name in ('recordings.csv', 'route_groups.csv'):
        rows = read_csv(OUT / name)
        for r in rows:
            r['status'] = a.reason if r['id'] in ids else (r.get('status') or 'used')
        write_csv(OUT / name, rows)

    deleted = Counter()
    for d, pat in (('frames', '{}_s*.jpg'), ('frames_full', '{}_s*.jpg'), ('autolabels', '{}_s*.txt'),
                   ('autolabel_parts', '{}.csv'), ('contact', '{}.jpg')):
        for rid in ids:
            for p in (OUT / d).glob(pat.format(rid)):
                p.unlink()
                deleted[d] += 1
    # Derived pictures that show these recordings (made during the band and label checks).
    for p in [OUT / 'contact' / 'all_recordings.jpg', OUT / 'r01_road_scores.csv'] + \
             [p for p in (OUT / 'band_check').glob('*') if any(k in p.name for k in ('all_bands', 'crops', 'r01', 'autolabel_sample'))]:
        if p.exists():
            p.unlink()
            deleted['derived pictures'] += 1

    for name, key in (('manifest.csv', 'recording'), ('frames_all.csv', 'recording'), ('splits.csv', 'recording'),
                      ('autolabel_log.csv', 'recording')):
        rows = read_csv(OUT / name)
        keep = [r for r in rows if r[key] not in ids]
        write_csv(OUT / name, keep, list(rows[0].keys()))
        print(f'{name}: {len(rows) - len(keep)} rows removed, {len(keep)} left')
    ov = read_csv(OUT / 'route_overlap.csv')
    write_csv(OUT / 'route_overlap.csv', [r for r in ov if r['a'] not in ids and r['b'] not in ids], list(ov[0].keys()))

    html_p = OUT / 'route_groups.html'
    if html_p.exists():
        html = html_p.read_text(encoding='utf-8')
        m = re.search(r'const feats = (\[.*?\]);\n', html, flags=re.S)
        feats = [f for f in json.loads(m.group(1)) if f['id'] not in ids]
        html = html[:m.start(1)] + json.dumps(feats) + html[m.end(1):]
        for rid in ids:   # legend entries
            html = re.sub(rf'(, )?{rid}(?=[,<])', '', html)
        html_p.write_text(html, encoding='utf-8')
    print('Deleted files: ' + ', '.join(f'{k} {v}' for k, v in deleted.items()))

    rows = [r for r in read_csv(OUT / 'splits.csv') if r['dropped_by_location'] == '0']
    print('\n| Split | Recordings | Route groups | Frames | Frames with a draft box | D00 | D10 | D20 | D40 |')
    print('|---|---|---|---|---|---|---|---|---|')
    for s in ('train', 'val', 'test'):
        x = [r for r in rows if r['split'] == s]
        c = [sum(int(r[k]) for r in x) for k in CODES]
        print(f'| {s} | {len({r["recording"] for r in x})} | {len({r["route_group"] for r in x})} | {len(x)} | '
              f'{sum(1 for r in x if any(int(r[k]) for k in CODES))} | ' + ' | '.join(map(str, c)) + ' |')


if __name__ == '__main__':
    main()

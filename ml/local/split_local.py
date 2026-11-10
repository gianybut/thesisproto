"""Step 1.4: assign whole route groups to train / val / test (about 70/15/15 of frames).

    python ml/local/split_local.py --by-route-group [--radius-m 50] [--val 0.15] [--test 0.15]

1. Every route group goes to exactly one split (the script fails if a group ends up in two).
2. Location rule (team decision 2026-11-09): after the groups are assigned, a val or test frame
   whose GPS position lies within --radius-m of ANY train frame is dropped. This covers roads
   shared below the route-group threshold and the boundary between consecutive clips of one drive
   that went to different splits.
3. Choice: every assignment whose val and test hold 8-22% of the frames before the drop is scored
   on the frames left AFTER the drop: distance from the target shares, plus (weight 0.5) the
   distance of each class's share of the draft labels (autolabel_log.csv, kept boxes) from the
   same targets, plus (weight 0.5) the share of frames the location rule drops. Draft labels are
   used for this balance only. Ties go to the lexicographically first assignment, so the result
   is deterministic.

Reads manifest.csv, route_groups.csv, autolabel_log.csv. Writes data/local/splits.csv (every
frame: split, dropped_by_location, distance to the nearest train frame) and
results/step1_split.md.
"""

import argparse
import itertools
import math
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy.spatial import cKDTree

from common import OUT, ROOT, read_csv, refuse_overwrite, write_csv

CODES = ['D00', 'D10', 'D20', 'D40']


def metres(lat, lon, lat0):
    return np.column_stack([lat * 111_320.0, lon * 111_320.0 * math.cos(math.radians(lat0))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--by-route-group', action='store_true', required=True)
    ap.add_argument('--radius-m', type=float, default=50.0)
    ap.add_argument('--val', type=float, default=0.15)
    ap.add_argument('--test', type=float, default=0.15)
    ap.add_argument('--min-share', type=float, default=0.08)
    ap.add_argument('--max-share', type=float, default=0.22)
    a = ap.parse_args()

    refuse_overwrite(OUT / 'splits.csv', 'the split and 50 m drops the team kept on 2026-11-09 (computed with R01-R03 in train)')
    man = read_csv(OUT / 'manifest.csv')
    groups = {g['id']: g['route_group'] for g in read_csv(OUT / 'route_groups.csv')}
    log = read_csv(OUT / 'autolabel_log.csv')
    labelled = {r['recording'] for r in log}
    missing = sorted({m['recording'] for m in man} - labelled - {''})
    if missing:
        sys.exit(f'autolabel_log.csv has no rows for {", ".join(missing)}: run autolabel.py first')
    for m in man:
        if groups[m['recording']] != m['route_group']:
            sys.exit(f'{m["frame"]}: manifest says {m["route_group"]}, route_groups.csv says {groups[m["recording"]]}')
    boxes = defaultdict(Counter)
    for r in log:
        if r['kept'] == '1':
            boxes[r['frame']][r['code']] += 1

    gnames = sorted(set(groups.values()))
    gidx = {g: i for i, g in enumerate(gnames)}
    lat = np.array([float(m['lat']) for m in man])
    lon = np.array([float(m['lon']) for m in man])
    xy = metres(lat, lon, float(lat.mean()))
    fg = np.array([gidx[m['route_group']] for m in man])
    # For each frame: bitmask of the OTHER groups that have a frame within the radius.
    tree = cKDTree(xy)
    near = np.zeros(len(man), np.int64)
    for i, nb in enumerate(tree.query_ball_point(xy, a.radius_m)):
        for j in nb:
            if fg[j] != fg[i]:
                near[i] |= 1 << int(fg[j])
    cls = np.array([[boxes[m['frame']][c] for c in CODES] for m in man])

    # Aggregate frames by (group, near-mask) so each candidate is cheap to score.
    keys = defaultdict(lambda: [0, np.zeros(4)])
    for g, nm, c in zip(fg, near, cls):
        k = keys[(int(g), int(nm))]
        k[0] += 1
        k[1] += c
    kg = np.array([k[0] for k in keys])
    kn = np.array([k[1] for k in keys])
    kf = np.array([v[0] for v in keys.values()])
    kc = np.array([v[1] for v in keys.values()])
    total = kf.sum()
    gshare = np.array([kf[kg == i].sum() / total for i in range(len(gnames))])

    subsets = [s for r in range(1, len(gnames)) for s in itertools.combinations(range(len(gnames)), r)
               if a.min_share <= gshare[list(s)].sum() <= a.max_share]
    best = None
    for vs in subsets:
        vmask = sum(1 << i for i in vs)
        for ts in subsets:
            tmask = sum(1 << i for i in ts)
            if vmask & tmask:
                continue
            trmask = ((1 << len(gnames)) - 1) & ~(vmask | tmask)
            inval = ((1 << kg) & vmask) > 0
            intest = ((1 << kg) & tmask) > 0
            drop = (inval | intest) & ((kn & trmask) > 0)
            keepf = np.where(drop, 0, kf)
            keepc = np.where(drop[:, None], 0, kc)
            n = keepf.sum()
            sv, st = keepf[inval].sum() / n, keepf[intest].sum() / n
            ct = keepc.sum(0)
            cv = keepc[inval].sum(0) / np.maximum(ct, 1)
            cte = keepc[intest].sum(0) / np.maximum(ct, 1)
            score = (abs(sv - a.val) + abs(st - a.test)
                     + 0.5 * float(np.mean(np.abs(cv - a.val) + np.abs(cte - a.test)))
                     + 0.5 * kf[drop].sum() / total)
            cand = (round(score, 9), vs, ts)
            if best is None or cand < best:
                best = cand
    if best is None:
        sys.exit('No assignment puts val and test within the share limits.')
    _, vs, ts = best
    split_of = {g: 'val' if gidx[g] in vs else 'test' if gidx[g] in ts else 'train' for g in gnames}

    # Apply, and check the result independently of the search.
    split = np.array([split_of[m['route_group']] for m in man])
    tr = split == 'train'
    dist_train, _ = cKDTree(xy[tr]).query(xy)
    dropped = (~tr) & (dist_train <= a.radius_m)
    by_group = defaultdict(set)
    for m, s in zip(man, split):
        by_group[m['route_group']].add(s)
    bad = {g: s for g, s in by_group.items() if len(s) > 1}
    if bad:
        sys.exit(f'FAIL: route groups in more than one split: {bad}')
    kept_eval = (~tr) & ~dropped
    if len(xy[tr]) and (cKDTree(xy[tr]).query(xy[kept_eval])[0] <= a.radius_m).any():
        sys.exit('FAIL: a val/test frame within the radius of a train frame survived')

    rows = []
    for m, s, d, dr in zip(man, split, dist_train, dropped):
        rows.append(dict(frame=m['frame'], recording=m['recording'], route_group=m['route_group'], split=s,
                         dropped_by_location=int(dr), nearest_train_m='' if s == 'train' else round(float(d), 1),
                         D00=boxes[m['frame']]['D00'], D10=boxes[m['frame']]['D10'],
                         D20=boxes[m['frame']]['D20'], D40=boxes[m['frame']]['D40']))
    write_csv(OUT / 'splits.csv', rows)
    report(rows, split_of, a)


def report(rows, split_of, a):
    def summary(rs):
        return len(rs), [sum(r[c] for r in rs) for c in CODES], sum(1 for r in rs if any(r[c] for c in CODES))

    used = [r for r in rows if not r['dropped_by_location']]
    n_used = len(used)
    out = ['# Step 1.4: local split by route group', '',
           f'Rule: whole route groups per split; then val/test frames within {a.radius_m:.0f} m of any train frame '
           'are dropped (team decision 2026-11-09). Draft labels (autolabel, kept boxes) are used only to balance '
           'classes.', '',
           '| Split | Route groups | Frames | Share | Frames with a draft box | D00 | D10 | D20 | D40 |',
           '|---|---|---|---|---|---|---|---|---|']
    for s in ('train', 'val', 'test'):
        rs = [r for r in used if r['split'] == s]
        n, c, wb = summary(rs)
        gs = ', '.join(g for g, v in sorted(split_of.items()) if v == s)
        out.append(f'| {s} | {gs} | {n} | {n / n_used:.1%} | {wb} | ' + ' | '.join(str(x) for x in c) + ' |')
    dr = [r for r in rows if r['dropped_by_location']]
    out += ['', f'## Dropped by the {a.radius_m:.0f} m location rule: {len(dr)} frames', '',
            '| Recording | Route group | Split | Frames dropped | of frames in it | D00 | D10 | D20 | D40 |',
            '|---|---|---|---|---|---|---|---|---|']
    for rec in sorted({r['recording'] for r in rows if r['split'] != 'train'}):
        rr = [r for r in rows if r['recording'] == rec]
        d = [r for r in rr if r['dropped_by_location']]
        _, c, _ = summary(d)
        out.append(f'| {rec} | {rr[0]["route_group"]} | {rr[0]["split"]} | {len(d)} | {len(rr)} | '
                   + ' | '.join(str(x) for x in c) + ' |')
    _, c, _ = summary(dr)
    out.append(f'| **all** | | | **{len(dr)}** | | ' + ' | '.join(f'**{x}**' for x in c) + ' |')
    text = '\n'.join(out) + '\n'
    (ROOT / 'results').mkdir(exist_ok=True)
    (ROOT / 'results' / 'step1_split.md').write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()

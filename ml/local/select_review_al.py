"""Active learning review batches: "AL" (B v1, 150 frames), "AL2" (B v2, 300), and later rounds.

    python ml/local/select_review_al.py [--n 150] [--weights runs/v2/Bv1/weights/best.pt]      # AL (done)
    python ml/local/select_review_al.py --batch AL2 --n 300 --weights runs/v2/Bv2/weights/best.pt \
        --tag Bv2 --label "B v2" --priority D40,D20 --near-delta 0.10

The model runs on every train frame not yet in review_frames.csv (imgsz 1280, cached as
dets_<tag>_1280). Selection, taken in turn across the train route groups, at least --gap-s s apart
in a recording:
  1. class by class: the --priority classes in that order (AL2: D40 then D20, team decision
     2026-11-10), otherwise the class with the FEWEST reviewed train instances first: frames where
     the model detects that class at >= --rare-conf;
  2. then the most uncertain frames: the most detections with confidence between --low and --high
     (0.2-0.5), ties by the detection closest to 0.35.
--near-delta: only detections whose centre lies in the near zone count for 1 and 2 (near_zone.py:
top = band top + delta, bottom = band bottom or the R13/R14 bonnet line 0.73).
Drafts: the model's boxes at >= --low (data/local/review_drafts.csv). Appends the batch's rows to
review_frames.csv; writes results/step2_review_<batch>_batch.md.
"""

import argparse
import json
import random
from collections import Counter, defaultdict

from common import OUT, ROOT, SEED, read_csv, write_csv
import teacher_detect as td


def sec(f):
    return int(f.split('_s')[1][:4])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=150)
    ap.add_argument('--weights', default='runs/v2/Bv1/weights/best.pt')
    ap.add_argument('--rare-conf', type=float, default=0.25)
    ap.add_argument('--low', type=float, default=0.20)
    ap.add_argument('--high', type=float, default=0.50)
    ap.add_argument('--gap-s', type=int, default=3)
    ap.add_argument('--batch', default='AL')
    ap.add_argument('--tag', default='Bv1', help='detection cache name')
    ap.add_argument('--label', default='B v1', help='model name in the reasons and the report')
    ap.add_argument('--priority', help='classes first, in this order, e.g. D40,D20')
    ap.add_argument('--near-delta', type=float, help='count only detections in the near zone')
    a = ap.parse_args()
    rng = random.Random(f'{SEED}-AL' if a.batch == 'AL' else f'{SEED}-{a.batch}')
    sel = read_csv(OUT / 'review_frames.csv')
    if any(r.get('batch') == a.batch for r in sel):
        raise SystemExit(f'Batch {a.batch} is already in review_frames.csv.')
    reviewer = 'Gian Paolo Ybut'
    done = {r['frame'] for r in sel}
    # Reviewed train instances per class right now (train and earlier AL frames accepted in the tool).
    log = {r['frame']: r for r in read_csv(OUT / 'review_log.csv')}
    have = Counter()
    for r in sel:
        if r['split'] == 'train' and log.get(r['frame'], {}).get('reviewed') == 'yes':
            s = json.loads((OUT / 'reviewed' / 'state' / f'{r["frame"][:-4]}.json').read_text(encoding='utf-8'))
            have.update(b['cls'] for b in s['boxes'])
    order = a.priority.split(',') if a.priority else sorted(['D00', 'D10', 'D20', 'D40'], key=lambda c: (have[c], c))
    print('Reviewed train instances: ' + ', '.join(f'{c} {have[c]}' for c in order) + ' -> priority ' + ' > '.join(order),
          flush=True)
    cand = [r for r in read_csv(OUT / 'splits.csv') if r['split'] == 'train' and r['frame'] not in done]
    print(f'{a.label} on {len(cand)} unreviewed train frames ...', flush=True)
    dets = td.detect([r['frame'] for r in cand], 1280, weights=ROOT / a.weights, tag=a.tag)
    if a.near_delta is not None:   # selection looks at near-zone detections only (drafts keep all)
        from near_zone import BOTTOM
        man = {r['frame']: r for r in read_csv(OUT / 'manifest.csv')}

        def near(f, d):
            m = man[f]
            fh, top = int(m['frame_h']), int(m['band_top_px'])
            yc = (d['box'][1] + d['box'][3]) / 2 + top
            bot = BOTTOM.get(m['recording'], float(m['band_bottom']))
            return (float(m['band_top']) + a.near_delta) * fh <= yc <= bot * fh
        sel_dets = {f: [d for d in ds if near(f, d)] for f, ds in dets.items()}
    else:
        sel_dets = dets

    taken = defaultdict(list)
    for r in sel:
        taken[r['frame'].split('_s')[0]].append(sec(r['frame']))

    def free(f):
        return all(abs(sec(f) - s) >= a.gap_s for s in taken[f.split('_s')[0]])

    def uncertainty(f):
        u = [d['conf'] for d in sel_dets.get(f, []) if a.low <= d['conf'] <= a.high]
        return (len(u), -min((abs(c - 0.35) for c in u), default=1))

    by_group = defaultdict(list)
    for r in cand:
        by_group[r['route_group']].append(r)
    groups = sorted(by_group)
    tiers = [(c, {g: [r for r in sorted(by_group[g], key=lambda r: rng.random())
                       if any(d['cls'] == c and d['conf'] >= a.rare_conf for d in sel_dets.get(r['frame'], []))]
                  for g in groups}) for c in order]
    tiers.append(('uncertain 0.2-0.5', {g: sorted([r for r in by_group[g] if uncertainty(r['frame'])[0] > 0],
                                                  key=lambda r: uncertainty(r['frame']), reverse=True) for g in groups}))
    picked, chosen = [], set()
    for name, queues in tiers:
        while len(picked) < a.n and any(queues.values()):
            for g in groups:
                while queues[g]:
                    r = queues[g].pop(0)
                    if r['frame'] not in chosen and free(r['frame']):
                        picked.append((r, name))
                        chosen.add(r['frame'])
                        taken[r['frame'].split('_s')[0]].append(sec(r['frame']))
                        break
                if len(picked) >= a.n:
                    break
    new = [dict(frame=r['frame'], split='train', route_group=r['route_group'], recording=r['recording'],
                has_draft=int(any(d['conf'] >= a.low for d in dets.get(r['frame'], []))),
                reviewer=reviewer, batch=a.batch, reason=f'{a.label} {why}')
           for r, why in picked]
    write_csv(OUT / 'review_frames.csv', sel + new, list(sel[0].keys()))
    dp = OUT / 'review_drafts.csv'
    old = [o for o in (read_csv(dp) if dp.exists() else []) if o['frame'] not in chosen]
    rows = old + [dict(frame=f, x1=round(d['box'][0], 1), y1=round(d['box'][1], 1), x2=round(d['box'][2], 1),
                       y2=round(d['box'][3], 1), cls=d['cls'], conf=round(d['conf'], 4), source=f'{a.label} {a.batch}')
                  for f in sorted(chosen) for d in dets.get(f, []) if d['conf'] >= a.low]
    write_csv(dp, rows, ['frame', 'x1', 'y1', 'x2', 'y2', 'cls', 'conf', 'source'])
    why = Counter(w for _, w in picked)
    grp = Counter(r['route_group'] for r, _ in picked)
    md = [f'# Review batch "{a.batch}" (active learning with {a.label})', '',
          'Reviewed train instances when selected: ' + ', '.join(f'{c} {have[c]}' for c in order)
          + ('; classes taken in the order ' + ' > '.join(order) + ' (team priority)' if a.priority
             else '; classes taken fewest first') + '.'
          + (f' Selection counts near-zone detections only (band top + {a.near_delta}).' if a.near_delta is not None else ''),
          '', f'{len(new)} train frames: ' + ', '.join(f'{k} {v}' for k, v in why.items()) +
          f'; drafts are {a.label} boxes at >= {a.low} (weights {a.weights}).', '', '| Route group | Frames |', '|---|---|']
    md += [f'| {g} | {grp[g]} |' for g in groups]
    (ROOT / 'results' / f'step2_review_{a.batch}_batch.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

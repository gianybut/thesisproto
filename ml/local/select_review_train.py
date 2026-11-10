"""Review batch "train": about 300 train frames for the team to label (team decision 2026-11-09).

    python ml/local/select_review_train.py [--n 300] [--low 0.10] [--draft-conf 0.10] [--gap-s 3]

From train frames not yet in review_frames.csv: two thirds are frames where the RDD2022 teacher
detects damage at confidence >= --low, rare classes first (D10 frames, then D20, then D00/D40),
taken in turn across the train route groups; one third are random frames spread over the route
groups by size. At least --gap-s seconds between selected frames of one recording.

Drafts for these frames are the TEACHER's boxes at confidence >= --draft-conf (written to
data/local/review_drafts.csv, which the review tool uses instead of the stand-in drafts for the
frames listed there). Route groups are shared among the reviewers by frame count.
Appends batch "train" rows to review_frames.csv; writes results/step2_review_train_batch.md.
"""

import argparse
import csv
import random
from collections import Counter, defaultdict

from common import OUT, ROOT, SEED, read_csv, write_csv
import teacher_detect as td

TIERS = [('D10', ['D10']), ('D20', ['D20']), ('D00/D40', ['D00', 'D40'])]


def sec(f):
    return int(f.split('_s')[1][:4])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=300)
    ap.add_argument('--low', type=float, default=0.10)
    ap.add_argument('--draft-conf', type=float, default=0.10)
    ap.add_argument('--gap-s', type=int, default=3)
    ap.add_argument('--batch', default='train')
    a = ap.parse_args()
    rng = random.Random(f'{SEED}-{a.batch}')
    sel = read_csv(OUT / 'review_frames.csv')
    if any(r.get('batch') == a.batch for r in sel):
        raise SystemExit(f'Batch {a.batch} is already in review_frames.csv.')
    reviewers = sorted({r['reviewer'] for r in sel})
    done = {r['frame'] for r in sel}
    cand = [r for r in read_csv(OUT / 'splits.csv') if r['split'] == 'train' and r['frame'] not in done]
    dets = td.detect([r['frame'] for r in cand], 1280)

    taken = defaultdict(list)
    for r in sel:
        taken[r['frame'].split('_s')[0]].append(sec(r['frame']))

    def free(f):
        return all(abs(sec(f) - s) >= a.gap_s for s in taken[f.split('_s')[0]])

    def take(f):
        taken[f.split('_s')[0]].append(sec(f))

    by_group = defaultdict(list)
    for r in cand:
        by_group[r['route_group']].append(r)
    for g in by_group:
        rng.shuffle(by_group[g])
    groups = sorted(by_group)
    want_det = round(a.n * 2 / 3)
    picked, chosen = [], set()
    for tier, classes in TIERS:
        queues = {g: [r for r in by_group[g] if any(d['cls'] in classes and d['conf'] >= a.low
                                                    for d in dets.get(r['frame'], []))] for g in groups}
        while len(picked) < want_det and any(queues.values()):
            for g in groups:   # one frame per route group in turn
                while queues[g]:
                    r = queues[g].pop(0)
                    if r['frame'] not in chosen and free(r['frame']):
                        picked.append((r, f'teacher {tier}'))
                        chosen.add(r['frame'])
                        take(r['frame'])
                        break
                if len(picked) >= want_det:
                    break
    n_det = len(picked)
    want_rand = a.n - n_det
    total = sum(len(v) for v in by_group.values())
    quota = {g: want_rand * len(by_group[g]) / total for g in groups}
    alloc = {g: int(q) for g, q in quota.items()}
    for g in sorted(quota, key=lambda g: (-(quota[g] - alloc[g]), g))[:want_rand - sum(alloc.values())]:
        alloc[g] += 1
    for g in groups:
        got = 0
        for r in by_group[g]:
            if got >= alloc[g]:
                break
            if r['frame'] not in chosen and free(r['frame']):
                picked.append((r, 'random'))
                chosen.add(r['frame'])
                take(r['frame'])
                got += 1

    # Share the route groups among the reviewers by frame count (largest first to the least loaded).
    size = Counter(r['route_group'] for r, _ in picked)
    load = {w: 0 for w in reviewers}
    owner = {}
    for g in sorted(size, key=lambda g: (-size[g], g)):
        w = min(load, key=lambda k: (load[k], k))
        owner[g] = w
        load[w] += size[g]
    new = [dict(frame=r['frame'], split='train', route_group=r['route_group'], recording=r['recording'],
                has_draft=int(any(d['conf'] >= a.draft_conf for d in dets.get(r['frame'], []))),
                reviewer=owner[r['route_group']], batch=a.batch, reason=why) for r, why in picked]
    fields = list(sel[0].keys())
    write_csv(OUT / 'review_frames.csv', sel + new, fields)

    # Teacher drafts for these frames.
    dp = OUT / 'review_drafts.csv'
    old = read_csv(dp) if dp.exists() else []
    old = [o for o in old if o['frame'] not in chosen]
    rows = old + [dict(frame=f, x1=round(d['box'][0], 1), y1=round(d['box'][1], 1), x2=round(d['box'][2], 1),
                       y2=round(d['box'][3], 1), cls=d['cls'], conf=round(d['conf'], 4), source=f'teacher {a.batch}')
                  for f in sorted(chosen) for d in dets.get(f, []) if d['conf'] >= a.draft_conf]
    write_csv(dp, rows, ['frame', 'x1', 'y1', 'x2', 'y2', 'cls', 'conf', 'source'])

    why = Counter(w for _, w in picked)
    dcls = Counter(r['cls'] for r in rows if r['frame'] in chosen)
    md = [f'# Review batch "{a.batch}": train frames', '',
          f'{len(new)} train frames: {n_det} where the teacher detects damage at >= {a.low} (rare classes first: '
          + ', '.join(f'{t} {why["teacher " + t]}' for t, _ in TIERS) + f'), {why["random"]} random; at least '
          f'{a.gap_s} s apart within a recording. Drafts: teacher boxes at >= {a.draft_conf} ('
          + ', '.join(f'{c} {dcls[c]}' for c in ('D00', 'D10', 'D20', 'D40')) + ').', '',
          '| Route group | Frames | Reviewer |', '|---|---|---|']
    for g in groups:
        md.append(f'| {g} | {size[g]} | {owner.get(g, "-")} |')
    md += ['', '| Reviewer | Frames |', '|---|---|'] + [f'| {w} | {n} |' for w, n in load.items()]
    (ROOT / 'results' / f'step2_review_{a.batch}_batch.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

"""Step 2.3b: a second review batch for val and test (team request 2026-11-09), so that test has
about 20 or more instances per class.

    python ml/local/select_review_more.py [--per-split 150] [--low 0.10] [--gap-s 3]

Candidates: val/test frames the 50 m location rule kept that are not yet in review_frames.csv.
Per split: half the frames are ones where the RDD2022 teacher detects D10, D20 or D40 at
confidence >= --low (taken in turn D10, D20, D40, random within each, so the rare classes get their
share); the other half are random frames, spread over the split's route groups by size. A new frame
is at least --gap-s seconds away from every selected frame of the same recording (no near-repeats
of the same damage). Each route group keeps the reviewer it had in batch 1.

Drafts shown in the review tool stay the stand-in's (autolabel_log.csv), as for batch 1.

Expected instances per class are estimated from the reviewed VAL frames only: the mean number of
reviewed instances of a class in frames where the teacher does / does not detect that class at
--low, times the number of such frames selected.
Appends batch-2 rows to data/local/review_frames.csv and writes results/step2_review_batch2.md.
"""

import argparse
import json
import random
from collections import Counter, defaultdict

from common import OUT, ROOT, SEED, read_csv, write_csv
import teacher_detect as td

CODES = ['D00', 'D10', 'D20', 'D40']
TARGET = ['D10', 'D20', 'D40']


def sec(frame):
    return int(frame.split('_s')[1][:4])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-split', type=int, default=150)
    ap.add_argument('--low', type=float, default=0.10)
    ap.add_argument('--gap-s', type=int, default=3)
    a = ap.parse_args()
    rng = random.Random(f'{SEED}-batch2')
    rule = json.loads((OUT / 'teacher' / 'label_rule.json').read_text())
    imgsz = rule['imgsz']
    sel = read_csv(OUT / 'review_frames.csv')
    if any(r.get('batch') == '2' for r in sel):
        raise SystemExit('Batch 2 is already in review_frames.csv.')
    owner = {r['route_group']: r['reviewer'] for r in sel}
    chosen_names = {r['frame'] for r in sel}
    rows = [r for r in read_csv(OUT / 'splits.csv') if r['split'] in ('val', 'test') and r['dropped_by_location'] == '0']
    cand = [r for r in rows if r['frame'] not in chosen_names]
    print(f'Teacher on {len(cand)} candidate frames at {imgsz} ...', flush=True)
    dets = td.detect([r['frame'] for r in cand] + [r['frame'] for r in sel], imgsz)

    def has(f, c):
        return any(d['cls'] == c and d['conf'] >= a.low for d in dets.get(f, []))

    taken = defaultdict(list)   # recording -> seconds already selected
    for r in sel:
        taken[r['frame'].split('_s')[0]].append(sec(r['frame']))

    def free(f):
        rec = f.split('_s')[0]
        return all(abs(sec(f) - s) >= a.gap_s for s in taken[rec])

    def take(f):
        taken[f.split('_s')[0]].append(sec(f))

    new = []
    for split in ('val', 'test'):
        pool = [r for r in cand if r['split'] == split]
        rng.shuffle(pool)
        want_det, want_rand = a.per_split // 2, a.per_split - a.per_split // 2
        picked = []
        queues = {c: [r for r in pool if has(r['frame'], c)] for c in TARGET}
        while len(picked) < want_det and any(queues.values()):
            for c in TARGET:
                while queues[c]:
                    r = queues[c].pop(0)
                    if r['frame'] not in {p['frame'] for p, _ in picked} and free(r['frame']):
                        picked.append((r, f'teacher {c}'))
                        take(r['frame'])
                        break
                if len(picked) >= want_det:
                    break
        n_det = len(picked)
        want_rand = a.per_split - n_det   # if too few teacher-detected frames exist, random ones fill the rest
        rest = [r for r in pool if r['frame'] not in {p['frame'] for p, _ in picked}]
        groups = defaultdict(list)
        for r in rest:
            groups[r['route_group']].append(r)
        total = sum(len(v) for v in groups.values())
        quota = {g: want_rand * len(v) / total for g, v in groups.items()}
        alloc = {g: int(q) for g, q in quota.items()}
        for g in sorted(quota, key=lambda g: (-(quota[g] - alloc[g]), g))[:want_rand - sum(alloc.values())]:
            alloc[g] += 1
        for g in sorted(groups):
            got = 0
            for r in groups[g]:
                if got >= alloc[g]:
                    break
                if free(r['frame']):
                    picked.append((r, 'random'))
                    take(r['frame'])
                    got += 1
        for r, why in picked:
            new.append(dict(frame=r['frame'], split=split, route_group=r['route_group'], recording=r['recording'],
                            has_draft=int(any(int(r[c]) for c in CODES)), reviewer=owner[r['route_group']], batch=2,
                            reason=why))
        print(f'{split}: {n_det} teacher-detected + {len(picked) - n_det} random', flush=True)

    # Expected instances, from rates on the reviewed val frames.
    val_sel = [r for r in sel if r['split'] == 'val']
    rate = {}
    for c in CODES:
        hit, miss = Counter(), Counter()
        for r in val_sel:
            s = json.loads((OUT / 'reviewed' / 'state' / f'{r["frame"][:-4]}.json').read_text(encoding='utf-8'))
            n = sum(b['cls'] == c for b in s['boxes'])
            (hit if has(r['frame'], c) else miss).update(frames=1, inst=n)
        rate[c] = (hit['inst'] / hit['frames'] if hit['frames'] else 0.0, miss['inst'] / miss['frames'] if miss['frames'] else 0.0,
                   hit['frames'], miss['frames'])
    current = {}
    for split in ('val', 'test'):
        cnt = Counter()
        for r in sel:
            if r['split'] == split:
                s = json.loads((OUT / 'reviewed' / 'state' / f'{r["frame"][:-4]}.json').read_text(encoding='utf-8'))
                cnt.update(b['cls'] for b in s['boxes'])
        current[split] = cnt
    md = ['# Review batch 2 (val and test expansion)', '',
          f'{len(new)} new frames; teacher (RDD2022 only) at imgsz {imgsz}, low threshold {a.low}; at least '
          f'{a.gap_s} s from any selected frame of the same recording; 50 m rule respected (only frames it kept).', '',
          '| Split | Teacher-detected frames (D10 / D20 / D40 turns) | Random frames | Route groups (reviewer) |',
          '|---|---|---|---|']
    for split in ('val', 'test'):
        x = [n for n in new if n['split'] == split]
        why = Counter(n['reason'] for n in x)
        gr = Counter((n['route_group'], n['reviewer']) for n in x)
        md.append(f'| {split} | {sum(v for k, v in why.items() if k != "random")} '
                  f'({why["teacher D10"]} / {why["teacher D20"]} / {why["teacher D40"]}) | {why["random"]} | '
                  + ', '.join(f'{g} {n} ({w})' for (g, w), n in sorted(gr.items())) + ' |')
    md += ['', '## Expected reviewed instances after batch 2 (estimate)', '',
           'Rates from the 120 reviewed val frames: mean reviewed instances of the class per frame where the teacher '
           f'detects that class at >= {a.low}, and per frame where it does not.', '',
           '| Class | Rate if detected (frames) | Rate if not (frames) | Val now | Val expected | Test now | **Test expected** | Test >= 20? |',
           '|---|---|---|---|---|---|---|---|']
    for c in CODES:
        rh, rm, nh, nm = rate[c]
        exp = {}
        for split in ('val', 'test'):
            x = [n for n in new if n['split'] == split]
            k = sum(has(n['frame'], c) for n in x)
            exp[split] = current[split][c] + k * rh + (len(x) - k) * rm
        md.append(f'| {c} | {rh:.2f} ({nh}) | {rm:.3f} ({nm}) | {current["val"][c]} | {exp["val"]:.0f} | '
                  f'{current["test"][c]} | **{exp["test"]:.0f}** | {"yes" if exp["test"] >= 20 else "**no**"} |')
    fields = list(sel[0].keys())
    for f_ in ('batch', 'reason'):
        if f_ not in fields:
            fields.append(f_)
    for r in sel:
        r.setdefault('batch', 1)
        r.setdefault('reason', 'batch 1 (stand-in draft or random)')
    write_csv(OUT / 'review_frames.csv', sel + new, fields)
    (ROOT / 'results' / 'step2_review_batch2.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

"""Add frames to the "train" review batch for chosen classes (team request 2026-11-10: about 50 where
the teacher detects D40 and 30 where it detects D00).

    python ml/local/extend_train_batch.py --add D40=50 D00=30 [--low 0.10] [--gap-s 3]

From train frames not yet in review_frames.csv: frames where the teacher detects the class at
>= --low, taken in turn across the train route groups (random within a group, fixed seed), at least
--gap-s seconds from every selected frame of the same recording. Drafts: the teacher's boxes at
>= --low, appended to data/local/review_drafts.csv. Rows join batch "train".
"""

import argparse
import random
from collections import Counter, defaultdict

from common import OUT, ROOT, SEED, read_csv, write_csv
import teacher_detect as td

REVIEWER = 'Gian Paolo Ybut'


def sec(f):
    return int(f.split('_s')[1][:4])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--add', nargs='+', required=True, help='CLASS=N ...')
    ap.add_argument('--low', type=float, default=0.10)
    ap.add_argument('--gap-s', type=int, default=3)
    a = ap.parse_args()
    want = [(x.split('=')[0], int(x.split('=')[1])) for x in a.add]
    rng = random.Random(f'{SEED}-extend-' + '-'.join(a.add))
    sel = read_csv(OUT / 'review_frames.csv')
    done = {r['frame'] for r in sel}
    cand = [r for r in read_csv(OUT / 'splits.csv') if r['split'] == 'train' and r['frame'] not in done]
    dets = td.detect([r['frame'] for r in cand], 1280)
    taken = defaultdict(list)
    for r in sel:
        taken[r['frame'].split('_s')[0]].append(sec(r['frame']))

    def free(f):
        return all(abs(sec(f) - s) >= a.gap_s for s in taken[f.split('_s')[0]])

    by_group = defaultdict(list)
    for r in cand:
        by_group[r['route_group']].append(r)
    groups = sorted(by_group)
    for g in groups:
        rng.shuffle(by_group[g])
    picked, chosen = [], set()
    for cls, n in want:
        queues = {g: [r for r in by_group[g] if any(d['cls'] == cls and d['conf'] >= a.low for d in dets.get(r['frame'], []))]
                  for g in groups}
        got = 0
        while got < n and any(queues.values()):
            for g in groups:
                while queues[g]:
                    r = queues[g].pop(0)
                    if r['frame'] not in chosen and free(r['frame']):
                        picked.append((r, f'teacher {cls} (extension)'))
                        chosen.add(r['frame'])
                        taken[r['frame'].split('_s')[0]].append(sec(r['frame']))
                        got += 1
                        break
                if got >= n:
                    break
        print(f'{cls}: {got} of {n} frames', flush=True)
    new = [dict(frame=r['frame'], split='train', route_group=r['route_group'], recording=r['recording'],
                has_draft=1, reviewer=REVIEWER, batch='train', reason=why) for r, why in picked]
    write_csv(OUT / 'review_frames.csv', sel + new, list(sel[0].keys()))
    dp = OUT / 'review_drafts.csv'
    rows = read_csv(dp) + [dict(frame=f, x1=round(d['box'][0], 1), y1=round(d['box'][1], 1), x2=round(d['box'][2], 1),
                                y2=round(d['box'][3], 1), cls=d['cls'], conf=round(d['conf'], 4),
                                source='teacher train extension')
                           for f in sorted(chosen) for d in dets.get(f, []) if d['conf'] >= a.low]
    write_csv(dp, rows, ['frame', 'x1', 'y1', 'x2', 'y2', 'cls', 'conf', 'source'])
    grp = Counter(r['route_group'] for r, _ in picked)
    note = (f'\n\nExtension (2026-11-10): {len(new)} more frames, ' + ', '.join(f'{c} {sum(1 for _, w in picked if w.startswith("teacher " + c))}' for c, _ in want)
            + f' (teacher >= {a.low}, in turn across route groups: ' + ', '.join(f'{g} {grp[g]}' for g in sorted(grp)) + ').\n')
    p = ROOT / 'results' / 'step2_review_train_batch.md'
    p.write_text(p.read_text(encoding='utf-8').rstrip() + note, encoding='utf-8')
    print(note.strip())


if __name__ == '__main__':
    main()

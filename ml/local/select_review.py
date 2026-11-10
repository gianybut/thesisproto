"""Step 2.3: choose the val and test frames the team reviews, and split them among the reviewers.

    python ml/local/select_review.py [--per-split 120] [--reviewers 3]

Per split (val, test), from frames the 50 m location rule kept: EVERY frame with a kept draft box
(autolabel), then random frames without one up to --per-split, spread over the split's route
groups in proportion to their frames (fixed seed), so missed damage and true background are
checked too. If a split had more draft frames than --per-split, a random subset would be taken.

Reviewers get whole route groups (balanced by frame count), so each reviewer judges a road
consistently. Writes data/local/review_frames.csv; the review tool (tools/review_labels/) reads it.
"""

import argparse
import random
from collections import defaultdict

from common import OUT, SEED, read_csv, write_csv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-split', type=int, default=120)
    ap.add_argument('--reviewers', type=int, default=3)
    a = ap.parse_args()
    rng = random.Random(SEED)

    rows = [r for r in read_csv(OUT / 'splits.csv') if r['split'] in ('val', 'test') and r['dropped_by_location'] == '0']
    chosen = []
    for split in ('val', 'test'):
        rs = [r for r in rows if r['split'] == split]
        draft = [r for r in rs if any(int(r[c]) for c in ('D00', 'D10', 'D20', 'D40'))]
        empty = [r for r in rs if r not in draft]
        if len(draft) > a.per_split:
            draft = rng.sample(draft, a.per_split)
        need = a.per_split - len(draft)
        by_group = defaultdict(list)
        for r in empty:
            by_group[r['route_group']].append(r)
        # Largest-remainder allocation of the empty frames over route groups by their size.
        quota = {g: need * len(v) / len(empty) for g, v in by_group.items()}
        alloc = {g: int(q) for g, q in quota.items()}
        for g in sorted(quota, key=lambda g: (-(quota[g] - alloc[g]), g))[:need - sum(alloc.values())]:
            alloc[g] += 1
        picked = [r for g in sorted(by_group) for r in rng.sample(by_group[g], alloc[g])]
        for r in draft + picked:
            chosen.append(dict(frame=r['frame'], split=split, route_group=r['route_group'], recording=r['recording'],
                               has_draft=int(r in draft)))
        print(f'{split}: {len(draft)} frames with a draft box + {len(picked)} without '
              f'({", ".join(f"{g} {n}" for g, n in sorted(alloc.items()))})')

    # Whole route groups per reviewer, largest first onto the least-loaded reviewer.
    load = {f'Reviewer {chr(65 + i)}': 0 for i in range(a.reviewers)}
    owner = {}
    sizes = defaultdict(int)
    for c in chosen:
        sizes[c['route_group']] += 1
    for g in sorted(sizes, key=lambda g: (-sizes[g], g)):
        who = min(load, key=lambda k: (load[k], k))
        owner[g] = who
        load[who] += sizes[g]
    for c in chosen:
        c['reviewer'] = owner[c['route_group']]
    rng.shuffle(chosen)   # review order within a reviewer is random, not by time along the road
    chosen.sort(key=lambda c: c['reviewer'])
    write_csv(OUT / 'review_frames.csv', chosen)
    for who, n in load.items():
        print(f'{who}: {n} frames, route groups {", ".join(g for g, o in sorted(owner.items()) if o == who)}')
    print(f'-> {OUT / "review_frames.csv"}')


if __name__ == '__main__':
    main()

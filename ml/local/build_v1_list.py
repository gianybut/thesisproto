"""Training list for run v1 (final label freeze, 2026-11-11), from data/local/yolo_nz after export_yolo.py.

    python ml/local/build_v1_list.py [--max-negatives 1500] [--repeat 3] [--seed 0]

- Damage frames: all of them, from every labeller; frames with D10, D20 or D40 repeated x3 (as run B).
- Negatives ("no damage" frames), capped at --max-negatives, chosen in this order (team decision 2026-11-11):
    1. the single-reviewer frames (Gian Paolo Ybut, review tool), all kept;
    2. a random sample (seed) of Kyle's and Gian's annotation-site negatives, to fill the cap;
    3. Janmikael's site negatives only if 1-2 are not enough.
- No RDD2022 replay. Val = val.txt (reviewed 270 + site 1,354); val_reviewed.yaml / val_new.yaml are
  there for the selection decision.
Writes yolo_nz/v1_train.txt, yolo_nz/v1.yaml and results/train_list_counts.md, and appends the
negative choice to results/label_quality.md.
"""

import argparse
import csv
import random
from collections import Counter
from pathlib import Path

from common import OUT, ROOT

Y = OUT / 'yolo_nz'
CODES = ['D00', 'D10', 'D20', 'D40']


def labels(path):
    p = Y / 'labels' / 'train' / (Path(path).stem + '.txt')
    return [int(l.split()[0]) for l in p.read_text().splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-negatives', type=int, default=1500)
    ap.add_argument('--repeat', type=int, default=3)
    ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    who = {r['frame']: r['labeled_by'] for r in csv.DictReader(open(Y / 'site_frames.csv', encoding='utf-8'))}
    train = [l for l in (Y / 'local_train.txt').read_text().splitlines() if l.strip()]
    lab = {p: labels(p) for p in train}
    dmg = [p for p in train if lab[p]]
    neg = [p for p in train if not lab[p]]
    src = lambda p: who.get(Path(p).name, 'reviewed')
    tiers = [[p for p in neg if src(p) == 'reviewed'],
             sorted(p for p in neg if src(p) in ('Kyle', 'Gian')),
             sorted(p for p in neg if src(p) == 'Janmikael')]
    rng = random.Random(a.seed)
    chosen, left = [], a.max_negatives
    for t in tiers:
        take = t if len(t) <= left else rng.sample(t, left)
        chosen += take
        left -= len(take)
    rare = [p for p in dmg if any(k in (1, 2, 3) for k in lab[p])]
    lst = dmg + rare * (a.repeat - 1) + chosen
    rng.shuffle(lst)
    (Y / 'v1_train.txt').write_text('\n'.join(lst) + '\n')
    names = ''.join(f'  {i}: {c}\n' for i, c in enumerate(CODES))
    (Y / 'v1.yaml').write_text(f'path: {Y.as_posix()}\ntrain: v1_train.txt\nval: val.txt\nnc: 4\nnames:\n{names}')

    per_epoch = Counter(k for p in lst for k in lab[p])
    unique = Counter(k for p in set(lst) for k in lab[p])
    neg_src = Counter(src(p) for p in chosen)
    dmg_src = Counter(src(p) for p in dmg)
    md = ['# Run v1 training list (per epoch)', '',
          f'Data: data/local/yolo_nz from `backups/{(ROOT / "results/FINAL_SNAPSHOT.txt").read_text().split()[0]}`. '
          f'Built by ml/local/build_v1_list.py --max-negatives {a.max_negatives} --repeat {a.repeat} --seed {a.seed}.', '',
          '| | Images | ' + ' | '.join(CODES) + ' |', '|---|---|---|---|---|---|',
          f'| Per epoch (after x{a.repeat}) | {len(lst)} | ' + ' | '.join(str(per_epoch[i]) for i in range(4)) + ' |',
          f'| Unique frames | {len(set(lst))} | ' + ' | '.join(str(unique[i]) for i in range(4)) + ' |', '',
          f'Damage frames: {len(dmg)}, all kept (' + ', '.join(f'{k} {v}' for k, v in sorted(dmg_src.items())) + f'); '
          f'{len(rare)} with D10/D20/D40 repeated x{a.repeat}.',
          f'Negatives: {len(chosen)} of {len(neg)} (cap {a.max_negatives}): ' +
          ', '.join(f'{k} {v}' for k, v in sorted(neg_src.items())) +
          f'. Order: single-reviewer negatives all ({len(tiers[0])}), then a random sample (seed {a.seed}) of Kyle\'s '
          f'and Gian\'s site negatives ({len(tiers[1])} available), Janmikael\'s ({len(tiers[2])}) only if needed.',
          f'Negatives are {len(chosen) / len(lst):.0%} of the images per epoch. No RDD2022 replay.', '',
          'Ultralytics trains on this list every epoch (mosaic mixes four images per sample until the last 10 epochs).', '']
    (ROOT / 'results/train_list_counts.md').write_text('\n'.join(md), encoding='utf-8')
    with open(ROOT / 'results/label_quality.md', 'a', encoding='utf-8') as fh:
        fh.write('\n## Negatives used for training (run v1)\n\n' + md[9] + '\n' + md[10] + '\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

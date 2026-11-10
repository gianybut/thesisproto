"""Data for the RDD2022-only teacher model (pseudo-labelling and the "foreign only" reference row).

    python ml/teacher_data.py [--per-country 1000] [--val-per-country 150]

Train: up to --per-country random images from each of the six countries' TRAIN split (all of a
smaller pool). Validation while training: --val-per-country random images from each VAL split
(kept small so an epoch stays short). The final number is taken on the FULL foreign val split
(data_fullval.yaml). Fixed seed. Never uses local frames, and the teacher is never deployed.
Writes data/rdd2022/teacher/{train.txt, val_small.txt, val_full.txt, data.yaml, data_fullval.yaml}.
"""

import argparse
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTS = ROOT / 'data' / 'rdd2022' / 'lists'
OUT = ROOT / 'data' / 'rdd2022' / 'teacher'
COUNTRIES = ['Japan', 'India', 'Czech', 'Norway', 'United_States', 'China_MotorBike']
NAMES = '\n'.join(f'  {i}: {c}' for i, c in enumerate(['D00', 'D10', 'D20', 'D40']))


def read(p):
    return [l for l in p.read_text().splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-country', type=int, default=1000)
    ap.add_argument('--val-per-country', type=int, default=150)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    train, val_small, val_full = [], [], []
    for c in COUNTRIES:
        rng = random.Random(f'42-teacher-{c}')
        tr, va = read(LISTS / f'{c}_train.txt'), read(LISTS / f'{c}_val.txt')
        t = rng.sample(tr, min(a.per_country, len(tr)))
        v = rng.sample(va, min(a.val_per_country, len(va)))
        train += t; val_small += v; val_full += va
        print(f'{c}: train {len(t)} of {len(tr)}, val while training {len(v)} of {len(va)}')
    for name, items in (('train.txt', train), ('val_small.txt', val_small), ('val_full.txt', val_full)):
        (OUT / name).write_text('\n'.join(sorted(items)) + '\n')
    for name, val in (('data.yaml', 'val_small.txt'), ('data_fullval.yaml', 'val_full.txt')):
        (OUT / name).write_text(f'# RDD2022 teacher (six countries, never deployed)\npath: {OUT.as_posix()}\n'
                                f'train: train.txt\nval: {val}\nnc: 4\nnames:\n{NAMES}\n')
    print(f'train {len(train)}, val while training {len(val_small)}, full val {len(val_full)} -> {OUT}')


if __name__ == '__main__':
    main()

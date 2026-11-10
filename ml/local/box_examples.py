"""Box-convention sheet for reviewers: 8 RDD2022 training images (2 per class) with their boxes.

    python ml/local/box_examples.py [--pick Japan_001234,...]

Default choice (fixed seed): per class, images from the pre-resized RDD2022 copy with a single box,
of that class, covering 3-25% of the image and away from the edges; each tile is a close-up around it.
--pick overrides the images (comma-separated stems). Writes data/local/box_examples.jpg (RDD2022,
Arya et al. 2022, CC BY-SA 4.0; kept out of git with the other generated data). The review tool
shows it under "Box examples".
"""

import argparse
import random
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RDD = ROOT / 'data' / 'rdd2022'
OUT = ROOT / 'data' / 'local' / 'box_examples.jpg'
CODES = ['D00', 'D10', 'D20', 'D40']
NAMES = {'D00': 'D00 longitudinal crack: one tight box per continuous crack, along the road',
         'D10': 'D10 transverse crack: one tight box per continuous crack, across the road',
         'D20': 'D20 alligator crack: one box around the whole cracked area',
         'D40': 'D40 pothole: box at the edge of the hole'}
COL = {'D00': (132, 147, 14), 'D10': (6, 119, 217), 'D20': (196, 92, 124), 'D40': (69, 69, 214)}   # app colours, BGR


def labels(stem, country):
    p = RDD / 'labels' / country / f'{stem}.txt'
    return [l.split() for l in p.read_text().splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pick', default='')
    a = ap.parse_args()
    rng = random.Random(42)
    picks = []
    if a.pick:
        for stem in a.pick.split(','):
            country = stem.rsplit('_', 1)[0]
            cls = CODES[int(labels(stem, country)[0][0])]
            picks.append((cls, country, stem))
    else:
        for i, c in enumerate(CODES):
            pool = []
            for lst in sorted((RDD / 'lists').glob('*_train.txt')):
                country = lst.name[:-len('_train.txt')]
                for line in lst.read_text().splitlines():
                    stem = Path(line).stem
                    lb = labels(stem, country)
                    if lb and all(int(x[0]) == i for x in lb) and len(lb) == 1 and 0.03 <= float(lb[0][3]) * float(lb[0][4]) <= 0.25 and 0.2 <= float(lb[0][1]) <= 0.8 and 0.2 <= float(lb[0][2]) <= 0.85:
                        pool.append((c, country, stem))
            rng.shuffle(pool)
            seen = set()
            for p in pool:   # two different countries per class
                if p[1] not in seen:
                    picks.append(p)
                    seen.add(p[1])
                if len(seen) == 2:
                    break
    tiles = []
    for c, country, stem in picks:
        im = cv2.imread(str(RDD / 'images' / country / f'{stem}.jpg'))
        h, w = im.shape[:2]
        for l in labels(stem, country):
            k = CODES[int(l[0])]
            cx, cy, bw, bh = (float(v) for v in l[1:])
            x1, y1, x2, y2 = int((cx - bw / 2) * w), int((cy - bh / 2) * h), int((cx + bw / 2) * w), int((cy + bh / 2) * h)
            t = max(3, w // 200)
            cv2.rectangle(im, (x1, y1), (x2, y2), COL[k], t)
            cv2.putText(im, k, (x1 + 4, max(30, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, w / 700, COL[k], max(2, t - 1))
        # Close-up: the box with as much road again around it, so the convention is visible.
        cx, cy, bw, bh = (float(v) for v in labels(stem, country)[0][1:])
        cw, ch = max(bw * 2.2, 0.35) * w, max(bh * 2.2, 0.35) * h
        l, t_ = int(max(0, cx * w - cw / 2)), int(max(0, cy * h - ch / 2))
        im = im[t_:int(min(h, t_ + ch)), l:int(min(w, l + cw))]
        k = min(640 / im.shape[1], 480 / im.shape[0])
        im = cv2.resize(im, (int(im.shape[1] * k), int(im.shape[0] * k)), interpolation=cv2.INTER_CUBIC)
        im = cv2.copyMakeBorder(im, 0, 0, 0, 640 - im.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255))
        im = cv2.copyMakeBorder(im, 0, max(0, 480 - im.shape[0]), 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))[:480]
        head = np.full((60, 640, 3), 255, np.uint8)
        cv2.putText(head, NAMES[c][:58], (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (30, 30, 30), 1)
        cv2.putText(head, NAMES[c][58:], (8, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (30, 30, 30), 1)
        cv2.putText(head, f'{stem}', (480, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
        tiles.append(np.vstack([head, im]))
    rows = [np.hstack(tiles[i:i + 4]) for i in range(0, 8, 4)]
    foot = np.full((40, rows[0].shape[1], 3), 255, np.uint8)
    cv2.putText(foot, 'Patches and repairs are NOT damage unless they contain an actual pothole or crack.   '
                'Examples: RDD2022 (Arya et al., 2022), CC BY-SA 4.0.', (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (30, 30, 30), 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT), np.vstack(rows + [foot]), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print('picked:', ','.join(p[2] for p in picks), '->', OUT)


if __name__ == '__main__':
    main()

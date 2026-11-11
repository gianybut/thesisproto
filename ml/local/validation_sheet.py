"""Sample sheet for the validator's visual check (replaces the Google Form, which took too long).

    python ml/local/validation_sheet.py [--per-class 10]

From the human-labelled near-zone crops of the train and val splits (data/local/yolo_nz; test is left
out: its labels are frozen), --per-class boxes per damage type drawn at random with the fixed seed,
at most one per frame. Each becomes a numbered tile: the box with road around it, outlined in one
neutral colour. One strip of tiles per class, because the sheet states the class and the validator
confirms it by eye.

Writes data/local/validation_sheet/class_<code>.png, items.csv (item number -> frame, split, box,
class) and counts.json (boxes per class over train + val + test, for the letter). Footage-derived:
gitignored, never pushed. tools/make_validation_letter.js builds the Word file from them.
"""

import argparse
import json
import random

import cv2
import numpy as np

from common import OUT, SEED, write_csv

CODES = ['D00', 'D10', 'D20', 'D40']
YDIR = OUT / 'yolo_nz'
SHEET = OUT / 'validation_sheet'
BOX = (255, 0, 255)          # magenta for every class, as in annotation_sample.py
TW, TH, GAP, COLS = 600, 380, 12, 5


def boxes(split):
    out = []
    for f in sorted((YDIR / 'labels' / split).glob('*.txt')):
        for l in f.read_text().split('\n'):
            p = l.split()
            if len(p) == 5:
                out.append((split, f.stem, int(p[0]), *(float(v) for v in p[1:])))
    return out


def tile(split, stem, cx, cy, w, h, number):
    im = cv2.imread(str(YDIR / 'images' / split / f'{stem}.jpg'))
    H, W = im.shape[:2]
    bw, bh, cx, cy = w * W, h * H, cx * W, cy * H
    cw = max(300, 1.8 * bw, 1.6 * bh * TW / TH)
    ch = min(H, cw * TH / TW)
    cw = min(W, max(1.15 * bw, ch * TW / TH))
    x0 = int(min(max(0, cx - cw / 2), W - cw))
    y0 = int(min(max(0, cy - ch / 2), H - ch))
    crop = im[y0:y0 + int(ch), x0:x0 + int(cw)]
    k = min(TW / crop.shape[1], TH / crop.shape[0])
    crop = cv2.resize(crop, (int(crop.shape[1] * k), int(crop.shape[0] * k)), interpolation=cv2.INTER_CUBIC)
    x1, y1 = int((cx - bw / 2 - x0) * k) - 4, int((cy - bh / 2 - y0) * k) - 4
    x2, y2 = int((cx + bw / 2 - x0) * k) + 4, int((cy + bh / 2 - y0) * k) + 4
    cv2.rectangle(crop, (x1, y1), (x2, y2), (255, 255, 255), 4)
    cv2.rectangle(crop, (x1, y1), (x2, y2), BOX, 2)
    t = np.full((TH, TW, 3), 255, np.uint8)
    oy, ox = (TH - crop.shape[0]) // 2, (TW - crop.shape[1]) // 2
    t[oy:oy + crop.shape[0], ox:ox + crop.shape[1]] = crop
    label = str(number)
    (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 4)
    cv2.rectangle(t, (0, 0), (lw + 24, lh + 26), (255, 255, 255), -1)
    cv2.rectangle(t, (0, 0), (lw + 24, lh + 26), (0, 0, 0), 2)
    cv2.putText(t, label, (12, lh + 12), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.rectangle(t, (0, 0), (TW - 1, TH - 1), (120, 120, 120), 1)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-class', type=int, default=10)
    a = ap.parse_args()
    pool = boxes('train') + boxes('val')
    counts = {c: 0 for c in CODES}
    for b in pool + boxes('test'):
        counts[CODES[b[2]]] += 1
    frames = sum(len(list((YDIR / 'labels' / s).glob('*.txt'))) for s in ('train', 'val', 'test'))
    rng = random.Random(SEED)
    SHEET.mkdir(parents=True, exist_ok=True)
    rows, number = [], 0
    for ci, code in enumerate(CODES):
        cand = [b for b in pool if b[2] == ci]
        rng.shuffle(cand)
        seen, chosen = set(), []
        for b in cand:
            if b[1] not in seen:
                seen.add(b[1])
                chosen.append(b)
            if len(chosen) == a.per_class:
                break
        tiles = []
        for split, stem, _, cx, cy, w, h in chosen:
            number += 1
            tiles.append(tile(split, stem, cx, cy, w, h, number))
            rows.append({'item': number, 'class': code, 'split': split, 'frame': f'{stem}.jpg',
                         'cx': cx, 'cy': cy, 'w': w, 'h': h})
        n_rows = -(-len(tiles) // COLS)
        strip = np.full((n_rows * TH + (n_rows - 1) * GAP, COLS * TW + (COLS - 1) * GAP, 3), 255, np.uint8)
        for i, t in enumerate(tiles):
            r, c = divmod(i, COLS)
            strip[r * (TH + GAP):r * (TH + GAP) + TH, c * (TW + GAP):c * (TW + GAP) + TW] = t
        cv2.imwrite(str(SHEET / f'class_{code}.png'), strip)
        print(code, len(cand), 'boxes in train+val,', len(tiles), 'shown', strip.shape[1], 'x', strip.shape[0])
    write_csv(SHEET / 'items.csv', rows, list(rows[0]))
    (SHEET / 'counts.json').write_text(json.dumps({'frames': frames, 'boxes': counts, 'shown': a.per_class}, indent=1))
    print('frames', frames, 'boxes', counts, '->', SHEET)


if __name__ == '__main__':
    main()

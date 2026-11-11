"""Sample sheet for the validator's visual check (replaces the Google Form, which took too long).

    python ml/local/validation_sheet.py [--per-class 10]             random pick (fixed seed)
    python ml/local/validation_sheet.py --selection selection.json   the team's own pick
    python tools/validation_picker.py                                choose the pictures in the browser

Boxes come from the human-labelled near-zone crops of the train and val splits (data/local/yolo_nz;
test is left out: its labels are frozen). A box is named "<split>/<frame stem>/<line in its label
file>". Each chosen box becomes a numbered tile: the box with road around it, outlined in one neutral
colour. One strip of tiles per class, because the sheet states the class and the validator confirms
it by eye.

Writes data/local/validation_sheet/class_<code>.png, items.csv (item number -> box, class) and
counts.json (boxes per class over train + val + test, and whether the pick was random or by hand:
the letter says which). Footage-derived: gitignored, never pushed. tools/make_validation_letter.js
builds the Word file from them.
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
        for i, l in enumerate(f.read_text().split('\n')):
            p = l.split()
            if len(p) == 5:
                out.append({'id': f'{split}/{f.stem}/{i}', 'split': split, 'stem': f.stem, 'cls': int(p[0]),
                            'cx': float(p[1]), 'cy': float(p[2]), 'w': float(p[3]), 'h': float(p[4])})
    return out


def pool():
    """Every box the sample may come from: train, then val."""
    return boxes('train') + boxes('val')


def tile(b, number=None):
    im = cv2.imread(str(YDIR / 'images' / b['split'] / f"{b['stem']}.jpg"))
    H, W = im.shape[:2]
    bw, bh, cx, cy = b['w'] * W, b['h'] * H, b['cx'] * W, b['cy'] * H
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
    if number is not None:
        label = str(number)
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 4)
        cv2.rectangle(t, (0, 0), (lw + 24, lh + 26), (255, 255, 255), -1)
        cv2.rectangle(t, (0, 0), (lw + 24, lh + 26), (0, 0, 0), 2)
        cv2.putText(t, label, (12, lh + 12), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.rectangle(t, (0, 0), (TW - 1, TH - 1), (120, 120, 120), 1)
    return t


def random_pick(all_boxes, per_class):
    """per_class boxes per class at random (fixed seed), at most one per frame."""
    rng = random.Random(SEED)
    chosen = {}
    for ci, code in enumerate(CODES):
        cand = [b for b in all_boxes if b['cls'] == ci]
        rng.shuffle(cand)
        seen, chosen[code] = set(), []
        for b in cand:
            if b['stem'] not in seen:
                seen.add(b['stem'])
                chosen[code].append(b)
            if len(chosen[code]) == per_class:
                break
    return chosen


def build(chosen, picked):
    """chosen: {code: [box, ...]} in sheet order. picked: 'random' or 'by_hand'."""
    per_class = {len(v) for v in chosen.values()}
    if len(per_class) != 1:
        raise ValueError('every damage type needs the same number of pictures')
    counts = {c: 0 for c in CODES}
    for b in pool() + boxes('test'):
        counts[CODES[b['cls']]] += 1
    frames = sum(len(list((YDIR / 'labels' / s).glob('*.txt'))) for s in ('train', 'val', 'test'))
    SHEET.mkdir(parents=True, exist_ok=True)
    rows, number = [], 0
    for code in CODES:
        tiles = []
        for b in chosen[code]:
            number += 1
            tiles.append(tile(b, number))
            rows.append({'item': number, 'class': code, 'id': b['id'], 'split': b['split'], 'frame': f"{b['stem']}.jpg",
                         'cx': b['cx'], 'cy': b['cy'], 'w': b['w'], 'h': b['h']})
        n_rows = -(-len(tiles) // COLS)
        strip = np.full((n_rows * TH + (n_rows - 1) * GAP, COLS * TW + (COLS - 1) * GAP, 3), 255, np.uint8)
        for i, t in enumerate(tiles):
            r, c = divmod(i, COLS)
            strip[r * (TH + GAP):r * (TH + GAP) + TH, c * (TW + GAP):c * (TW + GAP) + TW] = t
        cv2.imwrite(str(SHEET / f'class_{code}.png'), strip)
    write_csv(SHEET / 'items.csv', rows, list(rows[0]))
    (SHEET / 'counts.json').write_text(json.dumps(
        {'frames': frames, 'boxes': counts, 'shown': per_class.pop(), 'picked': picked}, indent=1))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-class', type=int, default=10)
    ap.add_argument('--selection', help='JSON {"D00": [box ids], ...}: the team\'s own pick, in sheet order')
    a = ap.parse_args()
    all_boxes = pool()
    if a.selection:
        by_id = {b['id']: b for b in all_boxes}
        sel = json.loads(open(a.selection, encoding='utf-8').read())
        chosen = {c: [by_id[i] for i in sel[c]] for c in CODES}
        bad = [i for c in CODES for i in sel[c] if CODES[by_id[i]['cls']] != c]
        if bad:
            raise SystemExit(f'boxes filed under another class: {bad}')
        rows = build(chosen, 'by_hand')
    else:
        rows = build(random_pick(all_boxes, a.per_class), 'random')
    print(len(rows), 'items ->', SHEET)


if __name__ == '__main__':
    main()

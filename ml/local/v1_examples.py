"""Step 6: example val predictions of v1 (4 good frames, 4 D20 failures), at the deployed threshold.

    python ml/local/v1_examples.py [--run v1] [--thr 0.24]

Reads the app-style predictions cached by eval_val_sets.py (runs/eval/valsets/<run>.json) and the
near-zone val labels. Good = most correct boxes with no false alarm or miss (ties: higher confidence);
D20 failure = a labelled D20 box the model missed or called another class. Labels are drawn as thin
white boxes, predictions in the class colour (correct: solid, wrong: with an X). Writes
results/v1_examples/*.jpg (footage-derived: gitignored) and results/v1_examples.md. Seed 0.
"""

import argparse
import json
import random

import cv2
import numpy as np

from common import ROOT
from eval_val_sets import CACHE, CODES, SETS, YDIR, frames, gts, iou_matrix

COL = {0: (213, 94, 0), 1: (0, 158, 115), 2: (0, 114, 178), 3: (204, 121, 167)}   # BGR, colour-blind safe


def assess(pred, gt, thr):
    p = [q for q in pred if q[5] >= thr]
    hit_p, hit_g, wrong_cls = set(), set(), set()
    if p and gt:
        iou = iou_matrix([q[1:5] for q in p], [g[1:] for g in gt])
        for i, j in sorted(np.argwhere(iou >= 0.5).tolist(), key=lambda ij: -iou[ij[0], ij[1]]):
            if i in hit_p or j in hit_g:
                continue
            if p[i][0] == gt[j][0]:
                hit_p.add(i), hit_g.add(j)
        for j, g in enumerate(gt):
            if j not in hit_g and any(iou[i, j] >= 0.5 and p[i][0] != g[0] for i in range(len(p))):
                wrong_cls.add(j)
    return p, hit_p, hit_g, wrong_cls


def draw(stem, d, thr, out):
    img = cv2.imread(str(next(YDIR.glob(f'images/val/{stem}.*'))))
    gt = gts(stem, *d['wh'])
    p, hit_p, hit_g, _ = assess(d['pred'], gt, thr)
    for c, x1, y1, x2, y2 in gt:
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 255), 1)
        cv2.putText(img, f'label {CODES[c]}', (int(x1), int(y2) + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    for i, (c, x1, y1, x2, y2, s) in enumerate(p):
        pt1, pt2 = (int(x1), int(y1)), (int(x2), int(y2))
        cv2.rectangle(img, pt1, pt2, COL[c], 3)
        if i not in hit_p:
            cv2.line(img, pt1, pt2, COL[c], 1), cv2.line(img, (pt1[0], pt2[1]), (pt2[0], pt1[1]), COL[c], 1)
        cv2.putText(img, f'{CODES[c]} {s:.2f}', (pt1[0], max(12, pt1[1] - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COL[c], 2)
    cv2.imwrite(str(out), img, [cv2.IMWRITE_JPEG_QUALITY, 85])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', default='v1')
    ap.add_argument('--thr', type=float)
    a = ap.parse_args()
    thr = a.thr or json.loads((ROOT / 'results' / 'threshold_calibration.json').read_text())['threshold']
    det = json.loads((CACHE / f'{a.run}.json').read_text())
    reviewed = set(frames(SETS['reviewed']))
    random.seed(0)
    good, d20 = [], []
    for s in frames(SETS['full']):
        gt = gts(s, *det[s]['wh'])
        p, hit_p, hit_g, wrong = assess(det[s]['pred'], gt, thr)
        if gt and len(hit_g) == len(gt) and len(hit_p) == len(p):
            good.append((len(hit_g), sum(p[i][5] for i in hit_p), s))
        miss20 = [j for j, g in enumerate(gt) if g[0] == 2 and j not in hit_g]
        if miss20:
            d20.append((s, len(miss20), sum(1 for j in miss20 if j in wrong)))
    good.sort(reverse=True)
    pick_good = [s for *_, s in good[:4]]
    pick_d20 = random.sample(d20, min(4, len(d20)))
    out = ROOT / 'results' / 'v1_examples'
    out.mkdir(exist_ok=True)
    md = [f'# Example val predictions of {a.run} (threshold {thr:.2f}, app-style input)', '',
          'White thin box = label; thick box = prediction in its class colour; X = a prediction with no matching '
          'label of its class (false alarm). Images in `results/v1_examples/` (gitignored: footage).', '',
          f'Frames where every label was found with no false alarm: {len(good)} of 1,624. '
          f'Frames with a missed D20 label: {len(d20)} (of the 51 D20 boxes, '
          f'{sum(n for _, n, _ in d20)} missed; {sum(w for *_, w in d20)} of those found as another class).', '',
          '| Image | Frame | Set | Kind |', '|---|---|---|---|']
    for k, s in enumerate(pick_good, 1):
        draw(s, det[s], thr, out / f'good_{k}.jpg')
        md.append(f'| good_{k}.jpg | {s} | {"reviewed" if s in reviewed else "site"} | all labels found |')
    for k, (s, n, w) in enumerate(pick_d20, 1):
        draw(s, det[s], thr, out / f'd20_fail_{k}.jpg')
        md.append(f'| d20_fail_{k}.jpg | {s} | {"reviewed" if s in reviewed else "site"} | '
                  f'{n} D20 missed{f", {w} called another class" if w else ""} |')
    (ROOT / 'results' / 'v1_examples.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

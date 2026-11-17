"""Second-stage classifier vs the fusion's own class, on VALIDATION only (never test).

    python ml/local/classifier_val_compare.py [--device cpu]

Metrics: results/classifier_metric_definitions.md (written before this script was first run).

On the 270 reviewed val frames (data/local/yolo_nz/val_reviewed.txt, 122 boxes):
  1. The deployed fusion (model_config.json: members, sizes, grey border, weighted box fusion,
     threshold) detects, exactly as test_eval_nz.py scores it.
  2. Detections are matched one-to-one to reviewed boxes at IoU >= 0.5, any class (label_quality.match).
  3. For every matched detection: the fusion's class, and the class the classifier gives to the
     detection's box cut from the frame exactly as the app does (backend/services/damage_classifier.
     classify_crop: no padding, imgsz and threshold from model_config.json "classifier").
  4. Classification accuracy of each on the same matched detections, Wilson 95% intervals, the 4 x 4
     tables, and an exact McNemar test on the detections where exactly one of the two is right.
  5. For reference, the classifier's top-1 accuracy on the 122 reviewed boxes themselves, cut as its
     training crops were (25% padding, ml/build_classifier_dataset.py): this is the number Ultralytics
     reported while training (0.820), and the classifier's best epoch was picked on it.

The classifier's own settings are read even when it is disabled; the fusion is always the deployed one.
Writes results/classifier_val_compare.md and .json. Refuses any frame list other than val_reviewed.txt.
"""

import argparse
import json
import math
import sys
from datetime import datetime

import calibrate_threshold as cal
from common import OUT, ROOT
from label_quality import match

sys.path.insert(0, str(ROOT / 'backend'))
from services.damage_classifier import classify_crop  # noqa: E402

YDIR = OUT / 'yolo_nz'
LIST = 'val_reviewed.txt'
CODES = ['D00', 'D10', 'D20', 'D40']
CONFIG = ROOT / 'ml' / 'models' / 'model_config.json'
REPORT = ROOT / 'results' / 'classifier_val_compare.md'


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar_exact(b, c):
    """Two-sided exact binomial test on the discordant counts b (only A right) and c (only B right)."""
    n = b + c
    if not n:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def table_md(t):
    rows = ['| Reviewed \\ Given | ' + ' | '.join(CODES) + ' |', '|---|' + '---|' * 4]
    rows += [f'| {CODES[i]} | ' + ' | '.join(str(x) for x in t[i]) + ' |' for i in range(4)]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', default='0')
    a = ap.parse_args()
    import cv2
    from ultralytics import YOLO

    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
    settings = dict(cfg.get('classifier') or {})
    if not settings.get('weights'):
        sys.exit('model_config.json has no "classifier" weights.')
    members = [(ROOT / cfg['weights'], int(cfg['imgsz']))] + [(ROOT / m['weights'], int(m['imgsz'])) for m in cfg.get('ensemble') or []]
    thr, border = float(cfg['conf_threshold']), int(cfg.get('border_px') or 0)
    clf = YOLO(str(ROOT / settings['weights']))

    frames = cal.frames_of('val', ydir=YDIR, list_name=LIST)
    if len(frames) != 270:
        sys.exit(f'{LIST} has {len(frames)} frames, expected 270.')
    det = cal.predict_fused(members, frames, a.device, border) if len(members) > 1 else \
        cal.predict(members[0][0], frames, a.device, members[0][1], border)

    t_fus = [[0] * 4 for _ in range(4)]
    t_clf = [[0] * 4 for _ in range(4)]
    both = only_fus = only_clf = neither = unusable = 0
    rows = []
    gt_right = gt_n = 0
    for img, gts in frames:
        im = cv2.imread(str(img))
        h, w = im.shape[:2]
        preds = [d for d in det[img] if d['conf'] >= thr]
        for i, j in match(preds, gts, cal.MATCH_IOU, same_class=False).items():
            g, p = gts[j]['cls'], preds[i]['cls']
            res = classify_crop(clf, im, preds[i]['box'], settings)
            if res is None:
                unusable += 1
                continue
            c = CODES.index(res[0])
            t_fus[g][p] += 1
            t_clf[g][c] += 1
            fr, cr = p == g, c == g
            both += fr and cr
            only_fus += fr and not cr
            only_clf += cr and not fr
            neither += not fr and not cr
            rows.append(dict(frame=img.stem, reviewed=CODES[g], fusion=CODES[p], classifier=CODES[c],
                             classifier_conf=round(res[2], 4), det_conf=round(preds[i]['conf'], 4)))
        for gt in gts:   # reference: the reviewed boxes cut like the training crops (25% padding)
            x1, y1, x2, y2 = gt['box']
            bw, bh = x2 - x1, y2 - y1
            crop = im[max(0, int(y1 - .25 * bh)):min(h, int(y2 + .25 * bh)), max(0, int(x1 - .25 * bw)):min(w, int(x2 + .25 * bw))]
            r = clf(crop, verbose=False, imgsz=int(settings.get('imgsz', 224)))[0]
            gt_n += 1
            gt_right += clf.names[int(r.probs.top1)] == CODES[gt['cls']]

    n = both + only_fus + only_clf + neither
    acc_f, acc_c = (both + only_fus) / n if n else 0, (both + only_clf) / n if n else 0
    p_mc = mcnemar_exact(only_fus, only_clf)
    res = dict(when=datetime.now().isoformat(timespec='seconds'), frames=len(frames), threshold=thr, matched=n,
               unusable_crops=unusable, fusion_correct=both + only_fus, classifier_correct=both + only_clf,
               only_fusion_right=only_fus, only_classifier_right=only_clf, both_right=both, neither_right=neither,
               fusion_accuracy=acc_f, classifier_accuracy=acc_c, fusion_ci=wilson(both + only_fus, n),
               classifier_ci=wilson(both + only_clf, n), mcnemar_p=p_mc, table_fusion=t_fus, table_classifier=t_clf,
               reviewed_box_top1=gt_right / gt_n if gt_n else None, reviewed_boxes=gt_n,
               classifier_weights=settings['weights'], classifier_enabled=bool(settings.get('enabled')), pairs=rows)
    REPORT.with_suffix('.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
    lf, hf = res['fusion_ci']
    lc, hc = res['classifier_ci']
    md = ['# Second-stage classifier vs the fusion\'s class (validation only)', '',
          f'`ml/local/classifier_val_compare.py`, {res["when"]}. Metrics fixed in `results/classifier_metric_definitions.md`. '
          f'The test set was not used.', '',
          f'270 reviewed val frames; deployed fusion at threshold {thr}; {n} detections matched to a reviewed box at IoU >= 0.5 '
          f'(any class){f"; {unusable} crops the classifier could not label" if unusable else ""}.', '',
          '| Class decision on the same matched detections | Correct | Accuracy | 95% CI |', '|---|---|---|---|',
          f'| Fusion (deployed, as test-evaluated) | {both + only_fus} / {n} | {100 * acc_f:.1f}% | {100 * lf:.1f}% to {100 * hf:.1f}% |',
          f'| Second-stage classifier (as the app applies it) | {both + only_clf} / {n} | {100 * acc_c:.1f}% | {100 * lc:.1f}% to {100 * hc:.1f}% |', '',
          f'Both right {both}, only the fusion right {only_fus}, only the classifier right {only_clf}, neither {neither}; '
          f'exact McNemar p = {p_mc:.3f}.', '', 'Fusion:', ''] + table_md(t_fus) + ['', 'Classifier:', ''] + table_md(t_clf) + \
         ['', f'Reference: classifier top-1 on the {gt_n} reviewed boxes cut like its training crops (25% padding): '
          f'{100 * res["reviewed_box_top1"]:.1f}%. Its best epoch was chosen on these boxes, so this figure is optimistic.']
    REPORT.write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

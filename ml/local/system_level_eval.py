"""System-level (frame-level) evaluation of the deployed pipeline and pretrained comparators.

    python ml/local/system_level_eval.py [--device 0]

Adopted 2026-11-15 per adviser consultation (docs/decisions.md). Nothing here changes the deployed
model, its fusion, threshold or band; nothing here is used to select a model. Reads:

- data/local/yolo_nz/test.txt (270 near-zone test frames, 63 with damage, 99 reviewed boxes) and
  val_reviewed.txt (270 reviewed val frames; used only to pick each COMPARATOR's threshold).
- the deployed configuration, ml/models/model_config.json: v2b (1024) + v3 (1280) + S5_v8m_1920 (1280),
  each member at conf 0.05, NMS IoU 0.45, grey border 24 px, weighted box fusion
  (backend/services/box_fusion.py), fused score >= 0.25. Since 2026-11-12 the config also enables a
  second-stage classifier (ml/models/classifier.pt) that relabels every box (backend
  video_processor.py / damage_classifier.py); it is scored as a second row.

Definitions (also written into the report):

A. Damage present. A frame is positive if it has >= 1 reviewed box; predicted positive if it has >= 1
   detection at the threshold. TP/FP/FN/TN over the 270 frames.
B. Damage present with the correct type. Reviewed-positive frame: TP if some detection "hits" a reviewed
   box of the same class (the detection's centre inside the reviewed box, or IoU >= 0.25), else FN.
   Reviewed-negative frame: FP if it has any detection, else TN.
C. Per class c: as B restricted to class c (positive = has a reviewed c box; TP = a c detection hits a
   c box; FP = a frame with no reviewed c box but a c detection). The presence-only variant (no hit
   required) is given too.
Accuracy = (TP+TN)/N, precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2PR/(P+R). 95% Wilson
intervals for accuracy, precision and recall; F1 has no Wilson interval, so a frame-level bootstrap
percentile interval (10,000 resamples, seed 42) is given.

Comparators (teacher, SreekarAditya YOLOv8s / YOLOv12s seed 0, the 7-class stand-in) run with the same
app settings (imgsz 1280 = INFERENCE_IMGSZ, NMS IoU 0.45, border 24, conf floor 0.01); classes mapped
as the backend maps them (DAMAGE_CLASS_MAP substrings; unmapped classes dropped). Each comparator's
threshold = the one in 0.01..0.99 that maximises definition-A F1 on the 270 reviewed val frames
(ties: the higher threshold).

Raw detections are cached in data/local/system_eval/ (gitignored). Writes
results/system_level_evaluation.json; the markdown report is written by hand from it.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

import calibrate_threshold as cal
from common import OUT, ROOT
from label_quality import match

sys.path.insert(0, str(ROOT / 'backend' / 'services'))
from box_fusion import fuse  # noqa: E402

YDIR = OUT / 'yolo_nz'
CACHE = OUT / 'system_eval'
CODES = cal.CODES
BORDER = 24
NMS_IOU = 0.45
MEMBER_CONF = 0.05
DEPLOYED_THR = 0.25
HIT_IOU = 0.25
SWEEP = [round(0.01 * i, 2) for i in range(1, 100)]
NAME_MAP = {'d00': 0, 'd10': 1, 'd20': 2, 'd40': 3, 'longitudinal': 0, 'transverse': 1, 'lateral': 1,
            'alligator': 2, 'crocodile': 2, 'pothole': 3}   # backend video_processor.DAMAGE_CLASS_MAP
SA = 'SreekarAditya__yolo-rdd2022-benchmark/yolo-rdd2022-benchmark'
COMPARATORS = [
    ('Teacher (ours, RDD2022 only, YOLOv8m)', 'runs/teacher/teacher/weights/best.pt'),
    ('SreekarAditya YOLOv8s RDD2022 (seed 0)', f'ml/models/pretrained/{SA}/yolov8s_seed0_best.pt'),
    ('SreekarAditya YOLOv12s RDD2022 (seed 0)', f'data/pretrained/{SA}/yolo12s_seed0_best.pt'),
    ('Stand-in (external 7-class YOLOv8n RDD2022)', 'ml/models/rdd2022_pretrained.pt'),
]


def map_name(name):
    n = name.lower()
    for k, c in NAME_MAP.items():
        if k in n:
            return c
    return None


def predict_any(weights, frames, device, imgsz, conf):
    """{stem: [{'cls','box','conf'}]} with the app's border and NMS, classes mapped by name."""
    import cv2
    from ultralytics import YOLO
    model = YOLO(str(ROOT / weights))
    cmap = {i: map_name(n) for i, n in model.names.items()}
    out = {}
    for img, _ in frames:
        src = cv2.copyMakeBorder(cv2.imread(str(img)), BORDER, BORDER, 0, 0, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        r = model.predict(src, imgsz=imgsz, conf=conf, iou=NMS_IOU, device=device, verbose=False)[0]
        h = r.orig_shape[0] - 2 * BORDER
        dets = []
        for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
            m = cmap.get(int(c))
            if m is None:
                continue
            y1, y2 = min(max(b[1] - BORDER, 0), h), min(max(b[3] - BORDER, 0), h)
            if y2 - y1 >= 2:
                dets.append({'cls': m, 'box': (float(b[0]), float(y1), float(b[2]), float(y2)), 'conf': float(s)})
        out[img.stem] = dets
    return out


def deployed_fused(frames, device):
    cfg = json.loads((ROOT / 'ml' / 'models' / 'model_config.json').read_text(encoding='utf-8'))
    members = [(cfg['weights'], cfg['imgsz'])] + [(m['weights'], m['imgsz']) for m in cfg['ensemble']]
    assert cfg['conf_threshold'] == DEPLOYED_THR and cfg['border_px'] == BORDER and cfg['iou_threshold'] == NMS_IOU
    per = [predict_any(w, frames, device, sz, MEMBER_CONF) for w, sz in members]
    out = {}
    for img, _ in frames:
        f = fuse([[(d['cls'], *d['box'], d['conf']) for d in p[img.stem]] for p in per])
        out[img.stem] = [{'cls': int(x[0]), 'box': tuple(map(float, x[1:5])), 'conf': float(x[5])} for x in f]
    return out, members


def classify(frames, det, device, thr):
    """The deployed second stage, as backend damage_classifier.classify_crop: the detector box cropped
    (no padding) at imgsz 224, top-1 class replaces the detector's class (conf_threshold 0.0)."""
    import cv2
    from ultralytics import YOLO
    cfg = json.loads((ROOT / 'ml' / 'models' / 'model_config.json').read_text(encoding='utf-8'))['classifier']
    model = YOLO(str(ROOT / cfg['weights']))
    assert [model.names[i] for i in range(4)] == CODES
    out = {}
    for img, _ in frames:
        im = cv2.imread(str(img))
        H, W = im.shape[:2]
        dets = []
        for d in det[img.stem]:
            if d['conf'] < thr:
                continue
            x1, y1, x2, y2 = (int(round(v)) for v in d['box'])
            x1, x2 = max(0, min(x1, W - 1)), max(0, min(x2, W))
            y1, y2 = max(0, min(y1, H - 1)), max(0, min(y2, H))
            c = d['cls']
            if x2 > x1 and y2 > y1:
                r = model(im[y1:y2, x1:x2], verbose=False, imgsz=int(cfg.get('imgsz', 224)), device=device)[0]
                if r.probs is not None and float(r.probs.top1conf) >= float(cfg.get('conf_threshold', 0.0)):
                    c = int(r.probs.top1)
            dets.append({**d, 'cls': c})
        out[img.stem] = dets
    return out


def classifier_heldout(device):
    """Top-1 accuracy of the deployed classifier on the held-out test crops (reviewed boxes of test.txt,
    padding 0.25, as built by ml/build_classifier_dataset.py)."""
    from ultralytics import YOLO
    cfg = json.loads((ROOT / 'ml' / 'models' / 'model_config.json').read_text(encoding='utf-8'))['classifier']
    model = YOLO(str(ROOT / cfg['weights']))
    cm = [[0] * 4 for _ in range(4)]
    base = OUT / 'classification' / 'test'
    for t, code in enumerate(CODES):
        for p in sorted((base / code).glob('*.jpg')):
            r = model(str(p), verbose=False, imgsz=int(cfg.get('imgsz', 224)), device=device)[0]
            cm[t][int(r.probs.top1)] += 1
    return cm


# ---------- metrics ----------

def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0.0


def hits(d, g):
    cx, cy = (d['box'][0] + d['box'][2]) / 2, (d['box'][1] + d['box'][3]) / 2
    b = g['box']
    return (b[0] <= cx <= b[2] and b[1] <= cy <= b[3]) or iou(d['box'], b) >= HIT_IOU


def outcomes(frames, det, thr, mode, cls=None):
    """Per-frame outcome code: 'TP','FP','FN','TN'."""
    res = []
    for img, gts in frames:
        preds = [d for d in det[img.stem] if d['conf'] >= thr]
        if cls is not None:
            gts = [g for g in gts if g['cls'] == cls]
            preds = [d for d in preds if d['cls'] == cls]
        pos = bool(gts)
        if mode == 'present':
            ok = bool(preds)
        else:   # 'typed': a detection of the same class hits a reviewed box
            ok = any(d['cls'] == g['cls'] and hits(d, g) for d in preds for g in gts)
        if pos:
            res.append('TP' if ok else 'FN')
        else:
            res.append('FP' if preds else 'TN')
    return res


def summarise(oc, boot=True):
    oc = np.array(oc)
    tp, fp, fn, tn = (int((oc == k).sum()) for k in ('TP', 'FP', 'FN', 'TN'))
    n = len(oc)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    out = {'n': n, 'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn, 'acc': (tp + tn) / n, 'p': p, 'r': r, 'f1': f1,
           'acc_ci': wilson(tp + tn, n), 'p_ci': wilson(tp, tp + fp), 'r_ci': wilson(tp, tp + fn)}
    if boot:
        rng = np.random.default_rng(42)
        idx = rng.integers(0, n, size=(10000, n))
        s = oc[idx]
        T, F, N = (s == 'TP').sum(1), (s == 'FP').sum(1), (s == 'FN').sum(1)
        with np.errstate(divide='ignore', invalid='ignore'):
            f = np.where(2 * T + F + N > 0, 2 * T / (2 * T + F + N), 0.0)
        out['f1_ci'] = [float(np.percentile(f, 2.5)), float(np.percentile(f, 97.5))]
    return out


def full(frames, det, thr):
    return {
        'present': summarise(outcomes(frames, det, thr, 'present')),
        'typed': summarise(outcomes(frames, det, thr, 'typed')),
        'per_class_typed': {CODES[c]: summarise(outcomes(frames, det, thr, 'typed', c)) for c in range(4)},
        'per_class_present': {CODES[c]: summarise(outcomes(frames, det, thr, 'present', c)) for c in range(4)},
        'detections': sum(1 for img, _ in frames for d in det[img.stem] if d['conf'] >= thr),
    }


def box_check(frames, det, thr):
    """Box-level numbers of results/test_evaluation.md (same-class P/R and class accuracy), to confirm
    that this re-run reproduces the frozen test run."""
    fr = [(Path(img), gts) for img, gts in frames]
    d2 = {img: det[img.stem] for img, _ in fr}
    ov = cal.table(fr, d2, thr)[-1]
    cm = [[0] * 4 for _ in range(4)]
    for img, gts in fr:
        preds = [d for d in d2[img] if d['conf'] >= thr]
        for i, j in match(preds, gts, 0.5, same_class=False).items():
            cm[gts[j]['cls']][preds[i]['cls']] += 1
    right, n = sum(cm[c][c] for c in range(4)), sum(map(sum, cm))
    return {'boxes': ov[1], 'tp': ov[2], 'fp': ov[3], 'fn': ov[4], 'cls_correct': right, 'cls_matched': n,
            'cls_acc': right / n if n else 0.0, 'cls_ci': wilson(right, n), 'cls_table': cm}


def cached(name, fn):
    p = CACHE / f'{name}.json'
    if p.exists():
        return json.loads(p.read_text())
    d = fn()
    CACHE.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d))
    return d


def val_all(device):
    """The deployed system on all 1,624 val frames (val.txt: 270 reviewed + 1,354 annotation-site frames), for
    Table 5.1.4 next to the box-level figures of results/test_evaluation.md. Val only; nothing is selected on it."""
    val = cal.frames_of('val', ydir=YDIR, list_name='val.txt')
    fus = cached('fusion_valall', lambda: deployed_fused(val, device)[0])
    cls = cached('fusion_cls_valall', lambda: classify(val, fus, device, DEPLOYED_THR))
    out = {'n': len(val), 'pos': sum(1 for _, g in val if g),
           'fusion': full(val, fus, DEPLOYED_THR), 'fusion_cls': full(val, cls, DEPLOYED_THR)}
    p = ROOT / 'results' / 'system_level_evaluation.json'
    d = json.loads(p.read_text())
    d['val_all_1624'] = out
    p.write_text(json.dumps(d, indent=1))
    for k in ('fusion', 'fusion_cls'):
        for m in ('present', 'typed'):
            r = out[k][m]
            print(k, m, r['tp'], r['fp'], r['fn'], r['tn'], *(round(r[x], 3) for x in ('acc', 'p', 'r', 'f1')))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', default='0')
    ap.add_argument('--val-all', action='store_true',
                    help='only add the deployed system on all 1,624 val frames (val.txt) to the JSON')
    a = ap.parse_args()
    if a.val_all:
        return val_all(a.device)
    test = cal.frames_of('test', ydir=YDIR, list_name='test.txt')
    val = cal.frames_of('val', ydir=YDIR, list_name='val_reviewed.txt')
    res = {'n_test': len(test), 'test_pos': sum(1 for _, g in test if g), 'n_val': len(val),
           'val_pos': sum(1 for _, g in val if g),
           'test_boxes_per_class': [sum(1 for _, g in test for b in g if b['cls'] == c) for c in range(4)],
           'test_frames_per_class': [sum(1 for _, g in test if any(b['cls'] == c for b in g)) for c in range(4)]}

    # Deployed fusion (as test-evaluated on 2026-11-11) and fusion + classifier (deployed since 2026-11-12)
    fus_t = cached('fusion_test', lambda: deployed_fused(test, a.device)[0])
    fus_v = cached('fusion_val', lambda: deployed_fused(val, a.device)[0])
    cls_t = cached('fusion_cls_test', lambda: classify(test, fus_t, a.device, DEPLOYED_THR))
    cls_v = cached('fusion_cls_val', lambda: classify(val, fus_v, a.device, DEPLOYED_THR))
    res['fusion'] = {'threshold': DEPLOYED_THR, 'test': full(test, fus_t, DEPLOYED_THR),
                     'val': full(val, fus_v, DEPLOYED_THR), 'box_check_test': box_check(test, fus_t, DEPLOYED_THR)}
    res['fusion_cls'] = {'threshold': DEPLOYED_THR, 'test': full(test, cls_t, DEPLOYED_THR),
                         'val': full(val, cls_v, DEPLOYED_THR), 'box_check_test': box_check(test, cls_t, DEPLOYED_THR)}
    res['classifier_heldout_test_cm'] = classifier_heldout(a.device)

    res['comparators'] = []
    for title, w in COMPARATORS:
        key = Path(w).stem.replace('.', '_') + '_' + Path(w).parent.parent.name
        pv = cached(f'{key}_val', lambda: predict_any(w, val, a.device, 1280, 0.01))
        pt = cached(f'{key}_test', lambda: predict_any(w, test, a.device, 1280, 0.01))
        best = max(SWEEP, key=lambda t: (summarise(outcomes(val, pv, t, 'present'), boot=False)['f1'], t))
        res['comparators'].append({'title': title, 'weights': w, 'threshold': best,
                                   'val': full(val, pv, best), 'test': full(test, pt, best)})
        print(title, best, res['comparators'][-1]['test']['present']['f1'])

    (ROOT / 'results' / 'system_level_evaluation.json').write_text(json.dumps(res, indent=1))
    f = res['fusion']['test']
    print('fusion test present', f['present'])
    print('fusion test typed', f['typed'])
    print('box check', res['fusion']['box_check_test'])


if __name__ == '__main__':
    main()

"""Step 6 (final freeze, 2026-11-11): every candidate model on the NEW near-zone val sets.

    python ml/local/eval_val_sets.py                 # v1, A, B v2, S5_v8m_1280, the placeholder
    python ml/local/eval_val_sets.py --only v1       # one model (cached predictions are reused)

One prediction pass per model over all val frames of data/local/yolo_nz (val.txt = 1,624 near-zone
crops), at the model's own training size (the placeholder at the app's 1280), conf 0.001, NMS IoU 0.7
(Ultralytics' validation settings), then mAP@50 and mAP@50-95 per class with Ultralytics' own
ap_per_class and its matching rule, on three sets:

    reviewed  val_reviewed.txt  the 270 single-reviewer frames (the set runs A/B/S5 were chosen on)
    new       val_new.txt       the 1,354 annotation-site frames (labels frozen in labels_FINAL_...db)
    full      val.txt           both (the set v1's best.pt was chosen on)

The placeholder (rdd2022_pretrained.pt, 7 classes) is mapped as the app maps it
(video_processor.DAMAGE_CLASS_MAP: longitudinal D00, transverse D10, alligator D20, pothole D40;
block, crack and edge are dropped, as _is_pothole_class drops them). It is not the team's model.

Two input styles, both reported:
    val   the crop with the grey border Ultralytics' rect validation adds (to a multiple of 32 plus half
          a stride: 24 px top and bottom here): the conventional figures, close to model.val()
    app   the crop as the app passes it to model.predict (no border): what the deployed app does
They differ a lot for some models (S5_v8m_1280 on the 270 frames: 0.169 val, 0.125 app).

Predictions are cached in runs/eval/valsets/<model>[_val].json. Writes results/val_sets_comparison.md.
Test is not touched.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from common import OUT, ROOT

CODES = ['D00', 'D10', 'D20', 'D40']
YDIR = OUT / 'yolo_nz'
SETS = {'reviewed': 'val_reviewed.txt', 'new': 'val_new.txt', 'full': 'val.txt'}
CACHE = ROOT / 'runs' / 'eval' / 'valsets'
PLACEHOLDER_MAP = {'longitudinal': 0, 'transverse': 1, 'alligator': 2, 'pothole': 3}
MODELS = {
    'v1': ('v1 (local labels only, near zone, 1024)', ROOT / 'runs' / 'local' / 'v1' / 'weights' / 'best.pt', 1024),
    'v2': ('v2 (v1 recipe, label freeze 2)', ROOT / 'runs' / 'local' / 'v2' / 'weights' / 'best.pt', 1024),
    'v2b': ('v2b (YOLOv8s RDD2022, external start)', ROOT / 'runs' / 'local' / 'v2b' / 'weights' / 'best.pt', 1024),
    'A': ('run A (local only, old data)', ROOT / 'runs' / 'v2' / 'A' / 'weights' / 'best.pt', 1280),
    'Bv2': ('run B v2 (teacher + local + replay)', ROOT / 'runs' / 'v2' / 'Bv2' / 'weights' / 'best.pt', 1280),
    'S5_v8m_1280': ('S5_v8m_1280 (B v2 + near zone)', ROOT / 'runs' / 'v3' / 'S5_v8m_1280' / 'weights' / 'best.pt', 1280),
    'placeholder': ('placeholder rdd2022_pretrained.pt (NOT ours)', ROOT / 'ml' / 'models' / 'rdd2022_pretrained.pt', 1280),
}
IOUV = np.linspace(0.5, 0.95, 10)


def frames(list_name):
    return [Path(l.strip()).stem for l in (YDIR / list_name).read_text().splitlines() if l.strip()]


def gts(stem, w, h):
    lab = YDIR / 'labels' / 'val' / f'{stem}.txt'
    out = []
    if lab.exists():
        for row in lab.read_text().split('\n'):
            p = row.split()
            if len(p) == 5:
                c, x, y, bw, bh = int(p[0]), *map(float, p[1:])
                out.append((c, (x - bw / 2) * w, (y - bh / 2) * h, (x + bw / 2) * w, (y + bh / 2) * h))
    return out


def val_pad(w, h, imgsz):
    """Rows of grey (original pixels) above and below, as Ultralytics' rect validation pads."""
    import math
    r = imgsz / max(w, h)
    target = math.ceil(h * r / 32 + 0.5) * 32
    return int(round((target - h * r) / 2 / r))


def predict(key, style='app'):
    """{stem: {'wh': (w, h), 'pred': [[cls, x1, y1, x2, y2, conf]]}}, cached."""
    import cv2
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f'{key}{"_val" if style == "val" else ""}.json'
    if cache.exists():
        return json.loads(cache.read_text())
    from ultralytics import YOLO
    _, w, imgsz = MODELS[key]
    model = YOLO(str(w))
    names = model.names
    if key == 'placeholder':
        remap = {i: PLACEHOLDER_MAP.get(n.lower()) for i, n in names.items()}
    else:
        assert [names[i] for i in range(len(names))] == CODES, names
        remap = {i: i for i in names}
    out = {}
    paths = [l.strip() for l in (YDIR / 'val.txt').read_text().splitlines() if l.strip()]
    for k, p in enumerate(paths):
        img = Path(p) if Path(p).is_absolute() else YDIR / p
        im = cv2.imread(str(img))
        h, wd = im.shape[:2]
        pad = val_pad(wd, h, imgsz) if style == 'val' else 0
        if pad:
            im = cv2.copyMakeBorder(im, pad, pad, 0, 0, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        r = model.predict(im, imgsz=imgsz, conf=0.001, iou=0.7, device=0, verbose=False, max_det=300)[0]
        preds = []
        for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
            m = remap.get(int(c))
            if m is not None:
                preds.append([m, round(b[0], 1), round(b[1] - pad, 1), round(b[2], 1), round(b[3] - pad, 1),
                              round(float(s), 5)])
        out[img.stem] = {'wh': [wd, h], 'pred': preds}
        if k % 200 == 0:
            print(f'  {key}: {k}/{len(paths)}', flush=True)
    cache.write_text(json.dumps(out))
    return out


def iou_matrix(a, b):
    a, b = np.asarray(a, float).reshape(-1, 4), np.asarray(b, float).reshape(-1, 4)
    lt = np.maximum(a[:, None, :2], b[None, :, :2])
    rb = np.minimum(a[:, None, 2:], b[None, :, 2:])
    inter = np.clip(rb - lt, 0, None).prod(2)
    area = lambda x: (x[:, 2] - x[:, 0]) * (x[:, 3] - x[:, 1])
    return inter / (area(a)[:, None] + area(b)[None, :] - inter + 1e-9)


def match(pred, gt):
    """Ultralytics' BaseValidator.match_predictions (non-scipy): tp[n_pred, 10]."""
    tp = np.zeros((len(pred), len(IOUV)), bool)
    if not len(pred) or not len(gt):
        return tp
    iou = iou_matrix([p[1:5] for p in pred], [g[1:] for g in gt]).T   # gt x pred
    iou = iou * (np.array([g[0] for g in gt])[:, None] == np.array([p[0] for p in pred])[None, :])
    for i, t in enumerate(IOUV):
        m = np.array(np.nonzero(iou >= t)).T
        if m.shape[0]:
            if m.shape[0] > 1:
                m = m[iou[m[:, 0], m[:, 1]].argsort()[::-1]]
                m = m[np.unique(m[:, 1], return_index=True)[1]]
                m = m[np.unique(m[:, 0], return_index=True)[1]]
            tp[m[:, 1].astype(int), i] = True
    return tp


def metrics(det, stems):
    from ultralytics.utils.metrics import ap_per_class
    tps, confs, pcls, tcls = [], [], [], []
    for s in stems:
        d = det[s]
        g = gts(s, *d['wh'])
        tps.append(match(d['pred'], g))
        confs += [p[5] for p in d['pred']]
        pcls += [p[0] for p in d['pred']]
        tcls += [x[0] for x in g]
    tp = np.concatenate(tps) if tps else np.zeros((0, 10), bool)
    res = ap_per_class(tp, np.array(confs), np.array(pcls), np.array(tcls), names=dict(enumerate(CODES)))
    p, r, ap, cls = res[2], res[3], res[5], res[6]
    ap50 = {int(c): float(ap[i, 0]) for i, c in enumerate(cls)}
    return dict(p=float(p.mean()), r=float(r.mean()), m50=float(ap[:, 0].mean()), m5095=float(ap.mean()),
                ap50=[ap50.get(i, 0.0) for i in range(4)], boxes=len(tcls), frames=len(stems),
                per_class_boxes=[tcls.count(i) for i in range(4)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--style', choices=('app', 'val', 'both'), default='both')
    a = ap.parse_args()
    styles = ('app', 'val') if a.style == 'both' else (a.style,)
    sets = {k: frames(v) for k, v in SETS.items()}
    res_p = CACHE / 'results.json'
    allres = json.loads(res_p.read_text()) if res_p.exists() else {}
    allres = {k: v for k, v in allres.items() if '|' in k}
    for key in MODELS:
        if a.only and key not in a.only:
            continue
        if not MODELS[key][1].exists():
            print(f'{key}: no weights yet ({MODELS[key][1].relative_to(ROOT).as_posix()}), skipped', flush=True)
            continue
        for st in styles:
            print(key, st, flush=True)
            det = predict(key, st)
            allres[f'{key}|{st}'] = {k: metrics(det, v) for k, v in sets.items()}
            print({k: round(v['m50'], 3) for k, v in allres[f'{key}|{st}'].items()}, flush=True)
    res_p.write_text(json.dumps(allres, indent=1))

    md = ['# Candidate models on the new near-zone val sets (step 6, final freeze)', '',
          'Near-zone crops (1920x432) of the val recordings. Each model at its own training size (the placeholder at '
          "the app's 1280), conf 0.001, NMS IoU 0.7, Ultralytics' matching and AP (`ml/local/eval_val_sets.py`). "
          "The placeholder is mapped to the four codes as the app maps it and is NOT the team's model. "
          "Style **val** = with the grey border of Ultralytics' rect validation (the conventional figures, close to "
          'model.val()); **app** = the crop as the app passes it to the model (no border). Test is not touched.', '',
          '**Caution:** the annotation-site pre-labels came from S5_v8m_1280. 119 of the 537 site val boxes (22%) are '
          'its own predictions kept unchanged (IoU >= 0.95, same class, conf >= 0.15; v1, A, B v2: 0-1%), so on the '
          '"new" and "full" sets S5_v8m_1280 is partly marked on its own answers. Only the 270 single-reviewer '
          'frames compare it fairly.', '']
    any_set = next(iter(allres.values()))
    for k, label in (('full', 'Full val (selection set)'), ('reviewed', 'The 270 single-reviewer frames'),
                     ('new', 'The 1,354 annotation-site frames')):
        info = any_set[k]
        md += [f'## {label}: {info["frames"]} frames, {info["boxes"]} boxes '
               f'(D00 {info["per_class_boxes"][0]}, D10 {info["per_class_boxes"][1]}, D20 {info["per_class_boxes"][2]}, '
               f'D40 {info["per_class_boxes"][3]})', '',
               '| Model | Style | imgsz | P | R | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 |',
               '|---|---|---|---|---|---|---|---|---|---|---|']
        for key, (name, _, imgsz) in MODELS.items():
            for st in ('val', 'app'):
                if f'{key}|{st}' not in allres:
                    continue
                m = allres[f'{key}|{st}'][k]
                md.append(f'| {name} | {st} | {imgsz} | {m["p"]:.3f} | {m["r"]:.3f} | {m["m50"]:.3f} | {m["m5095"]:.3f} | '
                          + ' | '.join(f'{x:.3f}' for x in m['ap50']) + ' |')
        md.append('')
    (ROOT / 'results' / 'val_sets_comparison.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

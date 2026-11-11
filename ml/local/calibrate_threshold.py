"""Calibrate the app's confidence threshold for the chosen model on the reviewed LOCAL val set.

    python ml/local/calibrate_threshold.py --run Bv2          # runs/v2/<run>/weights/best.pt

The model runs on every val frame (road-band crops, as the app sees them) with the app's own
settings: imgsz 1280 (INFERENCE_IMGSZ) and NMS IoU 0.45 (IOU_THRESHOLD), keeping everything down to
conf 0.01. For each threshold 0.01..0.50 (step 0.01; it includes 0.10) a prediction counts as correct when it has the
reviewed box's class and IoU >= 0.5 with it (one-to-one, highest IoU first; label_quality.match).
The chosen threshold maximises F1 over all classes together (ties: the higher threshold, i.e.
fewer false alarms). The app uses one threshold for every class, so per-class best thresholds are
reported for information only. This threshold is for deployment only: mAP is always computed at
Ultralytics' default validation conf (0.001), never at this threshold.

Test is not touched. Writes results/threshold_calibration.md and
results/threshold_calibration.json (read by test_eval.py and deploy_model.py).

From the final label freeze (2026-11-11), for runs on the near-zone data:

    python ml/local/calibrate_threshold.py --run v1 --dataset nz --val reviewed   # or new / full

--dataset nz reads data/local/yolo_nz (near-zone crops: what the app passes to the model); --val picks
the selection set (val_reviewed.txt = the 270 single-reviewer frames, val_new.txt = the 1,354
annotation-site frames, val.txt = both). The other two are reported at the same threshold. imgsz
defaults to the run's training size (its args.yaml), which the app then uses (model_config.json).
Also writes results/threshold_<run>.md. The module defaults (old yolo/ data, imgsz 1280) are
unchanged, so test_eval.py behaves exactly as before.
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from common import OUT, ROOT
from label_quality import match

CODES = ['D00', 'D10', 'D20', 'D40']
IMGSZ = 1280       # backend/services/video_processor.py INFERENCE_IMGSZ
NMS_IOU = 0.45     # backend/services/video_processor.py IOU_THRESHOLD
MATCH_IOU = 0.5
THRESHOLDS = [round(0.01 * i, 2) for i in range(1, 51)]   # 0.01..0.50 (team, 2026-11-11; was 0.05..0.90)
RESULT = ROOT / 'results' / 'threshold_calibration.json'


PROJECTS = ('v2', 'v3', 'local')
VAL_LISTS = {'reviewed': 'val_reviewed.txt', 'new': 'val_new.txt', 'full': 'val.txt'}
VAL_LABEL = {'reviewed': 'the 270 single-reviewer val frames', 'new': 'the 1,354 annotation-site val frames',
             'full': 'all val frames (single-reviewer + annotation site)'}


def run_dir(run):
    for p in PROJECTS:
        d = ROOT / 'runs' / p / run
        if (d / 'weights' / 'best.pt').exists():
            return d
    sys.exit(f'No best.pt for run {run} under runs/{"|".join(PROJECTS)}/{run}/weights/')


def weights_for(run):
    return run_dir(run) / 'weights' / 'best.pt'


def train_imgsz(run):
    import re
    m = re.search(r'^imgsz: (\d+)', (run_dir(run) / 'args.yaml').read_text(), flags=re.M)
    return int(m.group(1)) if m else IMGSZ


def frames_of(split, ydir=None, list_name=None):
    """[(image path, [{'cls', 'box'} in pixels])] for a split of data/local/yolo (or ydir)."""
    import cv2
    ydir = ydir or OUT / 'yolo'
    out = []
    for line in (ydir / (list_name or f'{split}.txt')).read_text().splitlines():
        if not line.strip():
            continue
        img = Path(line.strip())
        if not img.is_absolute():
            img = ydir / img
        lab = ydir / 'labels' / split / (img.stem + '.txt')
        h, w = cv2.imread(str(img)).shape[:2]
        gts = []
        if lab.exists():
            for row in lab.read_text().split('\n'):
                p = row.split()
                if len(p) == 5:
                    c, x, y, bw, bh = int(p[0]), *map(float, p[1:])
                    gts.append({'cls': c, 'box': ((x - bw / 2) * w, (y - bh / 2) * h, (x + bw / 2) * w, (y + bh / 2) * h)})
        out.append((img, gts))
    return out


MEMBER_CONF = 0.05   # backend/services/video_processor.py MEMBER_CONF: each ensemble member's floor before fusion


def predict_fused(members, frames, device=0, border=0, tta=False):
    """As predict(), for an ensemble [(weights, imgsz), ...]: every model at MEMBER_CONF, fused with the app's
    own code (backend/services/box_fusion.py); 'conf' is the fused score."""
    import sys
    sys.path.insert(0, str(ROOT / 'backend' / 'services'))
    from box_fusion import fuse
    per = [predict(w, frames, device, sz, border, tta, conf=MEMBER_CONF) for w, sz in members]
    out = {}
    for img, _ in frames:
        f = fuse([[(d['cls'], *d['box'], d['conf']) for d in p[img]] for p in per])
        out[img] = [{'cls': int(x[0]), 'box': tuple(x[1:5]), 'conf': float(x[5])} for x in f]
    return out


def predict(weights, frames, device=0, imgsz=IMGSZ, border=0, tta=False, conf=0.01):
    """{image path: [{'cls', 'box', 'conf'}]} at the app's settings, conf >= 0.01."""
    from ultralytics import YOLO
    model = YOLO(str(weights))
    names = model.names
    assert [names[i] for i in range(len(names))] == CODES, f'unexpected classes {names}'
    det = {}
    for img, _ in frames:
        src = str(img)
        if border:   # the app's grey rows above and below the crop (video_processor.INPUT_BORDER_PX)
            import cv2
            src = cv2.copyMakeBorder(cv2.imread(str(img)), border, border, 0, 0, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        r = model.predict(src, imgsz=imgsz, conf=conf, iou=NMS_IOU, device=device, verbose=False, augment=tta)[0]
        if not border:   # exactly as before (what test_eval.py uses)
            det[img] = [{'cls': int(c), 'box': tuple(map(float, b)), 'conf': float(s)}
                        for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]
            continue
        h = r.orig_shape[0] - 2 * border
        det[img] = []
        for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist()):
            y1, y2 = min(max(b[1] - border, 0), h), min(max(b[3] - border, 0), h)
            if y2 - y1 >= 2:
                det[img].append({'cls': int(c), 'box': (float(b[0]), float(y1), float(b[2]), float(y2)), 'conf': float(s)})
    return det


def counts(frames, det, thr):
    """Per-class TP, FP, FN at confidence >= thr."""
    tp, fp, fn = Counter(), Counter(), Counter()
    for img, gts in frames:
        preds = [d for d in det[img] if d['conf'] >= thr]
        m = match(preds, gts, MATCH_IOU, same_class=True)
        for i, p in enumerate(preds):
            (tp if i in m else fp)[p['cls']] += 1
        hit = set(m.values())
        for j, g in enumerate(gts):
            if j not in hit:
                fn[g['cls']] += 1
    return tp, fp, fn


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def table(frames, det, thr):
    """Rows (label, n boxes, TP, FP, FN, P, R, F1) per class and for all classes at thr."""
    tp, fp, fn = counts(frames, det, thr)
    rows = []
    for c, code in enumerate(CODES):
        rows.append((code, tp[c] + fn[c], tp[c], fp[c], fn[c], *prf(tp[c], fp[c], fn[c])))
    T, F, N = sum(tp.values()), sum(fp.values()), sum(fn.values())
    rows.append(('All classes', T + N, T, F, N, *prf(T, F, N)))
    return rows


def md_rows(rows):
    return ['| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |', '|---|---|---|---|---|---|---|---|'] + \
           [f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]:.2f} | {r[6]:.2f} | {r[7]:.2f} |' for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True, help='run name under runs/v2, runs/v3 or runs/local')
    ap.add_argument('--device', default='0', help="'cpu' to leave the GPU to a training run")
    ap.add_argument('--limit', type=int, default=0, help='first N frames only (a smoke test; writes nothing)')
    ap.add_argument('--dataset', choices=('yolo', 'nz'), default='yolo', help='nz = data/local/yolo_nz (near zone)')
    ap.add_argument('--val', choices=tuple(VAL_LISTS), default='full', help='selection val set (with --dataset nz)')
    ap.add_argument('--imgsz', type=int, help="default: the run's training size (nz) or 1280 (yolo)")
    ap.add_argument('--border', type=int, default=0, help='grey rows above and below the crop, as the app adds them (border_px)')
    ap.add_argument('--members', nargs='*', default=[], metavar='RUN[:IMGSZ]',
                    help='further models of an ensemble (fused with --run, as the app does with model_config "ensemble")')
    ap.add_argument('--tta', action='store_true', help='test-time augmentation, as the app runs it when the config says tta')
    a = ap.parse_args()
    w = weights_for(a.run)
    nz = a.dataset == 'nz'
    ydir = OUT / ('yolo_nz' if nz else 'yolo')
    imgsz = a.imgsz or (train_imgsz(a.run) if nz else IMGSZ)
    sets = {k: frames_of('val', ydir, v) for k, v in VAL_LISTS.items()} if nz else {'full': frames_of('val')}
    sel = a.val if nz else 'full'
    if a.limit:
        sets = {k: v[:a.limit] for k, v in sets.items()}
    members = []
    for m in a.members:
        run, _, sz = m.partition(':')
        members.append({'run': run, 'weights': weights_for(run).relative_to(ROOT).as_posix(),
                        'imgsz': int(sz) if sz else train_imgsz(run)})
    todo = [f for k in sets for f in sets[k]] if a.limit else sets['full']
    if members:
        det = predict_fused([(w, imgsz)] + [(ROOT / m['weights'], m['imgsz']) for m in members], todo, a.device, a.border, a.tta)
    else:
        det = predict(w, todo, a.device, imgsz, a.border, a.tta)
    frames = sets[sel]
    curve = []
    for t in THRESHOLDS:
        all_row = table(frames, det, t)[-1]
        curve.append((t, all_row[5], all_row[6], all_row[7]))
    best = max(curve, key=lambda x: (round(x[3], 4), x[0]))
    thr = best[0]
    per_class_best = {}
    for c, code in enumerate(CODES):
        f1s = [(table(frames, det, t)[c][7], t) for t in THRESHOLDS]
        f, t = max(f1s, key=lambda x: (round(x[0], 4), x[1]))
        per_class_best[code] = (t, f)
    rows = table(frames, det, thr)
    if a.limit:
        print(f'Smoke test on {len(frames)} frames: threshold {thr:.2f}')
        print('\n'.join(md_rows(rows)))
        return
    RESULT.write_text(json.dumps({'run': a.run, 'weights': str(w.relative_to(ROOT)), 'threshold': thr,
                                  'val_f1': rows[-1][7], 'val_precision': rows[-1][5], 'val_recall': rows[-1][6],
                                  'imgsz': imgsz, 'border_px': a.border, 'tta': a.tta, 'ensemble': members, 'nms_iou': NMS_IOU, 'match_iou': MATCH_IOU,
                                  'dataset': ydir.name, 'val_set': sel, 'val_frames': len(frames),
                                  'when': datetime.now().isoformat(timespec='seconds')}, indent=1))
    where = (f'Data `data/local/{ydir.name}`; selection set: {VAL_LABEL[sel]}, {len(frames)} frames' if nz else
             f'Reviewed local val set, {len(frames)} frames (road-band crops)')
    md = [f'# Confidence threshold calibrated on local val ({a.run})', '',
          f'Weights `{w.relative_to(ROOT).as_posix()}`'
          + (' fused with ' + ', '.join(f'`{m["weights"]}` (imgsz {m["imgsz"]})' for m in members)
             + f' (each model at conf {MEMBER_CONF}, weighted box fusion; the threshold is on the fused score)' if members else '')
          + f'. {where}. '
          f'App settings: imgsz {imgsz}, grey border {a.border} px, TTA {"on" if a.tta else "off"}, NMS IoU {NMS_IOU}. A detection is correct with the labelled class and IoU >= {MATCH_IOU}. '
          'Threshold = highest F1 over all classes (ties: the higher threshold).', '',
          f'**Chosen threshold: {thr:.2f}** (the app used 0.15 before).', '', f'## At {thr:.2f}, on the selection set', ''] + md_rows(rows)
    for k in (k for k in sets if k != sel):
        md += ['', f'## Same threshold ({thr:.2f}) on {VAL_LABEL[k]} ({len(sets[k])} frames)', ''] + md_rows(table(sets[k], det, thr))
    md += ['', '## Precision, recall and F1 by threshold (all classes, selection set)', '', '| Threshold | Precision | Recall | F1 |', '|---|---|---|---|'] + \
         [f'| {t:.2f} | {p:.2f} | {r:.2f} | {f:.2f} |' for t, p, r, f in curve] + \
         ['', '## Best threshold per class (information only: the app uses one threshold)', '', '| Class | Threshold | F1 |', '|---|---|---|'] + \
         [f'| {c} | {t:.2f} | {f:.2f} |' for c, (t, f) in per_class_best.items()]
    (ROOT / 'results' / 'threshold_calibration.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    (ROOT / 'results' / f'threshold_{a.run}.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

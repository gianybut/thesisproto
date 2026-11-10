"""Diagnostics on the reviewed LOCAL val set before the test evaluation (test is not touched).

    python ml/local/val_diagnostics.py --check                 # label/crop alignment only
    python ml/local/val_diagnostics.py --run Bv1 [--device cpu]

--check (no model):
  * every local image in data/local/yolo (train, val, test): its size equals the reviewed state's
    width/height and the crop the extractor recorded (manifest: frame width, int(h*bottom) -
    int(h*top)); it is the same file as data/local/frames/<name> (what the review tool showed); its
    label file equals the state's boxes normalised by that size; every box lies inside the image.
  * results/val_alignment_overlay.jpg: 12 val frames (3 per class, seed 42). Each tile: the full
    upright video frame at that second with the road band (cyan lines) and the label boxes mapped
    back into the full frame (green), and below it the training crop with the boxes from the label
    file (green) and from the review state (thin magenta, drawn on top). Aligned = the two coincide
    and the boxes sit on the same damage in both pictures.
  Writes results/val_alignment.md.

--run (the model's best.pt, runs/v2/<run>): one prediction pass over val (imgsz 1280, conf 0.001,
  no NMS yet, max 3000 boxes), then
  * AP@50 per class at match IoU 0.25 and 0.50 (per-class NMS 0.7 as in Ultralytics validation;
    101-point AP, ultralytics compute_ap; a prediction is correct with the same class and IoU >=
    the threshold, one-to-one in confidence order). The 0.50 column should be close to the
    Chapter V table (Ultralytics' own matching differs slightly).
  * class-agnostic AP: the four classes merged into "damage", class-agnostic NMS 0.7.
  * the threshold candidate as in calibrate_threshold.py (app settings: per-class NMS 0.45; max F1
    over all classes), and at that threshold: the confusion matrix (match IoU 0.5 regardless of
    class, one-to-one, highest IoU first; rows = reviewed class, columns = predicted) and frame-level
    accuracy / precision / recall for "frame contains damage" (>= 1 reviewed box vs >= 1 prediction).
  Writes results/val_diagnostics_<run>.md.
"""

import argparse
import json
import random
import sys
from collections import Counter, defaultdict

import cv2
import numpy as np

import calibrate_threshold as cal
from common import OUT, ROOT, VIDEOS, open_upright, read_csv
from label_quality import iou, match

CODES = cal.CODES
YOLO_DIR = OUT / 'yolo'
GREEN, MAGENTA, CYAN = (0, 200, 0), (255, 0, 255), (255, 255, 0)


def state(frame):
    return json.loads((OUT / 'reviewed' / 'state' / f'{frame[:-4]}.json').read_text(encoding='utf-8'))


def label_boxes(path, w, h):
    out = []
    if path.exists():
        for row in path.read_text().splitlines():
            p = row.split()
            if len(p) == 5:
                c, x, y, bw, bh = int(p[0]), *map(float, p[1:])
                out.append((c, (x - bw / 2) * w, (y - bh / 2) * h, (x + bw / 2) * w, (y + bh / 2) * h))
    return out


def check_alignment():
    man = {r['frame']: r for r in read_csv(OUT / 'manifest.csv')}
    recs = {r['id']: r for r in read_csv(OUT / 'recordings.csv')}
    problems, n_img, n_box = [], Counter(), Counter()
    for split in ('train', 'val', 'test'):
        for img in sorted((YOLO_DIR / 'images' / split).glob('R*.jpg')):
            f = img.name
            n_img[split] += 1
            im = cv2.imread(str(img))
            h, w = im.shape[:2]
            s, m = state(f), man.get(f)
            if (s['width'], s['height']) != (w, h):
                problems.append(f'{split}/{f}: image {w}x{h}, review state {s["width"]}x{s["height"]}')
            if m is None:
                problems.append(f'{split}/{f}: not in manifest.csv')
            else:
                fh = int(m['frame_h'])
                exp_h = int(fh * float(m['band_bottom'])) - int(fh * float(m['band_top']))
                if (int(m['frame_w']), exp_h) != (w, h) or int(fh * float(m['band_top'])) != int(m['band_top_px']):
                    problems.append(f'{split}/{f}: crop {w}x{h}, extractor recorded {m["frame_w"]}x{exp_h}')
                rec = recs[m['recording']]
                from common import band_for
                bt, bb, _ = band_for(rec)
                if abs(bt - float(m['band_top'])) > 1e-6 or abs(bb - float(m['band_bottom'])) > 1e-6:
                    problems.append(f'{split}/{f}: cropped with band {m["band_top"]}-{m["band_bottom"]}, '
                                    f'the approved band is {bt}-{bb}')
            src = OUT / 'frames' / f
            if not src.exists() or not src.samefile(img):
                if not src.exists() or src.read_bytes() != img.read_bytes():
                    problems.append(f'{split}/{f}: not the same picture as frames/{f} (what the review tool showed)')
            lab = label_boxes(YOLO_DIR / 'labels' / split / f'{f[:-4]}.txt', w, h)
            want = sorted((CODES.index(b['cls']), b['x1'], b['y1'], b['x2'], b['y2']) for b in s['boxes'])
            if len(lab) != len(want) or any(a[0] != b[0] or max(abs(x - y) for x, y in zip(a[1:], b[1:])) > 1.0
                                             for a, b in zip(sorted(lab), want)):
                problems.append(f'{split}/{f}: label file differs from the review state ({len(lab)} vs {len(want)} boxes)')
            for c, x1, y1, x2, y2 in lab:
                n_box[split] += 1
                if x1 < -1 or y1 < -1 or x2 > w + 1 or y2 > h + 1 or x2 <= x1 or y2 <= y1:
                    problems.append(f'{split}/{f}: box outside the image or empty ({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f})')
    return problems, n_img, n_box, man, recs


def overlay(man, recs):
    rng = random.Random(42)
    by_cls = defaultdict(list)
    for img in sorted((YOLO_DIR / 'images' / 'val').glob('R*.jpg')):
        for b in state(img.name)['boxes']:
            by_cls[b['cls']].append(img.name)
    picked = []
    for c in CODES:
        pool = sorted(set(by_cls[c]) - set(picked))
        picked += rng.sample(pool, min(3, len(pool)))
    tiles = []
    for f in picked:
        m = man[f]
        rec = recs[m['recording']]
        cap, rotate, W, H = open_upright(str(VIDEOS / rec['folder'] / rec['video']))
        cap.set(cv2.CAP_PROP_POS_FRAMES, round(int(m['second']) * cap.get(cv2.CAP_PROP_FPS)))
        ok, full = cap.read()
        cap.release()
        crop = cv2.imread(str(YOLO_DIR / 'images' / 'val' / f))
        h, w = crop.shape[:2]
        lab = label_boxes(YOLO_DIR / 'labels' / 'val' / f'{f[:-4]}.txt', w, h)
        t = max(2, w // 500)
        if ok:
            if rotate is not None:
                full = cv2.rotate(full, rotate)
            top = int(m['band_top_px'])
            fh = full.shape[0]
            bot = int(fh * float(m['band_bottom']))
            cv2.line(full, (0, top), (full.shape[1], top), CYAN, t + 1)
            cv2.line(full, (0, bot - 1), (full.shape[1], bot - 1), CYAN, t + 1)
            for c, x1, y1, x2, y2 in lab:
                cv2.rectangle(full, (int(x1), int(y1 + top)), (int(x2), int(y2 + top)), GREEN, t + 1)
        else:
            full = np.zeros((int(m['frame_h']), int(m['frame_w']), 3), np.uint8)
            cv2.putText(full, 'video frame could not be read', (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
        for c, x1, y1, x2, y2 in lab:
            cv2.rectangle(crop, (int(x1), int(y1)), (int(x2), int(y2)), GREEN, t + 3)
            cv2.putText(crop, CODES[c], (int(x1), max(30, int(y1) - 8)), cv2.FONT_HERSHEY_SIMPLEX, 1.4, GREEN, 3)
        for b in state(f)['boxes']:
            cv2.rectangle(crop, (int(b['x1']), int(b['y1'])), (int(b['x2']), int(b['y2'])), MAGENTA, max(1, t - 1))
        full = cv2.resize(full, (960, int(full.shape[0] * 960 / full.shape[1])))
        crop = cv2.resize(crop, (960, int(h * 960 / w)))
        head = np.full((44, 960, 3), 255, np.uint8)
        cv2.putText(head, f'{f}  ({rec["folder"][:40]}, band {float(m["band_top"]):.2f}-{float(m["band_bottom"]):.2f})',
                    (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        tiles.append(np.vstack([head, full, np.full((6, 960, 3), 255, np.uint8), crop]))
    hmax = max(x.shape[0] for x in tiles)
    tiles = [np.vstack([x, np.full((hmax - x.shape[0], 960, 3), 255, np.uint8)]) for x in tiles]
    rows = [np.hstack(sum(([x, np.full((hmax, 12, 3), 255, np.uint8)] for x in tiles[i:i + 3]), [])[:-1])
            for i in range(0, len(tiles), 3)]
    sheet = np.vstack(sum(([r, np.full((12, r.shape[1], 3), 255, np.uint8)] for r in rows), [])[:-1])
    out = ROOT / 'results' / 'val_alignment_overlay.jpg'
    cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return out, picked


def run_check():
    problems, n_img, n_box, man, recs = check_alignment()
    out, picked = overlay(man, recs)
    md = ['# Label / crop alignment check', '',
          'Every local image in data/local/yolo: size = review state = extractor crop (approved band); same picture '
          'as the review tool showed; label file = reviewed boxes; boxes inside the image.', '',
          '| Split | Images | Boxes |', '|---|---|---|'] + \
         [f'| {s} | {n_img[s]} | {n_box[s]} |' for s in ('train', 'val', 'test')] + \
         ['', f'**Problems: {len(problems)}**', ''] + [f'- {p}' for p in problems[:50]] + \
         ['', f'Overlay: `results/val_alignment_overlay.jpg` ({len(picked)} val frames: {", ".join(picked)}). '
          'Top: full video frame, road band (cyan), labels mapped back (green). Bottom: training crop, label file '
          '(green) and review state (magenta).']
    (ROOT / 'results' / 'val_alignment.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))
    return not problems


# ---------------------------------------------------------------- metrics

def raw_predictions(run, frames, device):
    cache = ROOT / 'runs' / 'eval' / f'diag_raw_{run}.json'
    w = cal.weights_for(run)
    if cache.exists():
        c = json.loads(cache.read_text())
        if c['mtime'] == w.stat().st_mtime and len(c['det']) == len(frames):
            return {k: v for k, v in c['det'].items()}
    from ultralytics import YOLO
    model = YOLO(str(w))
    det = {}
    for i, (img, _) in enumerate(frames):
        r = model.predict(str(img), imgsz=cal.IMGSZ, conf=0.001, iou=0.99, max_det=3000, device=device, verbose=False)[0]
        det[str(img)] = [[int(c), float(s), *map(float, b)]
                         for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]
        if i % 25 == 0:
            print(f'  predicted {i + 1}/{len(frames)}', flush=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({'mtime': w.stat().st_mtime, 'det': det}))
    return det


def nms(dets, thr, agnostic):
    import torch
    import torchvision
    if not dets:
        return []
    t = torch.tensor(dets, dtype=torch.float32)
    boxes = t[:, 2:6]
    keep = torchvision.ops.nms(boxes, t[:, 1], thr) if agnostic else \
        torchvision.ops.batched_nms(boxes, t[:, 1], t[:, 0].long(), thr)
    return [dets[i] for i in keep.tolist()]


def ap_at(frames, det, cls, iou_thr):
    """101-point AP for one class (cls None = class-agnostic) at a match IoU."""
    from ultralytics.utils.metrics import compute_ap
    preds, n_gt = [], 0
    for img, gts in frames:
        g = [x['box'] for x in gts if cls is None or x['cls'] == cls]
        n_gt += len(g)
        ps = sorted((d for d in det[str(img)] if cls is None or d[0] == cls), key=lambda d: -d[1])
        used = set()
        for d in ps:
            best, bj = 0.0, -1
            for j, gb in enumerate(g):
                if j not in used:
                    v = iou(d[2:6], gb)
                    if v > best:
                        best, bj = v, j
            ok = best >= iou_thr
            if ok:
                used.add(bj)
            preds.append((d[1], ok))
    if not n_gt:
        return None
    preds.sort(key=lambda x: -x[0])
    tp = np.cumsum([p[1] for p in preds])
    fp = np.cumsum([not p[1] for p in preds])
    if not len(preds):
        return 0.0
    return float(compute_ap(list(tp / n_gt), list(tp / np.maximum(tp + fp, 1e-9)))[0])


def run_metrics(run, device):
    frames = cal.frames_of('val')
    raw = raw_predictions(run, frames, device)
    val_nms = {k: nms(v, 0.7, False) for k, v in raw.items()}
    agn_nms = {k: nms(v, 0.7, True) for k, v in raw.items()}
    app = {k: [{'cls': d[0], 'conf': d[1], 'box': tuple(d[2:6])} for d in nms(v, cal.NMS_IOU, False)] for k, v in raw.items()}
    app_by_path = {img: app[str(img)] for img, _ in frames}

    ap = {t: [ap_at(frames, val_nms, c, t) for c in range(4)] for t in (0.25, 0.5)}
    agn = {t: ap_at(frames, agn_nms, None, t) for t in (0.25, 0.5)}

    curve = [(t, *cal.table(frames, app_by_path, t)[-1][5:8]) for t in cal.THRESHOLDS]
    thr = max(curve, key=lambda x: (round(x[3], 4), x[0]))[0]
    rows = cal.table(frames, app_by_path, thr)

    labels = CODES + ['background']
    cm = np.zeros((5, 5), int)
    for img, gts in frames:
        preds = [d for d in app_by_path[img] if d['conf'] >= thr]
        m = match(preds, gts, 0.5, same_class=False)
        for i, j in m.items():
            cm[gts[j]['cls'], preds[i]['cls']] += 1
        for i, p in enumerate(preds):
            if i not in m:
                cm[4, p['cls']] += 1
        hit = set(m.values())
        for j, g in enumerate(gts):
            if j not in hit:
                cm[g['cls'], 4] += 1

    tp = fp = fn = tn = 0
    for img, gts in frames:
        truth = bool(gts)
        said = any(d['conf'] >= thr for d in app_by_path[img])
        tp += truth and said
        fp += said and not truth
        fn += truth and not said
        tn += not truth and not said
    n = len(frames)
    acc = (tp + tn) / n
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0

    md = [f'# Val diagnostics: {run}', '',
          f'Reviewed local val set, {n} frames ({sum(1 for _, g in frames if g)} with damage, '
          f'{sum(len(g) for _, g in frames)} boxes). Weights `runs/v2/{run}/weights/best.pt`, imgsz 1280.', '',
          '## AP@50 per class at match IoU 0.25 and 0.50', '',
          'Per-class NMS 0.7, conf >= 0.001, 101-point AP. Correct = same class and IoU >= the match threshold.', '',
          '| Class | Boxes | AP, IoU 0.25 | AP, IoU 0.50 |', '|---|---|---|---|']
    nbox = Counter(g['cls'] for _, gs in frames for g in gs)
    for c in range(4):
        md.append(f'| {CODES[c]} | {nbox[c]} | {ap[0.25][c]:.3f} | {ap[0.5][c]:.3f} |')
    md += [f'| Mean (mAP) | {sum(nbox.values())} | {np.mean(ap[0.25]):.3f} | {np.mean(ap[0.5]):.3f} |', '',
           '## Class-agnostic ("damage", the four classes merged)', '',
           'Class-agnostic NMS 0.7; correct = any reviewed box with IoU >= the match threshold.', '',
           '| | AP, IoU 0.25 | AP, IoU 0.50 |', '|---|---|---|',
           f'| Damage (any class) | {agn[0.25]:.3f} | {agn[0.5]:.3f} |', '',
           f'## At the threshold candidate {thr:.2f}', '',
           f'App settings (per-class NMS {cal.NMS_IOU}); threshold = highest F1 over all classes on val (as calibrate_threshold.py).', '']
    md += cal.md_rows(rows)
    md += ['', 'Confusion matrix (match IoU 0.5 regardless of class; rows = reviewed class, columns = predicted; '
           '"background" row = false alarms, column = missed):', '',
           '| Reviewed \\ Predicted | ' + ' | '.join(labels) + ' |', '|---' * 6 + '|']
    for i, lab in enumerate(labels):
        md.append(f'| {lab} | ' + ' | '.join(str(v) if not (i == 4 and j == 4) else '-' for j, v in enumerate(cm[i])) + ' |')
    md += ['', 'Frame level, "frame contains damage" (>= 1 reviewed box vs >= 1 prediction at the threshold):', '',
           '| Frames | With damage | Without | TP | FP | FN | TN | Accuracy | Precision | Recall |',
           '|---|---|---|---|---|---|---|---|---|---|',
           f'| {n} | {tp + fn} | {fp + tn} | {tp} | {fp} | {fn} | {tn} | {acc:.3f} | {prec:.3f} | {rec:.3f} |']
    (ROOT / 'results' / f'val_diagnostics_{run}.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--run')
    ap.add_argument('--device', default='cpu')
    a = ap.parse_args()
    if a.check:
        sys.exit(0 if run_check() else 1)
    if not a.run:
        sys.exit('Give --check or --run NAME')
    run_metrics(a.run, a.device)


if __name__ == '__main__':
    main()

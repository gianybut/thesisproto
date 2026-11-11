"""Inference-side options for a trained model, scored on near-zone val (no training, test untouched).

    python ml/local/infer_sweep.py --weights runs/local/v1/weights/best.pt --name v1 \
        --imgsz 1024 1280 1536 --pad 0 24 --tta 0 1 [--set reviewed] [--device cpu]

For every combination: predict each val frame of the chosen set (default: the 270 reviewed frames) with
    imgsz   the inference input size (width of the 1920x432 near-zone crop after resizing)
    pad     rows of grey (114) added above and below the crop, in original pixels (24 = what Ultralytics'
            rect validation adds at 1024/1280; 0 = the crop as the app passed it until 2026-11-11)
    tta     Ultralytics test-time augmentation (augment=True: flips and scales)
at conf 0.001, NMS IoU 0.7, and score mAP@50 / mAP@50-95 with eval_val_sets.metrics (Ultralytics' AP).
Predictions are cached in runs/eval/sweep/<name>/; the table is appended to results/infer_sweep.md.
"""

import argparse
import itertools
import json
import time
from datetime import datetime
from pathlib import Path

from common import ROOT
from eval_val_sets import CODES, SETS, YDIR, frames, metrics

OUT = ROOT / 'runs' / 'eval' / 'sweep'


def run(model, stems, paths, imgsz, pad, tta, device):
    import cv2
    out = {}
    for s in stems:
        im = cv2.imread(paths[s])
        h, w = im.shape[:2]
        if pad:
            im = cv2.copyMakeBorder(im, pad, pad, 0, 0, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        r = model.predict(im, imgsz=imgsz, conf=0.001, iou=0.7, device=device, verbose=False, max_det=300,
                          augment=bool(tta))[0]
        out[s] = {'wh': [w, h], 'pred': [[int(c), round(b[0], 1), round(b[1] - pad, 1), round(b[2], 1), round(b[3] - pad, 1),
                                          round(float(cf), 5)]
                                         for b, c, cf in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--weights', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--imgsz', type=int, nargs='+', default=[1024])
    ap.add_argument('--pad', type=int, nargs='+', default=[0])
    ap.add_argument('--tta', type=int, nargs='+', default=[0])
    ap.add_argument('--set', choices=tuple(SETS), default='reviewed')
    ap.add_argument('--device', default='0')
    a = ap.parse_args()
    from ultralytics import YOLO
    model = YOLO(str(ROOT / a.weights))
    names = model.names
    assert len(names) == 4, names
    stems = frames(SETS[a.set])
    paths = {}
    for l in (YDIR / 'val.txt').read_text().splitlines():
        if l.strip():
            p = Path(l.strip())
            paths[p.stem] = str(p if p.is_absolute() else YDIR / p)
    d = OUT / a.name
    d.mkdir(parents=True, exist_ok=True)
    rows = []
    for imgsz, pad, tta in itertools.product(a.imgsz, a.pad, a.tta):
        cache = d / f'{a.set}_{imgsz}_p{pad}_t{tta}.json'
        t0 = time.time()
        if cache.exists():
            det, dt = json.loads(cache.read_text()), None
        else:
            det = run(model, stems, paths, imgsz, pad, tta, a.device)
            dt = (time.time() - t0) / len(stems)
            cache.write_text(json.dumps(det))
        m = metrics(det, stems)
        rows.append((imgsz, pad, tta, m, dt))
        print(f'{a.name} {a.set} imgsz {imgsz} pad {pad} tta {tta}: mAP50 {m["m50"]:.3f} mAP50-95 {m["m5095"]:.3f} '
              + ' '.join(f'{c} {x:.3f}' for c, x in zip(CODES, m['ap50'])) + (f'  ({dt:.2f} s/frame)' if dt else ''), flush=True)
    md = [f'## {a.name} (`{a.weights}`), {a.set} set, {len(stems)} frames ({datetime.now():%Y-%m-%d %H:%M}, device {a.device})', '',
          '| imgsz | Border (px) | TTA | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | s/frame |', '|---|---|---|---|---|---|---|---|---|---|']
    for imgsz, pad, tta, m, dt in rows:
        md.append(f'| {imgsz} | {pad} | {"yes" if tta else "no"} | {m["m50"]:.3f} | {m["m5095"]:.3f} | '
                  + ' | '.join(f'{x:.3f}' for x in m['ap50']) + f' | {f"{dt:.2f}" if dt else "cached"} |')
    p = ROOT / 'results' / 'infer_sweep.md'
    head = '' if p.exists() else ('# Inference options on near-zone val (infer_sweep.py)\n\nconf 0.001, NMS IoU 0.7; '
                                  'border = grey rows above and below the 1920x432 crop. Test is not touched.\n\n')
    with open(p, 'a', encoding='utf-8') as f:
        f.write(head + '\n'.join(md) + '\n\n')


if __name__ == '__main__':
    main()

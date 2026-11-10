"""Run the RDD2022 teacher on local frames and cache its boxes (for the pseudo-label rule, the
review expansion and the train yield). The teacher is never deployed.

    python ml/local/teacher_detect.py --splits val --reviewed-only --imgsz 960 1280
    python ml/local/teacher_detect.py --splits val test train --imgsz 1280

Boxes at confidence >= --conf (default 0.05, deliberately low; thresholds are chosen later) on the
road-band crop, the server's IOU_THRESHOLD. Cached per image size in
data/local/teacher/dets_<imgsz>.csv (frame, x1..y2 in band-crop pixels, class, confidence, clip);
frames already in the cache are skipped. CLIP (the backend's damage_verifier.score, on the whole
frame as the server does) is added on request by add_clip().
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import cv2

from common import OUT, ROOT, read_csv
from services.video_processor import IOU_THRESHOLD

TEACHER = ROOT / 'runs' / 'teacher' / 'teacher' / 'weights' / 'best.pt'
CODES = ['D00', 'D10', 'D20', 'D40']
DIR = OUT / 'teacher'
FIELDS = ['frame', 'x1', 'y1', 'x2', 'y2', 'cls', 'conf', 'clip']


def cache_path(imgsz, tiles=1, tag=''):
    """Cache file; tag names another model's cache (e.g. 'Bv1'), empty for the teacher."""
    base = f'dets_{tag + "_" if tag else ""}{imgsz}'
    return DIR / (f'{base}.csv' if tiles == 1 else f'{base}_t{tiles}.csv')


def tile_spans(width, tiles, overlap=0.15):
    """Left/right pixel edges of `tiles` equal tiles across the width, neighbours overlapping."""
    if tiles == 1:
        return [(0, width)]
    w = width / (tiles - (tiles - 1) * overlap)
    step = w * (1 - overlap)
    return [(int(round(i * step)), int(round(min(width, i * step + w)))) for i in range(tiles)]


def load(imgsz, tiles=1, tag=''):
    """{frame: [box dicts]} for every frame in the cache (frames with no box map to [])."""
    p = cache_path(imgsz, tiles, tag)
    out = {}
    if p.exists():
        for r in read_csv(p):
            out.setdefault(r['frame'], [])
            if r['cls']:
                out[r['frame']].append(dict(box=tuple(float(r[k]) for k in ('x1', 'y1', 'x2', 'y2')), cls=r['cls'],
                                            conf=float(r['conf']), clip=float(r['clip']) if r['clip'] else None))
    return out


def save(imgsz, dets, tiles=1, tag=''):
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = cache_path(imgsz, tiles, tag).with_suffix('.tmp')
    with open(tmp, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for fr in sorted(dets):
            if not dets[fr]:
                w.writerow(dict(frame=fr, x1='', y1='', x2='', y2='', cls='', conf='', clip=''))
            for d in dets[fr]:
                w.writerow(dict(frame=fr, x1=round(d['box'][0], 1), y1=round(d['box'][1], 1), x2=round(d['box'][2], 1),
                                y2=round(d['box'][3], 1), cls=d['cls'], conf=round(d['conf'], 4),
                                clip='' if d['clip'] is None else d['clip']))
    tmp.replace(cache_path(imgsz, tiles, tag))


def detect(frames, imgsz, conf=0.05, batch=16, tiles=1, weights=None, tag=''):
    """Teacher boxes per frame. With tiles > 1 the band crop is cut into overlapping tiles across its
    width, each tile is run at imgsz, and the boxes are merged with class-wise NMS (same IoU)."""
    import torch
    import torchvision
    from ultralytics import YOLO
    dets = load(imgsz, tiles, tag)
    todo = [f for f in frames if f not in dets]
    if not todo:
        return dets
    model = YOLO(str(weights or TEACHER))
    assert [model.names[i] for i in range(4)] == CODES, model.names
    t0 = time.time()
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        if tiles == 1:
            res = model.predict([str(OUT / 'frames' / f) for f in chunk], imgsz=imgsz, conf=conf, iou=IOU_THRESHOLD,
                                device=0, verbose=False)
            for f, r in zip(chunk, res):
                dets[f] = [dict(box=tuple(float(v) for v in b.xyxy[0].tolist()), cls=CODES[int(b.cls[0])],
                                conf=float(b.conf[0]), clip=None) for b in r.boxes]
        else:
            for f in chunk:
                im = cv2.imread(str(OUT / 'frames' / f))
                spans = tile_spans(im.shape[1], tiles)
                res = model.predict([im[:, l:r] for l, r in spans], imgsz=imgsz, conf=conf, iou=IOU_THRESHOLD,
                                    device=0, verbose=False)
                xyxy, sc, cl = [], [], []
                for (l, _), r in zip(spans, res):
                    for b in r.boxes:
                        x1, y1, x2, y2 = b.xyxy[0].tolist()
                        xyxy.append([x1 + l, y1, x2 + l, y2]); sc.append(float(b.conf[0])); cl.append(int(b.cls[0]))
                if xyxy:
                    t_xy, t_sc, t_cl = torch.tensor(xyxy), torch.tensor(sc), torch.tensor(cl)
                    keep = torchvision.ops.batched_nms(t_xy, t_sc, t_cl, IOU_THRESHOLD).tolist()
                else:
                    keep = []
                dets[f] = [dict(box=tuple(xyxy[k]), cls=CODES[cl[k]], conf=sc[k], clip=None) for k in keep]
        if (i // batch) % 50 == 0:
            print(f'  {i + len(chunk)}/{len(todo)} frames, {time.time() - t0:.0f} s', flush=True)
            save(imgsz, dets, tiles, tag)
    save(imgsz, dets, tiles, tag)
    return dets


def add_clip(imgsz, frames, want, tiles=1):
    """Score with CLIP every cached box of these frames for which want(box) is true and that has no score yet."""
    from services import damage_verifier
    dets = load(imgsz, tiles)
    man = {m['frame']: m for m in read_csv(OUT / 'manifest.csv')}
    n = 0
    for f in frames:
        boxes = [d for d in dets.get(f, []) if d['clip'] is None and want(d)]
        if not boxes:
            continue
        full = cv2.imread(str(OUT / 'frames_full' / f))
        top = int(man[f]['band_top_px'])
        for d in boxes:
            x1, y1, x2, y2 = d['box']
            s = damage_verifier.score(full, (x1, y1 + top, x2, y2 + top))
            if s is None:
                sys.exit(f'AI check unavailable: {damage_verifier.problem()}')
            d['clip'] = s
            n += 1
        if n and n % 500 < len(boxes):
            save(imgsz, dets, tiles)
    save(imgsz, dets, tiles)
    print(f'  CLIP scored {n} boxes', flush=True)
    return dets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--splits', nargs='+', default=['val'])
    ap.add_argument('--reviewed-only', action='store_true', help='only the frames in review_frames.csv')
    ap.add_argument('--imgsz', nargs='+', type=int, default=[1280])
    ap.add_argument('--conf', type=float, default=0.05)
    a = ap.parse_args()
    rows = [r for r in read_csv(OUT / 'splits.csv') if r['split'] in a.splits and r['dropped_by_location'] == '0']
    if a.reviewed_only:
        sel = {r['frame'] for r in read_csv(OUT / 'review_frames.csv')}
        rows = [r for r in rows if r['frame'] in sel]
    frames = [r['frame'] for r in rows]
    for s in a.imgsz:
        print(f'imgsz {s}: {len(frames)} frames', flush=True)
        dets = detect(frames, s, a.conf)
        print(f'  {sum(len(dets[f]) for f in frames)} boxes at conf >= {a.conf}', flush=True)


if __name__ == '__main__':
    main()

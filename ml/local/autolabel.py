"""Step 2.1: automatic labels for every extracted frame (pseudo-labels for train, drafts for review).

    python ml/local/autolabel.py [--conf 0.25] [--only R01,R02]

1. Detector: the openly licensed RDD2022 checkpoint the system uses as its stand-in
   (ml/models/rdd2022_pretrained.pt; fixed here on purpose, so switching the server to the team's
   model later does not change how these labels were made). It runs on the road-band crop at the
   server's INFERENCE_IMGSZ and IOU_THRESHOLD; boxes below --conf are discarded. Class names are
   mapped with the server's own _classify_damage/_is_pothole_class, so the generic 'crack',
   'block' and 'edge' classes are dropped as the server drops them.
2. AI check: every remaining box is scored with the backend's damage_verifier.score() (CLIP,
   imported, not copied) on the WHOLE upright frame with the box moved into frame coordinates,
   exactly as the server scores a track. Boxes with a score below VERIFY_THRESHOLD (0.60) drop.

Writes data/local/autolabels/<frame>.txt (YOLO: 0 D00, 1 D10, 2 D20, 3 D40, normalised to the
band crop; an empty file = no kept box), per-recording logs in data/local/autolabel_parts/, and
the merged data/local/autolabel_log.csv (one row per box: frame, box, class, detector confidence,
CLIP score, kept or dropped and why).
"""

import argparse
import sys
import time

import cv2

from common import OUT, ROOT, read_csv, write_csv
from services import damage_verifier
from services.video_processor import INFERENCE_IMGSZ, IOU_THRESHOLD, _classify_damage, _is_pothole_class

STANDIN = ROOT / 'ml' / 'models' / 'rdd2022_pretrained.pt'
CODES = ['D00', 'D10', 'D20', 'D40']
LABELS, PARTS = OUT / 'autolabels', OUT / 'autolabel_parts'
FIELDS = ['frame', 'recording', 'x1', 'y1', 'x2', 'y2', 'model_class', 'code', 'det_conf', 'clip_score', 'kept',
          'reason']


def label_recording(model, rid, frames, conf, batch=16):
    rows = []
    for i in range(0, len(frames), batch):
        chunk = frames[i:i + batch]
        results = model.predict([str(OUT / 'frames' / f['frame']) for f in chunk], imgsz=INFERENCE_IMGSZ,
                                conf=conf, iou=IOU_THRESHOLD, device=0, verbose=False)
        for f, res in zip(chunk, results):
            h, w = res.orig_shape
            top_px = int(f['band_top_px'])
            full = None
            lines = []
            for b in res.boxes:
                cls_id, det_conf = int(b.cls[0]), float(b.conf[0])
                name = model.names[cls_id].lower()
                code, _, is_damage = _classify_damage(name, cls_id, model)
                x1, y1, x2, y2 = (float(v) for v in b.xyxy[0].tolist())
                row = dict(frame=f['frame'], recording=rid, x1=round(x1, 1), y1=round(y1, 1), x2=round(x2, 1),
                           y2=round(y2, 1), model_class=name, code=code, det_conf=round(det_conf, 4),
                           clip_score='', kept=0, reason='')
                if not (is_damage or _is_pothole_class(name, cls_id, model)) or code not in CODES:
                    row.update(code='', reason='not one of the four classes')
                else:
                    if full is None:
                        full = cv2.imread(str(OUT / 'frames_full' / f['frame']))
                    s = damage_verifier.score(full, (x1, y1 + top_px, x2, y2 + top_px))
                    row['clip_score'] = '' if s is None else s
                    if s is None:
                        sys.exit(f'AI check unavailable: {damage_verifier.problem()}')
                    if s < damage_verifier.VERIFY_THRESHOLD:
                        row['reason'] = f'AI check below {damage_verifier.VERIFY_THRESHOLD}'
                    else:
                        row.update(kept=1, reason='kept')
                        lines.append(f'{CODES.index(code)} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} '
                                     f'{(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}')
                rows.append(row)
            (LABELS / (f['frame'][:-4] + '.txt')).write_text(''.join(l + '\n' for l in lines))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--conf', type=float, default=0.25, help='minimum detector confidence')
    ap.add_argument('--only', default='', help='comma-separated recording ids to (re)label; default all')
    a = ap.parse_args()
    from ultralytics import YOLO

    if damage_verifier._load(allow_download=False) is None:
        sys.exit(f'AI check unavailable: {damage_verifier.problem()}')
    model = YOLO(str(STANDIN))
    manifest = read_csv(OUT / 'manifest.csv')
    rids = sorted({m['recording'] for m in manifest})
    only = [x.strip() for x in a.only.split(',') if x.strip()] or rids
    LABELS.mkdir(parents=True, exist_ok=True)
    PARTS.mkdir(parents=True, exist_ok=True)
    print(f'Stand-in {STANDIN.name} {model.names}; imgsz {INFERENCE_IMGSZ}, conf {a.conf}, iou {IOU_THRESHOLD}; '
          f'AI check threshold {damage_verifier.VERIFY_THRESHOLD}', flush=True)
    for rid in only:
        t0 = time.time()
        frames = [m for m in manifest if m['recording'] == rid]
        for old in LABELS.glob(f'{rid}_s*.txt'):
            old.unlink()
        rows = label_recording(model, rid, frames, a.conf)
        write_csv(PARTS / f'{rid}.csv', rows or [dict.fromkeys(FIELDS, '')], FIELDS)
        kept = sum(r['kept'] for r in rows)
        print(f'{rid}: {len(frames)} frames, {len(rows)} boxes, {kept} kept, '
              f'{sum(1 for r in rows if r["reason"].startswith("AI"))} dropped by the AI check, '
              f'{sum(1 for r in rows if r["reason"].startswith("not"))} not a target class, '
              f'{time.time() - t0:.0f} s', flush=True)

    # Merge whatever parts exist for the recordings currently in the manifest.
    merged = []
    for rid in rids:
        p = PARTS / f'{rid}.csv'
        if p.exists():
            merged += [r for r in read_csv(p) if r['frame']]
    write_csv(OUT / 'autolabel_log.csv', merged or [dict.fromkeys(FIELDS, '')], FIELDS)
    missing = [rid for rid in rids if not (PARTS / f'{rid}.csv').exists()]
    print(f'\nautolabel_log.csv: {len(merged)} boxes from {len(rids) - len(missing)} recordings'
          + (f'; not labelled yet: {", ".join(missing)}' if missing else ''))
    for c in CODES:
        print(f'  {c}: {sum(1 for r in merged if r["code"] == c and r["kept"] == "1")} kept, '
              f'{sum(1 for r in merged if r["code"] == c and r["kept"] == "0")} dropped by the AI check')


if __name__ == '__main__':
    main()

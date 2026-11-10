"""Draft boxes for the annotation queue (deploy_annotation_site.md §5).

    python tools/review_labels/prelabel.py                       # default weights, every frame without drafts
    python tools/review_labels/prelabel.py --weights runs/v3/S5_v8m_1920/weights/best.pt --imgsz 1920 --all

Runs the model over the queued near-zone frames on the GPU (batched), conf >= 0.15, and
  - writes YOLO txt (class cx cy w h conf) to data/local/annotate/prelabels/,
  - stores the boxes in labels.db as source='model' (only for frames still todo, never over human boxes),
  - sets tier and priority (§4): T1 = any D20 or D10 draft; T2 = max conf in [0.15, 0.5); T3 = the rest.
Default weights: runs/v3/S5_v8m_1280 (highest near-zone val mAP@50 in results/chapter5_val_table_nz.md),
at its training size 1280. Never touches test frames (they are not in the database).
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import annotate_db as adb  # noqa: E402

PRIORITY = {('T1', 'train'): 1, ('T1', 'val'): 2, ('T2', 'train'): 3, ('T2', 'val'): 4,
            ('T3', 'train'): 5, ('T3', 'val'): 5}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--weights', default=str(adb.ROOT / 'runs/v3/S5_v8m_1280/weights/best.pt'))
    ap.add_argument('--imgsz', type=int, default=1280)
    ap.add_argument('--conf', type=float, default=0.15)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--all', action='store_true', help='redo frames that already have drafts')
    a = ap.parse_args()
    from ultralytics import YOLO
    model = YOLO(a.weights)
    names = model.names
    code_of = {k: next((i for i, c in enumerate(adb.CODES) if c in str(v).upper()), None) for k, v in names.items()}
    if None in code_of.values():
        sys.exit(f'model classes {names} do not map onto {adb.CODES}')
    out = adb.ANN / 'prelabels'
    out.mkdir(parents=True, exist_ok=True)
    c = adb.connect()
    todo = [r[0] for r in c.execute("SELECT frame_id FROM frames WHERE status='todo'" +
                                     ('' if a.all else ' AND tier IS NULL') + ' ORDER BY frame_id')]
    split = dict(c.execute('SELECT frame_id, split FROM frames'))
    print(f'{len(todo)} frames, weights {a.weights}, imgsz {a.imgsz}', flush=True)
    t0 = time.time()
    for i in range(0, len(todo), a.batch):
        chunk = todo[i:i + a.batch]
        res = model.predict([str(adb.FRAMES_DIR / f) for f in chunk], imgsz=a.imgsz, conf=a.conf,
                            device=0, half=True, verbose=False)
        rows, meta = [], []
        for f, r in zip(chunk, res):
            bx = r.boxes
            dets = [(code_of[int(k)], *map(float, xywh), float(cf)) for k, xywh, cf in
                    zip(bx.cls.tolist(), bx.xywhn.tolist(), bx.conf.tolist())]
            (out / f'{f[:-4]}.txt').write_text(''.join(f'{k} {x:.6f} {y:.6f} {w:.6f} {h:.6f} {cf:.4f}\n'
                                                       for k, x, y, w, h, cf in dets))
            mx = max((d[5] for d in dets), default=0.0)
            tier = 'T1' if any(d[0] in (1, 2) for d in dets) else 'T2' if 0.15 <= mx < 0.5 else 'T3'
            meta.append((tier, PRIORITY[(tier, split[f])], mx, f))
            rows += [(f, k, x, y, w, h, 'model', cf) for k, x, y, w, h, cf in dets]
        with adb.tx(c):
            ok = {r[0] for r in c.execute(
                f"SELECT frame_id FROM frames WHERE status='todo' AND frame_id IN ({','.join('?' * len(chunk))})", chunk)}
            c.executemany("DELETE FROM boxes WHERE frame_id=? AND source='model'", [(f,) for f in ok])
            c.executemany('INSERT INTO boxes VALUES (?,?,?,?,?,?,?,?)', [r for r in rows if r[0] in ok])
            c.executemany('UPDATE frames SET tier=?, priority=?, max_conf=? WHERE frame_id=?', [m for m in meta if m[3] in ok])
        if (i // a.batch) % 20 == 0:
            n = i + len(chunk)
            print(f'{n}/{len(todo)}  {n / (time.time() - t0):.1f} frames/s', flush=True)
    print(f'done in {(time.time() - t0) / 60:.1f} min')
    adb.status()


if __name__ == '__main__':
    main()

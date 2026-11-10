"""Step 4 (2026-11-10): every candidate starting point, as it is, on the NEAR-ZONE local val set.

    python ml/local/zero_shot.py [--only NAME ...]

Ultralytics validation on data/local/yolo_nz/val.yaml (conf 0.001, NMS IoU 0.7) at imgsz 1280 (our
setting) and 640 (what the external checkpoints were trained at). Class i of every checkpoint is
D00/D10/D20/D40 (results/pretrained_sources.md), so no remapping is needed. Writes
results/zero_shot_nz_val.md. Test is not touched.
"""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / 'data' / 'pretrained'
CANDIDATES = {
    'YOLOv12m (SreekarAditya, RDD2022)': P / 'SreekarAditya__yolo-rdd2022-benchmark' / 'yolo-rdd2022-benchmark' / 'yolo12m_seed0_best.pt',
    'YOLOv12s (SreekarAditya, RDD2022)': P / 'SreekarAditya__yolo-rdd2022-benchmark' / 'yolo-rdd2022-benchmark' / 'yolo12s_seed0_best.pt',
    'YOLOv8m (dronefreak, RDD2022)': P / 'dronefreak__rdd2022-yolov8m' / 'best.pt',
    'YOLOv8m teacher (ours, RDD2022)': ROOT / 'runs' / 'teacher' / 'teacher' / 'weights' / 'best.pt',
    'B v2 (ours, teacher + local; reference)': ROOT / 'runs' / 'v2' / 'Bv2' / 'weights' / 'best.pt',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args()
    from ultralytics import YOLO
    data = ROOT / 'data' / 'local' / 'yolo_nz' / 'val.yaml'
    out = ROOT / 'results' / 'zero_shot_nz_val.md'
    rows = []
    for label, w in CANDIDATES.items():
        if a.only and not any(o in label for o in a.only):
            continue
        for imgsz in (1280, 640):
            try:
                m = YOLO(str(w)).val(data=str(data), imgsz=imgsz, batch=4, workers=2, device=0, split='val',
                                     plots=False, verbose=False, project=str(ROOT / 'runs' / 'eval'),
                                     name=f'zeroshot_{w.parent.name}_{w.stem}_{imgsz}', exist_ok=True)
                ap50 = dict(zip([int(i) for i in m.box.ap_class_index], [float(x) for x in m.box.ap50]))
                rows.append((label, imgsz, float(m.box.map50), [ap50.get(i, 0.0) for i in range(4)], ''))
            except Exception as e:
                rows.append((label, imgsz, float('nan'), [float('nan')] * 4, f'{type(e).__name__}: {str(e)[:100]}'))
            print(rows[-1], flush=True)
    md = ['# Zero-shot: each starting point as it is, on the near-zone local val set', '',
          '270 reviewed frames, 122 boxes (D00 30, D10 23, D20 17, D40 52). Ultralytics validation (conf 0.001, '
          'NMS IoU 0.7). Ranking for step 5 by mAP@50 at 1280.', '',
          '| Checkpoint | imgsz | mAP@50 | D00 | D10 | D20 | D40 | Note |', '|---|---|---|---|---|---|---|---|']
    for label, imgsz, m50, ap, note in sorted(rows, key=lambda r: (r[1] != 1280, -(r[2] if r[2] == r[2] else -1))):
        md.append(f'| {label} | {imgsz} | {m50:.3f} | ' + ' | '.join(f'{x:.3f}' for x in ap) + f' | {note} |')
    out.write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

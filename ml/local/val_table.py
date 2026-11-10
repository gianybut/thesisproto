"""Chapter V table: every run scored the same way on the reviewed LOCAL val set.

    python ml/local/val_table.py

Rows: the teacher (foreign data only), A, Bv1, Bv2, Bv2_freeze10, Bv2_noreplay (whichever exist).
Each run's best.pt is validated with Ultralytics on data/local/yolo/val.yaml at imgsz 1280
(conf 0.001, NMS IoU 0.7): P, R, mAP@50, mAP@50-95, AP@50 per class, lowest class AP@50 (the
tie-breaker for choosing the model). Build the dataset first (build_local_yolo.py), so the val
set is the final, reviewed one. Test is not touched. Writes results/chapter5_val_table.md.
"""

import json

from common import OUT, ROOT

CODES = ['D00', 'D10', 'D20', 'D40']
ROWS = [('Teacher (RDD2022 only)', 'runs/teacher/teacher'), ('A: local only', 'runs/v2/A'),
        ('B v1', 'runs/v2/Bv1'), ('B v2', 'runs/v2/Bv2'), ('B v2, freeze 10', 'runs/v2/Bv2_freeze10'),
        ('B v2, no replay', 'runs/v2/Bv2_noreplay')]


def main():
    from ultralytics import YOLO
    data = OUT / 'yolo' / 'val.yaml'
    n_val = sum(1 for l in (OUT / 'yolo' / 'val.txt').read_text().splitlines() if l.strip())
    out = []
    for label, run in ROWS:
        w = ROOT / run / 'weights' / 'best.pt'
        if not w.exists():
            continue
        m = YOLO(str(w)).val(data=str(data), imgsz=1280, batch=4, workers=2, device=0, split='val', plots=False,
                             project=str(ROOT / 'runs' / 'eval'), name=f'localval_{w.parent.parent.name}', exist_ok=True,
                             verbose=False)
        ap = dict(zip([int(i) for i in m.box.ap_class_index], [float(x) for x in m.box.ap50]))
        info_p = ROOT / run / 'run_info.json'
        hours = json.loads(info_p.read_text()).get('train_seconds_total', 0) / 3600 if info_p.exists() else 0
        out.append((label, float(m.box.mp), float(m.box.mr), float(m.box.map50), float(m.box.map),
                    [ap.get(i, 0.0) for i in range(4)], hours))
        print(label, f'{m.box.map50:.3f}', flush=True)
    md = ['# Local val results of every run (Chapter V)', '',
          f'Reviewed local val set: {n_val} frames. Each run\'s best.pt, Ultralytics validation at imgsz 1280 '
          '(conf 0.001, NMS IoU 0.7). Model choice: highest mAP@50; ties: higher lowest class AP@50.', '',
          '| Run | P | R | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | Lowest class AP@50 | Training h |',
          '|---|---|---|---|---|---|---|---|---|---|---|']
    best = max(out, key=lambda r: (round(r[3], 3), min(r[5]))) if out else None
    for r in out:
        name = f'**{r[0]}**' if r is best else r[0]
        md.append(f'| {name} | {r[1]:.3f} | {r[2]:.3f} | {r[3]:.3f} | {r[4]:.3f} | '
                  + ' | '.join(f'{x:.3f}' for x in r[5]) + f' | {min(r[5]):.3f} | {r[6]:.1f} |')
    if best:
        md.append(f'\nHighest local val mAP@50: **{best[0]}**.')
    (ROOT / 'results' / 'chapter5_val_table.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

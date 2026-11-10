"""Chapter V table for the step-5 runs (plan of 2026-11-10 12:00): near-zone local val.

    python ml/local/val_table_nz.py

Rows: B v2 as it is (reference) and every runs/v3/S5_* run with a best.pt (also one stopped by the
hard stop). Each is validated with Ultralytics on data/local/yolo_nz/val.yaml (270 frames, 122 boxes)
at its own training input size (conf 0.001, NMS IoU 0.7). Columns include how many AL2 frames the run
trained on (from the run's own copy of its training list) and whether it starts from an external
checkpoint. Model choice: highest mAP@50; ties: higher lowest class AP@50. Writes
results/chapter5_val_table_nz.md. Test is not touched.
"""

import json
from pathlib import Path

from common import OUT, ROOT, read_csv

CODES = ['D00', 'D10', 'D20', 'D40']


def main():
    from ultralytics import YOLO
    data = OUT / 'yolo_nz' / 'val.yaml'
    al2 = {r['frame'] for r in read_csv(OUT / 'review_frames.csv') if r.get('batch') == 'AL2'}
    rows = [('B v2 (reference, as it is)', ROOT / 'runs' / 'v2' / 'Bv2', 1280)]
    for d in sorted((ROOT / 'runs' / 'v3').glob('S5_*')):
        if (d / 'weights' / 'best.pt').exists():
            info = json.loads((d / 'run_info.json').read_text())
            rows.append((d.name, d, int(info.get('imgsz', 1280))))
    out = []
    for label, d, imgsz in rows:
        info = json.loads((d / 'run_info.json').read_text()) if (d / 'run_info.json').exists() else {}
        m = YOLO(str(d / 'weights' / 'best.pt')).val(data=str(data), imgsz=imgsz, batch=2 if imgsz > 1280 else 4,
                                                     workers=2, device=0, split='val', plots=False, verbose=False,
                                                     project=str(ROOT / 'runs' / 'eval'), name=f'nzval_{d.name}', exist_ok=True)
        ap = dict(zip([int(i) for i in m.box.ap_class_index], [float(x) for x in m.box.ap50]))
        lst = next((d / 'data').glob('B_train.txt'), None) if (d / 'data').exists() else None
        n_al2 = sum(1 for l in lst.read_text().splitlines() if Path(l).name in al2) if lst else 0
        uniq_al2 = len({Path(l).name for l in lst.read_text().splitlines() if Path(l).name in al2}) if lst else 0
        start = str(info.get('model', ''))
        external = 'data/pretrained' in start.replace('\\', '/')
        status = ('stopped at the hard stop' if info.get('hard_stop') else
                  'finished' if info.get('finished') else 'running/unfinished')
        out.append(dict(label=label, imgsz=imgsz, p=float(m.box.mp), r=float(m.box.mr), m50=float(m.box.map50),
                        m5095=float(m.box.map), ap=[ap.get(i, 0.0) for i in range(4)],
                        hours=info.get('train_seconds_total', 0) / 3600, al2=uniq_al2, al2_lines=n_al2,
                        start=Path(start).parent.parent.name if 'runs' in start else Path(start).stem,
                        external=external, status=status, epochs=len(read_csv(d / 'epochs.csv')) if (d / 'epochs.csv').exists() else 0))
        print(label, f'{m.box.map50:.3f}', flush=True)
    cand = [r for r in out if r['label'].startswith('S5_')]
    best = max(cand, key=lambda r: (round(r['m50'], 3), min(r['ap']))) if cand else None
    md = ['# Near-zone local val results of the step-5 runs (Chapter V)', '',
          'Reviewed near-zone local val set: 270 frames, 122 boxes. Each model\'s best.pt, Ultralytics validation at '
          'its own training input size (conf 0.001, NMS IoU 0.7). Choice: highest mAP@50; ties: higher lowest class '
          'AP@50. "External" = starts from a downloaded checkpoint: its foreign-test results are NOT HELD OUT '
          '(results/pretrained_sources.md).', '',
          '| Run | Starts from | imgsz | AL2 frames | P | R | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | Lowest class AP@50 | Epochs | Training h | Status |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in out:
        name = f'**{r["label"]}**' if r is best else r['label']
        md.append(f'| {name} | {r["start"]}{" (external)" if r["external"] else ""} | {r["imgsz"]} | {r["al2"]} | '
                  f'{r["p"]:.3f} | {r["r"]:.3f} | {r["m50"]:.3f} | {r["m5095"]:.3f} | '
                  + ' | '.join(f'{x:.3f}' for x in r['ap']) + f' | {min(r["ap"]):.3f} | {r["epochs"]} | {r["hours"]:.1f} | {r["status"]} |')
    if best:
        md.append(f'\nHighest near-zone val mAP@50 among the step-5 runs: **{best["label"]}** ({best["m50"]:.3f}).')
    md.append('\nAL2: run 1 (S5_v8m_1280) started before any AL2 frame was reviewed; see results/al2_inclusion.md.')
    (ROOT / 'results' / 'chapter5_val_table_nz.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

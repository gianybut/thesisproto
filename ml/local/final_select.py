"""Final model choice (deadline day, 2026-11-11): every candidate and every fusion of 2-3 of them.

    python ml/local/final_select.py v1:1024 v2b:1024 v3:1280 v3b:1280 [--border 24] [--device cpu]

Each candidate is RUN:IMGSZ (runs/local/<RUN>/weights/best.pt, or NAME=path:IMGSZ for other weights).
One prediction pass per candidate over all 1,624 near-zone val frames (cached in
runs/eval/sweep/<RUN>/full_<imgsz>_p<border>_t0.json by infer_sweep.run: conf 0.001, NMS IoU 0.7, grey
border as the app adds it), then mAP@50 / mAP@50-95 (Ultralytics' AP, eval_val_sets.metrics) of every
single model and of the weighted box fusion (backend/services/box_fusion.py, the app's code) of every
pair and triple, on:

    reviewed  the 270 single-reviewer frames: THE SELECTION SET (team decision)
    full      all 1,624 val frames: second column (S5-lineage models are favoured on it, see
              results/val_sets_comparison.md)

Rows are sorted by mAP@50 on reviewed. Writes results/final_selection.md. Test is not touched.
"""

import argparse
import itertools
import json
import sys
from datetime import datetime
from pathlib import Path

from common import ROOT
from eval_val_sets import CODES, SETS, YDIR, frames, metrics
from infer_sweep import OUT, run

sys.path.insert(0, str(ROOT / 'backend' / 'services'))
from box_fusion import fuse  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('candidates', nargs='+', help='RUN:IMGSZ or NAME=weights/path.pt:IMGSZ')
    ap.add_argument('--border', type=int, default=24)
    ap.add_argument('--device', default='0')
    ap.add_argument('--max-size', type=int, default=3, help='largest fusion (number of models)')
    a = ap.parse_args()
    stems = {k: frames(v) for k, v in SETS.items()}
    paths = {}
    for l in (YDIR / 'val.txt').read_text().splitlines():
        if l.strip():
            p = Path(l.strip())
            paths[p.stem] = str(p if p.is_absolute() else YDIR / p)
    dets, info = {}, {}
    for c in a.candidates:
        spec, _, sz = c.rpartition(':')
        name, _, w = spec.partition('=')
        w = ROOT / (w or f'runs/local/{name}/weights/best.pt')
        cache = OUT / name / f'full_{sz}_p{a.border}_t0.json'
        if not cache.exists():
            from ultralytics import YOLO
            print(f'predicting {name} at {sz} ...', flush=True)
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(run(YOLO(str(w)), stems['full'], paths, int(sz), a.border, 0, a.device)))
        dets[name] = json.loads(cache.read_text())
        info[name] = (w.relative_to(ROOT).as_posix(), int(sz))
    rows = []
    for n in range(1, min(a.max_size, len(dets)) + 1):
        for combo in itertools.combinations(dets, n):
            if n == 1:
                d = dets[combo[0]]
            else:
                d = {s: {'wh': dets[combo[0]][s]['wh'], 'pred': fuse([dets[k][s]['pred'] for k in combo])} for s in stems['full']}
            rows.append((' + '.join(combo), metrics(d, stems['reviewed']), metrics(d, stems['full'])))
            print(f'{rows[-1][0]:40} reviewed {rows[-1][1]["m50"]:.3f}  full {rows[-1][2]["m50"]:.3f}', flush=True)
    rows.sort(key=lambda r: -r[1]['m50'])
    md = ['# Final model choice: single models and fusions on near-zone val', '',
          f'{datetime.now():%Y-%m-%d %H:%M}. Each model at its training size with a {a.border} px grey border above and below the '
          'crop (as the app now adds it), conf 0.001, NMS IoU 0.7; fusion = weighted box fusion '
          '(`backend/services/box_fusion.py`). **Selection set: the 270 reviewed frames** (122 boxes); full val '
          '(1,624 frames, 659 boxes) is the second column. Test is not touched.', '',
          'Candidates: ' + '; '.join(f'**{k}** = `{w}` at {sz}' for k, (w, sz) in info.items()) + '.', '',
          '| Model(s) | mAP@50 reviewed | mAP@50-95 reviewed | D00 | D10 | D20 | D40 | mAP@50 full | mAP@50-95 full |',
          '|---|---|---|---|---|---|---|---|---|']
    for name, r, f in rows:
        md.append(f'| {name} | {r["m50"]:.3f} | {r["m5095"]:.3f} | ' + ' | '.join(f'{x:.3f}' for x in r['ap50'])
                  + f' | {f["m50"]:.3f} | {f["m5095"]:.3f} |')
    (ROOT / 'results' / 'final_selection.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

"""Every candidate .pt, as it is, on the NEAR-ZONE local val set (2026-11-10).

    python ml/local/bench_weights.py [--only TEXT ...] [--sizes 640 960 1280] [--fresh]

Candidates: all 29 SreekarAditya RDD2022 benchmark weights in yolo-rdd2022/ (CC BY 4.0), our own
runs (teacher, A, Bv1, Bv2, S5_*), dronefreak's YOLOv8m, and the demo placeholder in ml/models/best.pt
(7 classes; its head is cut to longitudinal/transverse/alligator/pothole = D00/D10/D20/D40, the classes
the backend keeps). Same protocol as zero_shot.py: Ultralytics validation on data/local/yolo_nz/val.yaml
(conf 0.001, NMS IoU 0.7). YOLOv10s is run twice: its NMS-free head as shipped and with standard NMS.

Besides mAP it reports what matters for the app: the best mean F1 over the confidence range (and that
confidence), and precision / recall at the app's CONF_THRESHOLD (0.15). Results are cached per run in
runs/eval/bench_weights.json so an interrupted benchmark resumes. Writes results/weights_benchmark_nz_val.md
and .csv. Test is not touched. Choice rule as elsewhere: mAP@50 at 1280 (the app's INFERENCE_IMGSZ).
"""

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'local' / 'yolo_nz' / 'val.yaml'
CACHE = ROOT / 'runs' / 'eval' / 'bench_weights.json'
OUT = ROOT / 'results' / 'weights_benchmark_nz_val'
APP_CONF = 0.15
P = ROOT / 'data' / 'pretrained'


def candidates():
    c = {}
    for w in sorted((ROOT / 'yolo-rdd2022').glob('*.pt')):
        c[f'SA {w.stem.replace("_best", "")}'] = (w, 'SreekarAditya RDD2022 (external)')
    for run in ('teacher/teacher', 'v2/A', 'v2/Bv1', 'v2/Bv2', 'v3/S5_v8m_1280', 'v3/S5_v8m_1920'):
        w = ROOT / 'runs' / run / 'weights' / 'best.pt'
        if w.exists():
            c[f'ours {run.split("/")[-1]}'] = (w, 'ours')
    c['dronefreak yolov8m'] = (P / 'dronefreak__rdd2022-yolov8m' / 'best.pt', 'dronefreak RDD2022 (external)')
    c['placeholder ml/models/best.pt (7-class)'] = (ROOT / 'ml' / 'models' / 'best.pt', 'demo placeholder (external)')
    return c


def to_four_classes(model):
    """Cut a multi-class head down to D00/D10/D20/D40 by class name; no-op for 4-class models."""
    import torch.nn as nn
    names = model.names
    if len(names) == 4:
        return model
    want = [('longitudinal',), ('transverse',), ('alligator',), ('pothole',)]
    keep = []
    for keys in want:
        hit = [i for i, n in names.items() if any(k in n.lower() for k in keys)]
        if len(hit) != 1:
            raise ValueError(f'cannot map {keys} in {names}')
        keep.append(hit[0])
    det = model.model.model[-1]
    for seq in det.cv3:
        conv = seq[-1]
        new = nn.Conv2d(conv.in_channels, len(keep), 1, bias=True)
        new.weight.data = conv.weight.data[keep].clone()
        new.bias.data = conv.bias.data[keep].clone()
        seq[-1] = new
    det.nc = len(keep)
    det.no = det.nc + det.reg_max * 4
    model.model.nc = det.nc
    model.model.names = {i: n for i, n in enumerate(['D00', 'D10', 'D20', 'D40'])}
    if isinstance(getattr(model.model, 'yaml', None), dict):
        model.model.yaml['nc'] = det.nc
    return model


def evaluate(w, imgsz, end2end=None):
    from ultralytics import YOLO
    model = to_four_classes(YOLO(str(w)))
    kw = {} if end2end is None else {'end2end': end2end}
    m = model.val(data=str(DATA), imgsz=imgsz, batch=4, workers=2, device=0, split='val', plots=False,
                  verbose=False, project=str(ROOT / 'runs' / 'eval'), name='bench_weights', exist_ok=True, **kw)
    b = m.box
    ap50 = dict(zip([int(i) for i in b.ap_class_index], [float(x) for x in b.ap50]))
    f1 = b.f1_curve.mean(0)
    p, r = b.p_curve.mean(0), b.r_curve.mean(0)
    px = b.px if hasattr(b, 'px') else None
    import numpy as np
    x = np.asarray(px) if px is not None else np.linspace(0, 1, 1000)
    i_best = int(f1.argmax())
    i_app = int(np.abs(x - APP_CONF).argmin())
    return {
        'map50': float(b.map50), 'map': float(b.map), 'P': float(b.mp), 'R': float(b.mr),
        'ap50': [ap50.get(i, 0.0) for i in range(4)],
        'f1_best': float(f1[i_best]), 'conf_best': float(x[i_best]),
        'f1_app': float(f1[i_app]), 'P_app': float(p[i_app]), 'R_app': float(r[i_app]),
        'ms': float(m.speed.get('inference', float('nan'))),
    }


def family(label):
    s = re.sub(r'_seed\d+', '', label)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--sizes', nargs='*', type=int, default=[1280, 960, 640])
    ap.add_argument('--fresh', action='store_true')
    a = ap.parse_args()
    cache = {} if a.fresh or not CACHE.exists() else json.loads(CACHE.read_text(encoding='utf-8'))
    CACHE.parent.mkdir(parents=True, exist_ok=True)

    jobs = []
    for label, (w, src) in candidates().items():
        if a.only and not any(o in label for o in a.only):
            continue
        variants = [(label, None)]
        if 'yolov10' in w.name:
            variants = [(label + ' (NMS-free)', None), (label + ' (+NMS)', False)]
        for lab, e2e in variants:
            for s in a.sizes:
                jobs.append((lab, src, w, s, e2e))

    for n, (lab, src, w, s, e2e) in enumerate(jobs, 1):
        key = f'{lab}|{s}'
        if key in cache and 'map50' in cache[key]:
            continue
        try:
            res = evaluate(w, s, e2e)
        except Exception as ex:  # noqa: BLE001
            res = {'error': f'{type(ex).__name__}: {str(ex)[:160]}'}
        cache[key] = {'label': lab, 'source': src, 'weights': str(w.relative_to(ROOT)), 'imgsz': s, **res}
        CACHE.write_text(json.dumps(cache, indent=1), encoding='utf-8')
        print(f'[{n}/{len(jobs)}] {key}: ' + (f"mAP50 {res['map50']:.3f}" if 'map50' in res else res['error']), flush=True)

    write_report(cache)


def write_report(cache):
    rows = [v for v in cache.values() if 'map50' in v]
    errs = [v for v in cache.values() if 'error' in v]
    with open(OUT.with_suffix('.csv'), 'w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['label', 'source', 'weights', 'imgsz', 'P', 'R', 'mAP50', 'mAP50-95', 'AP50_D00', 'AP50_D10',
                     'AP50_D20', 'AP50_D40', 'F1_best', 'conf_at_F1_best', 'F1_at_0.15', 'P_at_0.15', 'R_at_0.15',
                     'inference_ms'])
        for v in sorted(rows, key=lambda v: (-v['imgsz'], -v['map50'])):
            wr.writerow([v['label'], v['source'], v['weights'], v['imgsz'], *(round(x, 4) for x in (
                v['P'], v['R'], v['map50'], v['map'], *v['ap50'], v['f1_best'], v['conf_best'], v['f1_app'],
                v['P_app'], v['R_app'], v['ms']))])

    def line(v):
        return (f"| {v['label']} | {v['imgsz']} | {v['map50']:.3f} | {v['map']:.3f} | "
                + ' | '.join(f'{x:.3f}' for x in v['ap50'])
                + f" | {min(v['ap50']):.3f} | {v['f1_best']:.3f} @ {v['conf_best']:.2f} | {v['P_app']:.3f} | "
                  f"{v['R_app']:.3f} | {v['ms']:.1f} |")

    head = ['| Checkpoint | imgsz | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | Lowest class | Best F1 @ conf | '
            f'P @ {APP_CONF} | R @ {APP_CONF} | ms/img |', '|---' * 13 + '|']
    md = ['# Every candidate checkpoint on the near-zone local val set', '',
          '270 reviewed frames, 122 boxes (D00 30, D10 23, D20 17, D40 52). Ultralytics validation (conf 0.001, '
          'NMS IoU 0.7), no training: each checkpoint as it is. Choice rule: mAP@50 at 1280, the app\'s '
          'INFERENCE_IMGSZ; ties: higher lowest-class AP@50. "SA" = SreekarAditya yolo-rdd2022-benchmark (CC BY 4.0). '
          'External checkpoints saw RDD2022 images that may be in our foreign splits (results/pretrained_sources.md); '
          'the local val set is unaffected. Written by ml/local/bench_weights.py.', '']
    for s in sorted({v['imgsz'] for v in rows}, reverse=True):
        md += [f'## imgsz {s}', ''] + head
        md += [line(v) for v in sorted((v for v in rows if v['imgsz'] == s), key=lambda v: -v['map50'])] + ['']

    # Seed-averaged view at each size (3 seeds where available)
    md += ['## Seed means (SreekarAditya families with more than one seed)', '',
           '| Family | imgsz | seeds | mAP@50 mean | min | max | D40 mean |', '|---|---|---|---|---|---|---|']
    fams = {}
    for v in rows:
        fams.setdefault((family(v['label']), v['imgsz']), []).append(v)
    for (fam, s), vs in sorted(fams.items(), key=lambda kv: (-kv[0][1], -sum(x['map50'] for x in kv[1]) / len(kv[1]))):
        if len(vs) < 2:
            continue
        m = [x['map50'] for x in vs]
        d40 = sum(x['ap50'][3] for x in vs) / len(vs)
        md.append(f'| {fam} | {s} | {len(vs)} | {sum(m) / len(m):.3f} | {min(m):.3f} | {max(m):.3f} | {d40:.3f} |')
    if errs:
        md += ['', '## Not evaluated', ''] + [f"- {v['label']} @ {v['imgsz']}: {v['error']}" for v in errs]
    OUT.with_suffix('.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(f'wrote {OUT.with_suffix(".md")}')


if __name__ == '__main__':
    main()

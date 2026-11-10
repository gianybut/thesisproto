"""Largest fixed batch that fits a model at an input size on this GPU (for a run's settings).

    python ml/local/bench_batch.py --model <weights.pt> --imgsz 1024 --batches 8 12 16

Each batch in its own process: one short epoch (4% of data/local/yolo_nz/v1.yaml's training list,
SGD, the AUG of ml/train_run.py, AMP, no validation), then the peak GPU memory (torch max reserved)
and seconds per image. Above about 7.6 GiB the Windows driver spills into shared system memory and
training gets several times slower, so such a batch does not "fit". Writes nothing into runs/;
appends to results/bench_batch.md.
"""

import argparse
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'local' / 'yolo_nz' / 'v1.yaml'
LIMIT_GIB = 7.6


def one(model, imgsz, batch):
    import torch
    sys.path.insert(0, str(ROOT / 'ml'))
    from train_run import AUG
    from ultralytics import YOLO
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        tr = YOLO(model).train(data=str(DATA), imgsz=imgsz, batch=batch, epochs=1, fraction=0.04, val=False,
                               workers=2, device=0, optimizer='SGD', lr0=0.001, plots=False, verbose=False,
                               project=tmp, name='b', exist_ok=True, **AUG)
        n = len(tr.train_loader.dataset) if tr and hasattr(tr, 'train_loader') else None
    dt = time.time() - t0
    print('BENCH ' + json.dumps({'gib': torch.cuda.max_memory_reserved() / 2**30, 'seconds': dt, 'images': n}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--imgsz', type=int, required=True)
    ap.add_argument('--batches', type=int, nargs='+', required=True)
    ap.add_argument('--one', type=int, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.one:
        return one(a.model, a.imgsz, a.one)
    rows = []
    for b in a.batches:
        out = subprocess.run([sys.executable, __file__, '--model', a.model, '--imgsz', str(a.imgsz), '--batches', str(b),
                              '--one', str(b)], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        line = next((l for l in out.stdout.splitlines() if l.startswith('BENCH ')), None)
        r = json.loads(line[6:]) if line else {'error': (out.stderr.strip().splitlines() or ['?'])[-1][:120]}
        rows.append((b, r))
        print(b, r, flush=True)
    md = [f'## {Path(a.model).name} at imgsz {a.imgsz} ({datetime.now():%Y-%m-%d %H:%M})', '',
          '| Batch | Peak GPU memory (GiB) | Fits (< 7.6 GiB) | Seconds (short epoch) |', '|---|---|---|---|']
    for b, r in rows:
        if 'error' in r:
            md.append(f'| {b} | failed: {r["error"]} | no | |')
        else:
            md.append(f'| {b} | {r["gib"]:.2f} | {"yes" if r["gib"] < LIMIT_GIB else "no"} | {r["seconds"]:.0f} |')
    p = ROOT / 'results' / 'bench_batch.md'
    head = '' if p.exists() else ('# Batch size that fits (bench_batch.py)\n\nOne short epoch per batch, peak torch '
                                  'reserved memory; above 7.6 GiB the Windows driver spills into shared memory.\n\n')
    with open(p, 'a', encoding='utf-8') as f:
        f.write(head + '\n'.join(md) + '\n\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

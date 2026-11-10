"""Time and GPU memory of a training step at larger input sizes, for planning step 5 (2026-11-10).

    python ml/local/bench_sizes.py

For each architecture (from its Ultralytics yaml, so no downloaded weights are loaded) and input
size: one short epoch on 15% of the near-zone B training list (data/local/yolo_nz/B.yaml) with the
step-5 settings (AdamW, mosaic, AMP), no validation. Reports seconds per image and the peak GPU memory
(torch max reserved). Above about 7.6 GiB the Windows driver spills into shared system memory, which
makes training several times slower, so such a size does not "fit". Writes results/bench_sizes.md.
"""

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'local' / 'yolo_nz' / 'B.yaml'
CASES = [('yolo12s.yaml', 1280, 2), ('yolo12s.yaml', 1280, 1), ('yolo12s.yaml', 1024, 2)]
FRACTION = 0.06


def main():
    import torch
    from ultralytics import YOLO
    rows = []
    for arch, imgsz, batch in CASES:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        name = f'{arch[:-5]}_{imgsz}_b{batch}'
        t0 = time.time()
        m = None
        try:
            m = YOLO(arch)
            stamps = []
            m.add_callback('on_train_batch_end', lambda tr: stamps.append(time.time()))
            m.train(data=str(DATA), imgsz=imgsz, batch=batch, epochs=1, fraction=FRACTION, val=False, plots=False,
                    workers=2, device=0, amp=True, optimizer='AdamW', lr0=0.0005, cos_lr=True, seed=42,
                    project=str(ROOT / 'runs' / 'bench_nz'), name=name, exist_ok=True, verbose=False)
            secs = time.time() - t0
            steady = stamps[10:]                      # skip warm-up batches
            spi = (steady[-1] - steady[0]) / ((len(steady) - 1) * batch) if len(steady) > 2 else secs / (len(stamps) * batch)
            peak = torch.cuda.max_memory_reserved(0) / 2 ** 30
            rows.append((arch[:-5], imgsz, batch, len(stamps) * batch, secs, spi, peak, 'ok'))
        except Exception as e:
            rows.append((arch[:-5], imgsz, batch, 0, time.time() - t0, 0, torch.cuda.max_memory_reserved(0) / 2 ** 30,
                         f'{type(e).__name__}: {str(e)[:80]}'))
        print(rows[-1], flush=True)
        del m
    md = ['# Training speed and GPU memory at larger input sizes (near-zone data)', '',
          f'One epoch on {FRACTION:.0%} of the near-zone B list (AdamW, AMP, mosaic), no validation; s/image from the batches after the first 10 (no start-up). '
          'Fits = peak reserved memory under about 7.6 GiB of the 8 GiB card.', '',
          '| Model | imgsz | Batch | Images | s/image | Peak GiB | Fits | Result |', '|---|---|---|---|---|---|---|---|']
    for a, i, b, n, s, spi, pk, res in rows:
        md.append(f'| {a} | {i} | {b} | {n} | {spi:.3f} | {pk:.2f} | {"yes" if pk < 7.6 and res == "ok" else "no"} | {res} |')
    (ROOT / 'results' / 'bench_sizes_part2.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

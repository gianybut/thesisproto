# Batch size that fits (bench_batch.py)

One short epoch per batch, peak torch reserved memory; above 7.6 GiB the Windows driver spills into shared memory.

## yolov8s_seed0_best.pt at imgsz 1024 (2026-11-11 07:53)

| Batch | Peak GPU memory (GiB) | Fits (< 7.6 GiB) | Seconds (short epoch) |
|---|---|---|---|
| 8 | 4.54 | yes | 44 |
| 12 | 6.42 | yes | 40 |
| 16 | 8.84 | no | 68 |


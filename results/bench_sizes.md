# Training speed and GPU memory at larger input sizes (near-zone data, 2026-11-10)

`ml/local/bench_sizes.py`: one short epoch (15% or 6% of the near-zone B list) with the step-5
settings (AdamW, AMP, mosaic), no validation; seconds per image from the batches after the first 10.
RTX 4060 8 GiB under Windows: above about 7.6 GiB the driver spills into shared system memory and
training becomes many times slower, so such a size does not fit. Architectures were built from the
Ultralytics yaml (same size and speed as the pretrained checkpoints).

| Model | imgsz | Batch | s/image | Peak GiB | Fits | Note |
|---|---|---|---|---|---|---|
| YOLOv8m | 1280 | 4 | 0.101 | 6.20 | yes | |
| YOLOv8m | 1600 | 2 | 0.155 | 5.30 | yes | |
| YOLOv8m | 1920 | 2 | 0.239 | 7.14 | yes (close to the limit) | |
| YOLOv12m | 1280 | 4 | 1.84 | 13.9 | no | out of memory, Ultralytics retried at batch 2 and spilled |
| YOLOv12m | 1280 | 2 | 3.20 | 11.1 | no | spills into system memory |
| YOLOv12m | 1600 | 1 | (about 5.7 s per step) | 11.9 | no | stopped |
| YOLOv12s | 1280 | 4 | (12.9 s per step) | 12.6 | no | stopped |
| YOLOv12s | 1280 | 2 | 0.242 | 6.43 | yes | 2.4x the time of YOLOv8m at 1280 |
| YOLOv12s | 1280 | 1 | 0.169 | 3.35 | yes | batch 1: batch-norm statistics from one image |
| YOLOv12s | 1024 | 2 | 0.163 | 3.20 | yes | |

YOLOv12's attention layers grow quickly with the input size and this Windows install has no flash
attention, so YOLOv12 above 1280 does not fit; YOLOv8m is the only candidate that fits at 1600/1920.

## Time per run (step 5: 1,414 images per epoch + 270 val frames; 60 epochs, patience 15)

| Run | Minutes per epoch | 60 epochs (upper bound) | Typical with early stopping (~45 epochs) |
|---|---|---|---|
| YOLOv8m from B v2, 1280, batch 4 | 2.7 | 2.7 h | ~2.0 h |
| YOLOv8m from B v2, 1600, batch 2 | 4.2 | 4.2 h | ~3.1 h |
| YOLOv8m from B v2, 1920, batch 2 | 6.4 | 6.4 h | ~4.8 h |
| YOLOv12s (RDD2022), 1280, batch 2 | 6.4 | 6.4 h | ~4.8 h |
| YOLOv12s (RDD2022), 1024, batch 2 | 4.3 | 4.3 h | ~3.2 h |

With the AL2 frames added (300 frames, about half with D10/D20/D40, so about +600 images per epoch)
every run takes about 1.4x as long.

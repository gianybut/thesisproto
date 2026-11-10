# Training speed and GPU memory at larger input sizes (near-zone data)

One epoch on 6% of the near-zone B list (AdamW, AMP, mosaic), no validation; s/image from the batches after the first 10 (no start-up). Fits = peak reserved memory under about 7.6 GiB of the 8 GiB card.

| Model | imgsz | Batch | Images | s/image | Peak GiB | Fits | Result |
|---|---|---|---|---|---|---|---|
| yolo12s | 1280 | 2 | 86 | 0.242 | 6.43 | yes | ok |
| yolo12s | 1280 | 1 | 85 | 0.169 | 3.35 | yes | ok |
| yolo12s | 1024 | 2 | 86 | 0.163 | 3.20 | yes | ok |

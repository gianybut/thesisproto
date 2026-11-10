# Label / crop alignment check

Every local image in data/local/yolo: size = review state = extractor crop (approved band); same picture as the review tool showed; label file = reviewed boxes; boxes inside the image.

| Split | Images | Boxes |
|---|---|---|
| train | 526 | 419 |
| val | 270 | 122 |
| test | 270 | 99 |

**Problems: 0**


Overlay: `results/val_alignment_overlay.jpg` (12 val frames: R05_s0201.jpg, R05_s0155.jpg, R05_s0459.jpg, R05_s0520.jpg, R16_s0183.jpg, R05_s0354.jpg, R05_s0145.jpg, R05_s0508.jpg, R05_s0554.jpg, R05_s0588.jpg, R05_s0226.jpg, R07_s0054.jpg). Top: full video frame, road band (cyan), labels mapped back (green). Bottom: training crop, label file (green) and review state (magenta).

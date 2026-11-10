# Near-zone local val results of the step-5 runs (Chapter V)

Reviewed near-zone local val set: 270 frames, 122 boxes. Each model's best.pt, Ultralytics validation at its own training input size (conf 0.001, NMS IoU 0.7). Choice: highest mAP@50; ties: higher lowest class AP@50. "External" = starts from a downloaded checkpoint: its foreign-test results are NOT HELD OUT (results/pretrained_sources.md).

| Run | Starts from | imgsz | AL2 frames | P | R | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | Lowest class AP@50 | Epochs | Training h | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B v2 (reference, as it is) | teacher | 1280 | 0 | 0.193 | 0.268 | 0.164 | 0.068 | 0.296 | 0.136 | 0.012 | 0.212 | 0.012 | 27 | 1.0 | finished |
| **S5_v8m_1280** | Bv2 | 1280 | 0 | 0.209 | 0.240 | 0.185 | 0.070 | 0.350 | 0.218 | 0.012 | 0.160 | 0.012 | 19 | 0.7 | finished |

Highest near-zone val mAP@50 among the step-5 runs: **S5_v8m_1280** (0.185).

AL2: run 1 (S5_v8m_1280) started before any AL2 frame was reviewed; see results/al2_inclusion.md.

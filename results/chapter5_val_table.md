# Local val results of every run (Chapter V)

Reviewed local val set: 270 frames. Each run's best.pt, Ultralytics validation at imgsz 1280 (conf 0.001, NMS IoU 0.7). Model choice: highest mAP@50; ties: higher lowest class AP@50.

| Run | P | R | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | Lowest class AP@50 | Training h |
|---|---|---|---|---|---|---|---|---|---|---|
| Teacher (RDD2022 only) | 0.110 | 0.167 | 0.087 | 0.033 | 0.236 | 0.023 | 0.013 | 0.077 | 0.013 | 2.4 |
| A: local only | 0.703 | 0.095 | 0.100 | 0.048 | 0.305 | 0.031 | 0.003 | 0.062 | 0.003 | 0.3 |
| B v1 | 0.192 | 0.237 | 0.140 | 0.056 | 0.239 | 0.108 | 0.025 | 0.187 | 0.025 | 0.9 |
| **B v2** | 0.203 | 0.214 | 0.167 | 0.075 | 0.274 | 0.143 | 0.015 | 0.236 | 0.015 | 1.0 |

Highest local val mAP@50: **B v2**.

# final_v3: foreign (RDD2022) test, full split

Weights `ml/models/oculubak_v3.pt`, imgsz 1280. Test = 15% of each country (seed 42), never used for training. Standard Ultralytics validation (conf 0.001, NMS IoU 0.7).

| Test set | Images | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |
|---|---|---|---|---|---|---|---|---|---|
| **all six countries** | 3277 | 0.337 | 0.305 | 0.239 | 0.084 | 0.330 | 0.242 | 0.230 | 0.154 |
| Japan | 1185 | 0.277 | 0.263 | 0.177 | 0.061 | 0.139 | 0.162 | 0.235 | 0.173 |
| India | 483 | 0.226 | 0.201 | 0.155 | 0.052 | 0.146 | 0.007 | 0.285 | 0.182 |
| Czech | 161 | 0.201 | 0.258 | 0.151 | 0.048 | 0.287 | 0.104 | 0.085 | 0.128 |
| Norway | 437 | 0.296 | 0.220 | 0.182 | 0.065 | 0.316 | 0.163 | 0.088 | 0.161 |
| United_States | 721 | 0.371 | 0.418 | 0.360 | 0.151 | 0.535 | 0.424 | 0.391 | 0.091 |
| China_MotorBike | 290 | 0.315 | 0.354 | 0.284 | 0.087 | 0.239 | 0.283 | 0.278 | 0.337 |

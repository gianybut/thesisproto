# final_S5_v8m_1920: foreign (RDD2022) test, full split

Weights `ml/models/oculubak_S5_v8m_1920.pt`, imgsz 1280. Test = 15% of each country (seed 42), never used for training. Standard Ultralytics validation (conf 0.001, NMS IoU 0.7).

| Test set | Images | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |
|---|---|---|---|---|---|---|---|---|---|
| **all six countries** | 3277 | 0.411 | 0.369 | 0.318 | 0.127 | 0.406 | 0.284 | 0.328 | 0.254 |
| Japan | 1185 | 0.394 | 0.352 | 0.312 | 0.122 | 0.314 | 0.289 | 0.349 | 0.295 |
| India | 483 | 0.249 | 0.231 | 0.180 | 0.066 | 0.158 | 0.003 | 0.330 | 0.229 |
| Czech | 161 | 0.326 | 0.267 | 0.247 | 0.079 | 0.397 | 0.258 | 0.117 | 0.216 |
| Norway | 437 | 0.382 | 0.237 | 0.216 | 0.084 | 0.363 | 0.199 | 0.101 | 0.200 |
| United_States | 721 | 0.446 | 0.439 | 0.429 | 0.205 | 0.620 | 0.431 | 0.357 | 0.306 |
| China_MotorBike | 290 | 0.422 | 0.363 | 0.340 | 0.117 | 0.296 | 0.338 | 0.339 | 0.388 |

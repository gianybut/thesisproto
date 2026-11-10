# teacher: foreign (RDD2022) val, full split

Weights `runs/teacher/teacher/weights/best.pt`, imgsz 960. Val = 15% of each country (seed 42), never used for training. Standard Ultralytics validation (conf 0.001, NMS IoU 0.7).

| Val set | Images | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |
|---|---|---|---|---|---|---|---|---|---|
| **all six countries** | 3277 | 0.529 | 0.471 | 0.472 | 0.223 | 0.535 | 0.430 | 0.544 | 0.379 |
| Japan | 1185 | 0.499 | 0.446 | 0.438 | 0.190 | 0.447 | 0.353 | 0.567 | 0.386 |
| India | 484 | 0.477 | 0.327 | 0.344 | 0.133 | 0.335 | 0.205 | 0.498 | 0.339 |
| Czech | 161 | 0.418 | 0.432 | 0.420 | 0.180 | 0.583 | 0.438 | 0.406 | 0.253 |
| Norway | 437 | 0.394 | 0.312 | 0.274 | 0.115 | 0.419 | 0.284 | 0.132 | 0.264 |
| United_States | 720 | 0.474 | 0.562 | 0.515 | 0.269 | 0.699 | 0.532 | 0.550 | 0.280 |
| China_MotorBike | 290 | 0.810 | 0.761 | 0.812 | 0.471 | 0.740 | 0.741 | 0.815 | 0.951 |

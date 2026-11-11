# final_v2b: foreign (RDD2022) test, full split

Weights `ml/models/oculubak_v2b.pt`, imgsz 1024. Test = 15% of each country (seed 42), never used for training. Standard Ultralytics validation (conf 0.001, NMS IoU 0.7).

| Test set | Images | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |
|---|---|---|---|---|---|---|---|---|---|
| **all six countries** | 3277 | 0.323 | 0.269 | 0.200 | 0.068 | 0.290 | 0.179 | 0.190 | 0.143 |
| Japan | 1185 | 0.229 | 0.242 | 0.145 | 0.046 | 0.152 | 0.124 | 0.181 | 0.123 |
| India | 483 | 0.272 | 0.195 | 0.171 | 0.058 | 0.207 | 0.009 | 0.203 | 0.267 |
| Czech | 161 | 0.220 | 0.312 | 0.190 | 0.057 | 0.291 | 0.104 | 0.163 | 0.202 |
| Norway | 437 | 0.353 | 0.160 | 0.131 | 0.039 | 0.232 | 0.085 | 0.159 | 0.048 |
| United_States | 721 | 0.381 | 0.454 | 0.361 | 0.145 | 0.534 | 0.355 | 0.457 | 0.097 |
| China_MotorBike | 290 | 0.369 | 0.140 | 0.131 | 0.040 | 0.110 | 0.085 | 0.030 | 0.300 |

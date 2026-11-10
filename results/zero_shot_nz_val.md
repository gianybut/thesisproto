# Zero-shot: each starting point as it is, on the near-zone local val set

270 reviewed frames, 122 boxes (D00 30, D10 23, D20 17, D40 52). Ultralytics validation (conf 0.001, NMS IoU 0.7). Ranking for step 5 by mAP@50 at 1280.

| Checkpoint | imgsz | mAP@50 | D00 | D10 | D20 | D40 | Note |
|---|---|---|---|---|---|---|---|
| B v2 (ours, teacher + local; reference) | 1280 | 0.164 | 0.296 | 0.136 | 0.012 | 0.212 |  |
| YOLOv12s (SreekarAditya, RDD2022) | 1280 | 0.156 | 0.338 | 0.051 | 0.012 | 0.222 |  |
| YOLOv12m (SreekarAditya, RDD2022) | 1280 | 0.138 | 0.309 | 0.040 | 0.002 | 0.200 |  |
| YOLOv8m teacher (ours, RDD2022) | 1280 | 0.090 | 0.224 | 0.017 | 0.014 | 0.105 |  |
| YOLOv8m (dronefreak, RDD2022) | 1280 | 0.086 | 0.273 | 0.059 | 0.011 | 0.001 |  |
| YOLOv12s (SreekarAditya, RDD2022) | 640 | 0.111 | 0.170 | 0.054 | 0.022 | 0.198 |  |
| B v2 (ours, teacher + local; reference) | 640 | 0.100 | 0.216 | 0.046 | 0.004 | 0.133 |  |
| YOLOv12m (SreekarAditya, RDD2022) | 640 | 0.089 | 0.127 | 0.064 | 0.006 | 0.158 |  |
| YOLOv8m (dronefreak, RDD2022) | 640 | 0.069 | 0.168 | 0.088 | 0.010 | 0.011 |  |
| YOLOv8m teacher (ours, RDD2022) | 640 | 0.066 | 0.205 | 0.014 | 0.004 | 0.042 |  |

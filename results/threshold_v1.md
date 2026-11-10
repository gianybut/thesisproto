# Confidence threshold calibrated on local val (v1)

Weights `runs/local/v1/weights/best.pt`. Data `data/local/yolo_nz`; selection set: all val frames (single-reviewer + annotation site), 1624 frames. App settings: imgsz 1024, NMS IoU 0.45. A detection is correct with the labelled class and IoU >= 0.5. Threshold = highest F1 over all classes (ties: the higher threshold).

**Chosen threshold: 0.24** (the app used 0.15 before).

## At 0.24, on the selection set

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 214 | 42 | 124 | 172 | 0.25 | 0.20 | 0.22 |
| D10 | 150 | 37 | 178 | 113 | 0.17 | 0.25 | 0.20 |
| D20 | 51 | 7 | 45 | 44 | 0.13 | 0.14 | 0.14 |
| D40 | 244 | 34 | 134 | 210 | 0.20 | 0.14 | 0.17 |
| All classes | 659 | 120 | 481 | 539 | 0.20 | 0.18 | 0.19 |

## Same threshold (0.24) on the 270 single-reviewer val frames (270 frames)

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 30 | 11 | 25 | 19 | 0.31 | 0.37 | 0.33 |
| D10 | 23 | 5 | 45 | 18 | 0.10 | 0.22 | 0.14 |
| D20 | 17 | 2 | 14 | 15 | 0.12 | 0.12 | 0.12 |
| D40 | 52 | 16 | 42 | 36 | 0.28 | 0.31 | 0.29 |
| All classes | 122 | 34 | 126 | 88 | 0.21 | 0.28 | 0.24 |

## Same threshold (0.24) on the 1,354 annotation-site val frames (1354 frames)

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 184 | 31 | 99 | 153 | 0.24 | 0.17 | 0.20 |
| D10 | 127 | 32 | 133 | 95 | 0.19 | 0.25 | 0.22 |
| D20 | 34 | 5 | 31 | 29 | 0.14 | 0.15 | 0.14 |
| D40 | 192 | 18 | 92 | 174 | 0.16 | 0.09 | 0.12 |
| All classes | 537 | 86 | 355 | 451 | 0.20 | 0.16 | 0.18 |

## Precision, recall and F1 by threshold (all classes, selection set)

| Threshold | Precision | Recall | F1 |
|---|---|---|---|
| 0.05 | 0.07 | 0.36 | 0.11 |
| 0.10 | 0.10 | 0.29 | 0.15 |
| 0.15 | 0.13 | 0.24 | 0.17 |
| 0.20 | 0.17 | 0.20 | 0.18 |
| 0.24 | 0.20 | 0.18 | 0.19 |
| 0.25 | 0.20 | 0.18 | 0.19 |
| 0.30 | 0.25 | 0.14 | 0.18 |
| 0.35 | 0.31 | 0.11 | 0.17 |
| 0.40 | 0.34 | 0.09 | 0.14 |
| 0.45 | 0.42 | 0.07 | 0.12 |
| 0.50 | 0.49 | 0.06 | 0.10 |
| 0.55 | 0.47 | 0.03 | 0.06 |
| 0.60 | 0.61 | 0.03 | 0.05 |
| 0.65 | 0.72 | 0.02 | 0.04 |
| 0.70 | 0.80 | 0.01 | 0.02 |
| 0.75 | 0.75 | 0.00 | 0.01 |
| 0.80 | 1.00 | 0.00 | 0.01 |
| 0.85 | 1.00 | 0.00 | 0.01 |
| 0.90 | 0.00 | 0.00 | 0.00 |

## Best threshold per class (information only: the app uses one threshold)

| Class | Threshold | F1 |
|---|---|---|
| D00 | 0.23 | 0.23 |
| D10 | 0.26 | 0.21 |
| D20 | 0.31 | 0.17 |
| D40 | 0.33 | 0.18 |

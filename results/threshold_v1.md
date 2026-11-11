# Confidence threshold calibrated on local val (v1)

Weights `runs/local/v1/weights/best.pt` fused with `runs/v3/S5_v8m_1920/weights/best.pt` (imgsz 1280) (each model at conf 0.05, weighted box fusion; the threshold is on the fused score). Data `data/local/yolo_nz`; selection set: the 270 single-reviewer val frames, 270 frames. App settings: imgsz 1024, grey border 24 px, TTA off, NMS IoU 0.45. A detection is correct with the labelled class and IoU >= 0.5. Threshold = highest F1 over all classes (ties: the higher threshold).

**Chosen threshold: 0.24** (the app used 0.15 before).

## At 0.24, on the selection set

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 30 | 17 | 22 | 13 | 0.44 | 0.57 | 0.49 |
| D10 | 23 | 5 | 19 | 18 | 0.21 | 0.22 | 0.21 |
| D20 | 17 | 1 | 4 | 16 | 0.20 | 0.06 | 0.09 |
| D40 | 52 | 12 | 11 | 40 | 0.52 | 0.23 | 0.32 |
| All classes | 122 | 35 | 56 | 87 | 0.38 | 0.29 | 0.33 |

## Same threshold (0.24) on the 1,354 annotation-site val frames (1354 frames)

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 184 | 28 | 99 | 156 | 0.22 | 0.15 | 0.18 |
| D10 | 127 | 30 | 48 | 97 | 0.38 | 0.24 | 0.29 |
| D20 | 34 | 4 | 6 | 30 | 0.40 | 0.12 | 0.18 |
| D40 | 192 | 14 | 20 | 178 | 0.41 | 0.07 | 0.12 |
| All classes | 537 | 76 | 173 | 461 | 0.31 | 0.14 | 0.19 |

## Same threshold (0.24) on all val frames (single-reviewer + annotation site) (1624 frames)

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 214 | 45 | 121 | 169 | 0.27 | 0.21 | 0.24 |
| D10 | 150 | 35 | 67 | 115 | 0.34 | 0.23 | 0.28 |
| D20 | 51 | 5 | 10 | 46 | 0.33 | 0.10 | 0.15 |
| D40 | 244 | 26 | 31 | 218 | 0.46 | 0.11 | 0.17 |
| All classes | 659 | 111 | 229 | 548 | 0.33 | 0.17 | 0.22 |

## Precision, recall and F1 by threshold (all classes, selection set)

| Threshold | Precision | Recall | F1 |
|---|---|---|---|
| 0.01 | 0.08 | 0.58 | 0.14 |
| 0.02 | 0.08 | 0.58 | 0.14 |
| 0.03 | 0.09 | 0.56 | 0.15 |
| 0.04 | 0.10 | 0.54 | 0.17 |
| 0.05 | 0.12 | 0.53 | 0.19 |
| 0.06 | 0.13 | 0.52 | 0.21 |
| 0.07 | 0.15 | 0.51 | 0.23 |
| 0.08 | 0.15 | 0.48 | 0.23 |
| 0.09 | 0.16 | 0.43 | 0.23 |
| 0.10 | 0.17 | 0.42 | 0.24 |
| 0.11 | 0.18 | 0.40 | 0.25 |
| 0.12 | 0.20 | 0.40 | 0.27 |
| 0.13 | 0.21 | 0.39 | 0.27 |
| 0.14 | 0.22 | 0.37 | 0.28 |
| 0.15 | 0.23 | 0.36 | 0.28 |
| 0.16 | 0.25 | 0.35 | 0.29 |
| 0.17 | 0.25 | 0.33 | 0.28 |
| 0.18 | 0.26 | 0.31 | 0.28 |
| 0.19 | 0.28 | 0.30 | 0.29 |
| 0.20 | 0.30 | 0.30 | 0.30 |
| 0.21 | 0.32 | 0.30 | 0.31 |
| 0.22 | 0.34 | 0.30 | 0.32 |
| 0.23 | 0.36 | 0.29 | 0.32 |
| 0.24 | 0.38 | 0.29 | 0.33 |
| 0.25 | 0.39 | 0.27 | 0.32 |
| 0.26 | 0.41 | 0.26 | 0.32 |
| 0.27 | 0.40 | 0.25 | 0.31 |
| 0.28 | 0.38 | 0.23 | 0.29 |
| 0.29 | 0.42 | 0.23 | 0.30 |
| 0.30 | 0.43 | 0.21 | 0.28 |
| 0.31 | 0.44 | 0.20 | 0.28 |
| 0.32 | 0.47 | 0.20 | 0.28 |
| 0.33 | 0.52 | 0.19 | 0.28 |
| 0.34 | 0.56 | 0.19 | 0.28 |
| 0.35 | 0.59 | 0.18 | 0.28 |
| 0.36 | 0.57 | 0.16 | 0.25 |
| 0.37 | 0.58 | 0.16 | 0.25 |
| 0.38 | 0.58 | 0.15 | 0.24 |
| 0.39 | 0.68 | 0.14 | 0.23 |
| 0.40 | 0.71 | 0.14 | 0.23 |
| 0.41 | 0.70 | 0.13 | 0.22 |
| 0.42 | 0.73 | 0.13 | 0.22 |
| 0.43 | 0.76 | 0.13 | 0.22 |
| 0.44 | 0.78 | 0.11 | 0.20 |
| 0.45 | 0.73 | 0.09 | 0.16 |
| 0.46 | 0.79 | 0.09 | 0.16 |
| 0.47 | 0.79 | 0.09 | 0.16 |
| 0.48 | 0.77 | 0.08 | 0.15 |
| 0.49 | 0.75 | 0.07 | 0.13 |
| 0.50 | 0.70 | 0.06 | 0.11 |

## Best threshold per class (information only: the app uses one threshold)

| Class | Threshold | F1 |
|---|---|---|
| D00 | 0.25 | 0.51 |
| D10 | 0.31 | 0.26 |
| D20 | 0.16 | 0.14 |
| D40 | 0.13 | 0.32 |

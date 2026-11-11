# Confidence threshold calibrated on local val (v1)

Weights `runs/local/v1/weights/best.pt` fused with `runs/local/v3/weights/best.pt` (imgsz 1280), `runs/v3/S5_v8m_1920/weights/best.pt` (imgsz 1280) (each model at conf 0.05, weighted box fusion; the threshold is on the fused score). Data `data/local/yolo_nz`; selection set: the 270 single-reviewer val frames, 270 frames. App settings: imgsz 1024, grey border 24 px, TTA off, NMS IoU 0.45. A detection is correct with the labelled class and IoU >= 0.5. Threshold = highest F1 over all classes (ties: the higher threshold).

**Chosen threshold: 0.24** (the app used 0.15 before).

## At 0.24, on the selection set

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 30 | 16 | 23 | 14 | 0.41 | 0.53 | 0.46 |
| D10 | 23 | 7 | 25 | 16 | 0.22 | 0.30 | 0.25 |
| D20 | 17 | 0 | 9 | 17 | 0.00 | 0.00 | 0.00 |
| D40 | 52 | 16 | 17 | 36 | 0.48 | 0.31 | 0.38 |
| All classes | 122 | 39 | 74 | 83 | 0.35 | 0.32 | 0.33 |

## Same threshold (0.24) on the 1,354 annotation-site val frames (1354 frames)

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 184 | 31 | 104 | 153 | 0.23 | 0.17 | 0.19 |
| D10 | 127 | 34 | 56 | 93 | 0.38 | 0.27 | 0.31 |
| D20 | 34 | 4 | 8 | 30 | 0.33 | 0.12 | 0.17 |
| D40 | 192 | 20 | 36 | 172 | 0.36 | 0.10 | 0.16 |
| All classes | 537 | 89 | 204 | 448 | 0.30 | 0.17 | 0.21 |

## Same threshold (0.24) on all val frames (single-reviewer + annotation site) (1624 frames)

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 214 | 47 | 127 | 167 | 0.27 | 0.22 | 0.24 |
| D10 | 150 | 41 | 81 | 109 | 0.34 | 0.27 | 0.30 |
| D20 | 51 | 4 | 17 | 47 | 0.19 | 0.08 | 0.11 |
| D40 | 244 | 36 | 53 | 208 | 0.40 | 0.15 | 0.22 |
| All classes | 659 | 128 | 278 | 531 | 0.32 | 0.19 | 0.24 |

## Precision, recall and F1 by threshold (all classes, selection set)

| Threshold | Precision | Recall | F1 |
|---|---|---|---|
| 0.01 | 0.06 | 0.66 | 0.12 |
| 0.02 | 0.07 | 0.65 | 0.13 |
| 0.03 | 0.09 | 0.61 | 0.15 |
| 0.04 | 0.10 | 0.59 | 0.18 |
| 0.05 | 0.11 | 0.57 | 0.19 |
| 0.06 | 0.13 | 0.56 | 0.21 |
| 0.07 | 0.14 | 0.56 | 0.23 |
| 0.08 | 0.15 | 0.53 | 0.24 |
| 0.09 | 0.16 | 0.52 | 0.25 |
| 0.10 | 0.18 | 0.52 | 0.27 |
| 0.11 | 0.19 | 0.48 | 0.27 |
| 0.12 | 0.20 | 0.48 | 0.28 |
| 0.13 | 0.21 | 0.46 | 0.29 |
| 0.14 | 0.22 | 0.43 | 0.29 |
| 0.15 | 0.23 | 0.41 | 0.30 |
| 0.16 | 0.25 | 0.41 | 0.31 |
| 0.17 | 0.26 | 0.40 | 0.32 |
| 0.18 | 0.28 | 0.39 | 0.32 |
| 0.19 | 0.28 | 0.37 | 0.32 |
| 0.20 | 0.29 | 0.35 | 0.32 |
| 0.21 | 0.30 | 0.34 | 0.32 |
| 0.22 | 0.31 | 0.34 | 0.32 |
| 0.23 | 0.32 | 0.33 | 0.32 |
| 0.24 | 0.35 | 0.32 | 0.33 |
| 0.25 | 0.34 | 0.30 | 0.32 |
| 0.26 | 0.37 | 0.30 | 0.33 |
| 0.27 | 0.38 | 0.29 | 0.33 |
| 0.28 | 0.38 | 0.27 | 0.32 |
| 0.29 | 0.43 | 0.26 | 0.32 |
| 0.30 | 0.44 | 0.26 | 0.33 |
| 0.31 | 0.45 | 0.25 | 0.32 |
| 0.32 | 0.47 | 0.23 | 0.31 |
| 0.33 | 0.48 | 0.21 | 0.30 |
| 0.34 | 0.51 | 0.20 | 0.28 |
| 0.35 | 0.53 | 0.19 | 0.28 |
| 0.36 | 0.53 | 0.19 | 0.28 |
| 0.37 | 0.53 | 0.19 | 0.28 |
| 0.38 | 0.57 | 0.19 | 0.28 |
| 0.39 | 0.59 | 0.19 | 0.29 |
| 0.40 | 0.60 | 0.17 | 0.27 |
| 0.41 | 0.62 | 0.16 | 0.26 |
| 0.42 | 0.62 | 0.16 | 0.26 |
| 0.43 | 0.66 | 0.16 | 0.25 |
| 0.44 | 0.68 | 0.14 | 0.23 |
| 0.45 | 0.73 | 0.13 | 0.22 |
| 0.46 | 0.76 | 0.13 | 0.22 |
| 0.47 | 0.75 | 0.12 | 0.21 |
| 0.48 | 0.71 | 0.10 | 0.17 |
| 0.49 | 0.71 | 0.10 | 0.17 |
| 0.50 | 0.71 | 0.10 | 0.17 |

## Best threshold per class (information only: the app uses one threshold)

| Class | Threshold | F1 |
|---|---|---|
| D00 | 0.30 | 0.54 |
| D10 | 0.24 | 0.25 |
| D20 | 0.16 | 0.12 |
| D40 | 0.18 | 0.43 |

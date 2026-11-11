# Confidence threshold calibrated on local val (v2b)

Weights `runs/local/v2b/weights/best.pt` fused with `runs/local/v3/weights/best.pt` (imgsz 1280), `runs/v3/S5_v8m_1920/weights/best.pt` (imgsz 1280) (each model at conf 0.05, weighted box fusion; the threshold is on the fused score). Data `data/local/yolo_nz`; selection set: the 270 single-reviewer val frames, 270 frames. App settings: imgsz 1024, grey border 24 px, TTA off, NMS IoU 0.45. A detection is correct with the labelled class and IoU >= 0.5. Threshold = highest F1 over all classes (ties: the higher threshold).

**Chosen threshold: 0.25** (the app used 0.15 before).

## At 0.25, on the selection set

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 30 | 15 | 22 | 15 | 0.41 | 0.50 | 0.45 |
| D10 | 23 | 5 | 20 | 18 | 0.20 | 0.22 | 0.21 |
| D20 | 17 | 0 | 8 | 17 | 0.00 | 0.00 | 0.00 |
| D40 | 52 | 17 | 14 | 35 | 0.55 | 0.33 | 0.41 |
| All classes | 122 | 37 | 64 | 85 | 0.37 | 0.30 | 0.33 |

## Same threshold (0.25) on the 1,354 annotation-site val frames (1354 frames)

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 184 | 33 | 108 | 151 | 0.23 | 0.18 | 0.20 |
| D10 | 127 | 35 | 35 | 92 | 0.50 | 0.28 | 0.36 |
| D20 | 34 | 3 | 15 | 31 | 0.17 | 0.09 | 0.12 |
| D40 | 192 | 19 | 45 | 173 | 0.30 | 0.10 | 0.15 |
| All classes | 537 | 90 | 203 | 447 | 0.31 | 0.17 | 0.22 |

## Same threshold (0.25) on all val frames (single-reviewer + annotation site) (1624 frames)

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 214 | 48 | 130 | 166 | 0.27 | 0.22 | 0.24 |
| D10 | 150 | 40 | 55 | 110 | 0.42 | 0.27 | 0.33 |
| D20 | 51 | 3 | 23 | 48 | 0.12 | 0.06 | 0.08 |
| D40 | 244 | 36 | 59 | 208 | 0.38 | 0.15 | 0.21 |
| All classes | 659 | 127 | 267 | 532 | 0.32 | 0.19 | 0.24 |

## Precision, recall and F1 by threshold (all classes, selection set)

| Threshold | Precision | Recall | F1 |
|---|---|---|---|
| 0.01 | 0.07 | 0.68 | 0.12 |
| 0.02 | 0.07 | 0.66 | 0.13 |
| 0.03 | 0.09 | 0.61 | 0.15 |
| 0.04 | 0.10 | 0.58 | 0.17 |
| 0.05 | 0.11 | 0.56 | 0.18 |
| 0.06 | 0.12 | 0.54 | 0.20 |
| 0.07 | 0.13 | 0.52 | 0.21 |
| 0.08 | 0.15 | 0.52 | 0.23 |
| 0.09 | 0.15 | 0.49 | 0.23 |
| 0.10 | 0.17 | 0.49 | 0.25 |
| 0.11 | 0.18 | 0.49 | 0.27 |
| 0.12 | 0.19 | 0.48 | 0.28 |
| 0.13 | 0.20 | 0.46 | 0.28 |
| 0.14 | 0.22 | 0.46 | 0.29 |
| 0.15 | 0.22 | 0.43 | 0.30 |
| 0.16 | 0.25 | 0.43 | 0.31 |
| 0.17 | 0.26 | 0.42 | 0.32 |
| 0.18 | 0.26 | 0.39 | 0.31 |
| 0.19 | 0.27 | 0.37 | 0.31 |
| 0.20 | 0.29 | 0.34 | 0.31 |
| 0.21 | 0.30 | 0.34 | 0.32 |
| 0.22 | 0.32 | 0.33 | 0.32 |
| 0.23 | 0.33 | 0.32 | 0.33 |
| 0.24 | 0.34 | 0.30 | 0.32 |
| 0.25 | 0.37 | 0.30 | 0.33 |
| 0.26 | 0.36 | 0.29 | 0.32 |
| 0.27 | 0.37 | 0.28 | 0.32 |
| 0.28 | 0.39 | 0.27 | 0.32 |
| 0.29 | 0.39 | 0.26 | 0.31 |
| 0.30 | 0.41 | 0.25 | 0.31 |
| 0.31 | 0.41 | 0.24 | 0.30 |
| 0.32 | 0.45 | 0.24 | 0.31 |
| 0.33 | 0.47 | 0.24 | 0.32 |
| 0.34 | 0.48 | 0.22 | 0.30 |
| 0.35 | 0.49 | 0.21 | 0.30 |
| 0.36 | 0.51 | 0.21 | 0.30 |
| 0.37 | 0.52 | 0.20 | 0.29 |
| 0.38 | 0.53 | 0.19 | 0.28 |
| 0.39 | 0.56 | 0.19 | 0.28 |
| 0.40 | 0.57 | 0.17 | 0.26 |
| 0.41 | 0.57 | 0.16 | 0.25 |
| 0.42 | 0.57 | 0.16 | 0.25 |
| 0.43 | 0.62 | 0.15 | 0.24 |
| 0.44 | 0.61 | 0.14 | 0.23 |
| 0.45 | 0.64 | 0.13 | 0.22 |
| 0.46 | 0.59 | 0.11 | 0.18 |
| 0.47 | 0.59 | 0.11 | 0.18 |
| 0.48 | 0.60 | 0.10 | 0.17 |
| 0.49 | 0.60 | 0.10 | 0.17 |
| 0.50 | 0.60 | 0.07 | 0.13 |

## Best threshold per class (information only: the app uses one threshold)

| Class | Threshold | F1 |
|---|---|---|
| D00 | 0.39 | 0.52 |
| D10 | 0.34 | 0.28 |
| D20 | 0.08 | 0.07 |
| D40 | 0.21 | 0.43 |

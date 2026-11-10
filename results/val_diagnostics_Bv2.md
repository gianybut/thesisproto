# Val diagnostics: Bv2

Reviewed local val set, 270 frames (63 with damage, 122 boxes). Weights `runs/v2/Bv2/weights/best.pt`, imgsz 1280.

## AP@50 per class at match IoU 0.25 and 0.50

Per-class NMS 0.7, conf >= 0.001, 101-point AP. Correct = same class and IoU >= the match threshold.

| Class | Boxes | AP, IoU 0.25 | AP, IoU 0.50 |
|---|---|---|---|
| D00 | 30 | 0.432 | 0.280 |
| D10 | 23 | 0.167 | 0.160 |
| D20 | 17 | 0.051 | 0.013 |
| D40 | 52 | 0.297 | 0.229 |
| Mean (mAP) | 122 | 0.237 | 0.170 |

## Class-agnostic ("damage", the four classes merged)

Class-agnostic NMS 0.7; correct = any reviewed box with IoU >= the match threshold.

| | AP, IoU 0.25 | AP, IoU 0.50 |
|---|---|---|
| Damage (any class) | 0.313 | 0.190 |

## At the threshold candidate 0.16

App settings (per-class NMS 0.45); threshold = highest F1 over all classes on val (as calibrate_threshold.py).

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 30 | 14 | 76 | 16 | 0.16 | 0.47 | 0.23 |
| D10 | 23 | 6 | 17 | 17 | 0.26 | 0.26 | 0.26 |
| D20 | 17 | 0 | 17 | 17 | 0.00 | 0.00 | 0.00 |
| D40 | 52 | 15 | 29 | 37 | 0.34 | 0.29 | 0.31 |
| All classes | 122 | 35 | 139 | 87 | 0.20 | 0.29 | 0.24 |

Confusion matrix (match IoU 0.5 regardless of class; rows = reviewed class, columns = predicted; "background" row = false alarms, column = missed):

| Reviewed \ Predicted | D00 | D10 | D20 | D40 | background |
|---|---|---|---|---|---|
| D00 | 14 | 0 | 0 | 0 | 16 |
| D10 | 0 | 6 | 2 | 0 | 15 |
| D20 | 0 | 0 | 0 | 1 | 16 |
| D40 | 0 | 1 | 0 | 15 | 36 |
| background | 76 | 16 | 15 | 28 | - |

Frame level, "frame contains damage" (>= 1 reviewed box vs >= 1 prediction at the threshold):

| Frames | With damage | Without | TP | FP | FN | TN | Accuracy | Precision | Recall |
|---|---|---|---|---|---|---|---|---|---|
| 270 | 63 | 207 | 49 | 56 | 14 | 151 | 0.741 | 0.467 | 0.778 |

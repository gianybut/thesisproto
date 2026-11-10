# Val diagnostics: Bv1

Reviewed local val set, 270 frames (63 with damage, 122 boxes). Weights `runs/v2/Bv1/weights/best.pt`, imgsz 1280.

## AP@50 per class at match IoU 0.25 and 0.50

Per-class NMS 0.7, conf >= 0.001, 101-point AP. Correct = same class and IoU >= the match threshold.

| Class | Boxes | AP, IoU 0.25 | AP, IoU 0.50 |
|---|---|---|---|
| D00 | 30 | 0.372 | 0.238 |
| D10 | 23 | 0.118 | 0.111 |
| D20 | 17 | 0.076 | 0.021 |
| D40 | 52 | 0.230 | 0.174 |
| Mean (mAP) | 122 | 0.199 | 0.136 |

## Class-agnostic ("damage", the four classes merged)

Class-agnostic NMS 0.7; correct = any reviewed box with IoU >= the match threshold.

| | AP, IoU 0.25 | AP, IoU 0.50 |
|---|---|---|
| Damage (any class) | 0.258 | 0.149 |

## At the threshold candidate 0.25

App settings (per-class NMS 0.45); threshold = highest F1 over all classes on val (as calibrate_threshold.py).

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 30 | 14 | 60 | 16 | 0.19 | 0.47 | 0.27 |
| D10 | 23 | 5 | 17 | 18 | 0.23 | 0.22 | 0.22 |
| D20 | 17 | 0 | 13 | 17 | 0.00 | 0.00 | 0.00 |
| D40 | 52 | 6 | 12 | 46 | 0.33 | 0.12 | 0.17 |
| All classes | 122 | 25 | 102 | 97 | 0.20 | 0.20 | 0.20 |

Confusion matrix (match IoU 0.5 regardless of class; rows = reviewed class, columns = predicted; "background" row = false alarms, column = missed):

| Reviewed \ Predicted | D00 | D10 | D20 | D40 | background |
|---|---|---|---|---|---|
| D00 | 14 | 0 | 0 | 0 | 16 |
| D10 | 0 | 5 | 3 | 0 | 15 |
| D20 | 0 | 1 | 0 | 0 | 16 |
| D40 | 0 | 2 | 0 | 6 | 44 |
| background | 60 | 14 | 10 | 12 | - |

Frame level, "frame contains damage" (>= 1 reviewed box vs >= 1 prediction at the threshold):

| Frames | With damage | Without | TP | FP | FN | TN | Accuracy | Precision | Recall |
|---|---|---|---|---|---|---|---|---|---|
| 270 | 63 | 207 | 42 | 49 | 21 | 158 | 0.741 | 0.462 | 0.667 |

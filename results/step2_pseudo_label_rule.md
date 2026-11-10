# Pseudo-label rule for the teacher, fitted on the reviewed val frames

120 reviewed val frames; class-aware matching at IoU >= 0.50, one-to-one, highest confidence first. Test frames were not used.

## Image size (teacher AP@50 on reviewed val)

| imgsz | D00 | D10 | D20 | D40 | mean |
|---|---|---|---|---|---|
| 960 | 0.292 | 0.000 | 0.022 | 0.086 | 0.100 |
| 1280 | 0.308 | 0.077 | 0.000 | 0.093 | 0.119 |

Chosen: **1280**.

## Per-class rule (target precision 0.60)

| Class | Val instances | Threshold | How chosen | TP | FP | FN | Precision | Recall | With CLIP: P | With CLIP: R | CLIP used |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D00 | 25 | 0.587 | lowest with P >= 0.60 | 3 | 2 | 22 | 0.60 | 0.12 | 0.75 | 0.12 | yes |
| D10 | 13 | 0.102 | lowest with P >= 0.60 | 1 | 0 | 12 | 1.00 | 0.08 | 1.00 | 0.08 | no |
| D20 | 12 | - | none: no correct box on val at any threshold | 0 | 0 | 12 | 0.00 | 0.00 | 0.00 | 0.00 | no |
| D40 | 36 | 0.051 | best F1 (target not reached) | 8 | 16 | 28 | 0.33 | 0.22 | 0.37 | 0.19 | yes |

## Train yield (6103 train frames, teacher at 1280, rule above)

| | D00 | D10 | D20 | D40 | Frames with any box |
|---|---|---|---|---|---|
| Boxes | 46 | 144 | 0 | 145 | |
| Frames containing the class | 45 | 121 | 0 | 128 | 283 |

Small val counts (D10 13, D20 12 instances) make those thresholds uncertain; the expanded, second-pass-reviewed val set will be used to re-fit before labels are written.

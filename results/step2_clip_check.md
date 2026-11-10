# AI check (CLIP) per class against the reviewed val labels

Every stand-in detector box (confidence >= 0.25) in the 120 reviewed val frames, matched one-to-one to the reviewed boxes at IoU >= 0.5 (any class). "Real" = it matches a reviewed box; "false" = it matches none. The AI check keeps a box when its CLIP score is >= 0.60.

| Detector class | Boxes | Kept, real | **Kept, false** | **Dropped, real** | Dropped, false | Real but other class |
|---|---|---|---|---|---|---|
| D00 | 11 | 6 | 5 | 0 | 0 | 0 |
| D10 | 0 | 0 | 0 | 0 | 0 | 0 |
| D20 | 9 | 7 | 1 | 0 | 1 | 0 |
| D40 | 86 | 12 | 72 | 0 | 2 | 1 |
| **all** | 106 | 25 | 78 | 0 | 3 | 1 |

## Candidate rules on val (class-aware, IoU >= 0.5)

| Rule | D00 P | D00 R | D10 P | D10 R | D20 P | D20 R | D40 P | D40 R | All P | All R |
|---|---|---|---|---|---|---|---|---|---|---|
| detector only (no AI check) | 0.55 (6/11) | 0.24 (6/25) | - (0/0) | 0.00 (0/13) | 0.78 (7/9) | 0.58 (7/12) | 0.13 (11/86) | 0.31 (11/36) | 0.23 | 0.28 |
| AI check on all classes (current) | 0.55 (6/11) | 0.24 (6/25) | - (0/0) | 0.00 (0/13) | 0.88 (7/8) | 0.58 (7/12) | 0.13 (11/84) | 0.31 (11/36) | 0.23 | 0.28 |
| AI check for D20/D40; D00/D10 at conf >= 0.40 | 1.00 (2/2) | 0.08 (2/25) | - (0/0) | 0.00 (0/13) | 0.88 (7/8) | 0.58 (7/12) | 0.13 (11/84) | 0.31 (11/36) | 0.21 | 0.23 |
| AI check for D20/D40; D00/D10 without it | 0.55 (6/11) | 0.24 (6/25) | - (0/0) | 0.00 (0/13) | 0.88 (7/8) | 0.58 (7/12) | 0.13 (11/84) | 0.31 (11/36) | 0.23 | 0.28 |
| AI check for D40 only | 0.55 (6/11) | 0.24 (6/25) | - (0/0) | 0.00 (0/13) | 0.78 (7/9) | 0.58 (7/12) | 0.13 (11/84) | 0.31 (11/36) | 0.23 | 0.28 |

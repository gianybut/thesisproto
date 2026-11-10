# Review batch 2 (val and test expansion)

300 new frames; teacher (RDD2022 only) at imgsz 1280, low threshold 0.1; at least 3 s from any selected frame of the same recording; 50 m rule respected (only frames it kept).

| Split | Teacher-detected frames (D10 / D20 / D40 turns) | Random frames | Route groups (reviewer) |
|---|---|---|---|
| val | 31 (13 / 11 / 7) | 119 | G04 52 (Reviewer A), G06 52 (Reviewer B), G10 46 (Reviewer C) |
| test | 37 (14 / 19 / 4) | 113 | G05 59 (Reviewer C), G13 47 (Reviewer A), G15 44 (Reviewer B) |

## Expected reviewed instances after batch 2 (estimate)

Rates from the 120 reviewed val frames: mean reviewed instances of the class per frame where the teacher detects that class at >= 0.1, and per frame where it does not.

| Class | Rate if detected (frames) | Rate if not (frames) | Val now | Val expected | Test now | **Test expected** | Test >= 20? |
|---|---|---|---|---|---|---|---|
| D00 | 0.75 (28) | 0.043 (92) | 25 | 50 | 23 | **41** | yes |
| D10 | 1.00 (1) | 0.101 (119) | 13 | 40 | 4 | **32** | yes |
| D20 | 0.60 (10) | 0.055 (110) | 12 | 27 | 15 | **34** | yes |
| D40 | 1.00 (8) | 0.250 (112) | 36 | 80 | 10 | **50** | yes |

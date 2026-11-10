# Review batch "train": train frames

300 train frames: 200 where the teacher detects damage at >= 0.1 (rare classes first: D10 93, D20 107, D00/D40 0), 100 random; at least 3 s apart within a recording. Drafts: teacher boxes at >= 0.10 (lowered from 0.15 so every teacher-selected frame shows the box it was chosen for).

| Route group | Frames | Reviewer |
|---|---|---|
| G01 | 84 | Reviewer B |
| G03 | 37 | Reviewer C |
| G07 | 44 | Reviewer C |
| G08 | 8 | Reviewer B |
| G09 | 96 | Reviewer A |
| G11 | 5 | Reviewer A |
| G12 | 11 | Reviewer B |
| G14 | 15 | Reviewer C |

| Reviewer | Frames |
|---|---|
| Reviewer A | 101 |
| Reviewer B | 103 |
| Reviewer C | 96 |

Extension (2026-11-10): 76 more frames, D40 46, D00 30 (teacher >= 0.1, in turn across route groups: G01 10, G03 15, G07 21, G08 6, G09 12, G11 4, G12 4, G14 4).

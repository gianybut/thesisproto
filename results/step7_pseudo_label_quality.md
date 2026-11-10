# Pseudo-label quality (stand-in RDD2022 detector) against the reviewed labels

Reviewed val + test frames (240; 120 each). Class-aware matching at IoU >= 0.5. "Drafts" are the detector boxes the AI check kept (what the reviewers were shown); "detector alone" is every box of the four classes at confidence >= 0.25. Reviewers saw the drafts, which may anchor them toward accepting them; the boxes the AI check removed were not shown.

| Split | Labels | D00 P | D00 R | D10 P | D10 R | D20 P | D20 R | D40 P | D40 R | All P | All R | Reviewed boxes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| val | drafts (detector + AI check) | 0.55 | 0.24 | - | 0.00 | 0.88 | 0.58 | 0.13 | 0.31 | 0.23 | 0.28 | D00 25, D10 13, D20 12, D40 36 |
| val | detector alone | 0.55 | 0.24 | - | 0.00 | 0.78 | 0.58 | 0.13 | 0.31 | 0.23 | 0.28 | D00 25, D10 13, D20 12, D40 36 |
| test | drafts (detector + AI check) | 0.86 | 0.26 | - | 0.00 | 0.12 | 0.07 | 0.07 | 0.70 | 0.13 | 0.27 | D00 23, D10 4, D20 15, D40 10 |
| test | detector alone | 0.86 | 0.26 | - | 0.00 | 0.11 | 0.07 | 0.07 | 0.70 | 0.12 | 0.27 | D00 23, D10 4, D20 15, D40 10 |
| val+test | drafts (detector + AI check) | 0.67 | 0.25 | - | 0.00 | 0.50 | 0.30 | 0.10 | 0.39 | 0.18 | 0.28 | D00 48, D10 17, D20 27, D40 46 |
| val+test | detector alone | 0.67 | 0.25 | - | 0.00 | 0.44 | 0.30 | 0.10 | 0.39 | 0.17 | 0.28 | D00 48, D10 17, D20 27, D40 46 |

AI check: removed 10 detector boxes in these frames; 10 of them match no reviewed box (confirmed not damage at IoU >= 0.5): D00 0, D10 0, D20 2, D40 8.

# Step 1.4: local split by route group

18 mounted recordings (R04-R21). The hand-held R01-R03 (route groups G01 and G02, all train) were excluded on 2026-11-09 after the split was made; their frames are removed. Val/test and their 50 m drops are unchanged: the drops were computed with R01-R03 still in train, and the team kept them as they were.

Rule: whole route groups per split; then val/test frames within 50 m of any train frame are dropped (team decision 2026-11-09). Draft labels (autolabel, kept boxes) are used only to balance classes.

| Split | Route groups | Frames | Share | Frames with a draft box | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|---|---|
| train | G01, G03, G07, G08, G09, G11, G12, G14 | 6103 | 64.4% | 351 | 30 | 0 | 39 | 351 |
| val | G04, G06, G10 | 1717 | 18.1% | 87 | 11 | 0 | 8 | 84 |
| test | G05, G13, G15 | 1661 | 17.5% | 90 | 7 | 0 | 8 | 96 |

## Dropped by the 50 m location rule: 109 frames

| Recording | Route group | Split | Frames dropped | of frames in it | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|---|---|
| R05 | G04 | val | 5 | 586 | 0 | 0 | 0 | 0 |
| R06 | G05 | test | 0 | 586 | 0 | 0 | 0 | 0 |
| R07 | G06 | val | 6 | 590 | 0 | 0 | 0 | 0 |
| R16 | G10 | val | 8 | 560 | 0 | 0 | 0 | 1 |
| R19 | G13 | test | 5 | 580 | 0 | 0 | 0 | 0 |
| R21 | G15 | test | 85 | 585 | 0 | 0 | 0 | 3 |
| **all** | | | **109** | | **0** | **0** | **0** | **4** |

# Review batch "AL2" (active learning with B_v2)

Reviewed train instances when selected: D40 103, D20 25; classes taken in the order D40 > D20 (team priority). Selection counts near-zone detections only (band top + 0.1).

300 train frames: D40 111, D20 25, uncertain 0.2-0.5 164; drafts are B_v2 boxes at >= 0.2 (weights runs/v2/Bv2/weights/best.pt).

| Route group | Frames |
|---|---|
| G01 | 71 |
| G03 | 45 |
| G07 | 52 |
| G08 | 17 |
| G09 | 49 |
| G11 | 17 |
| G12 | 25 |
| G14 | 24 |

Class tiers counted detections at >= 0.10 (--rare-conf 0.10): at the usual 0.25, B v2 found D40/D20 in only 15 unreviewed near-zone frames. Drafts still show B v2 boxes at >= 0.20, so D40/D20 seen at 0.10-0.20 must be drawn by the reviewer. First attempt (rare-conf 0.25, 271 frames, unreviewed) discarded 2026-11-10 11:55.

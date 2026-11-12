# Local YOLO datasets (human labels only), near zone

Export 20261110_170638: 1,066 reviewed frames + annotation-site frames from `backups/labels_20261110_170638_export.db`.

| Split | Frames | No damage | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|
| train | 526 | 315 | 165 | 103 | 23 | 97 |
| val | 270 | 207 | 30 | 23 | 17 | 52 |
| test | 270 | 207 | 36 | 8 | 34 | 21 |

| Of which new from the annotation site | Frames | No damage | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|
| train | 0 | 0 | 0 | 0 | 0 | 0 |
| val | 0 | 0 | 0 | 0 | 0 | 0 |

| Training list | Images per epoch |
|---|---|
| local_train.txt (A) | 526 |
| local_train_x3.txt (B_noreplay, D10/D20/D40 x3) | 814 |

No RDD2022 replay (decision 2026-11-10): B.yaml / B_train.txt are not written. Test set unchanged.

Reviewed-only base (build_local_yolo.py) before the export:
> # Local YOLO datasets (human-reviewed labels only), near zone
> | Split | Frames | No damage | D00 | D10 | D20 | D40 |
> |---|---|---|---|---|---|---|
> | train | 526 | 315 | 165 | 103 | 23 | 97 |
> | val | 270 | 207 | 30 | 23 | 17 | 52 |
> | test | 270 | 207 | 36 | 8 | 34 | 21 |
> | Training list | Images per epoch | of which local |
> |---|---|---|
> | local_train.txt | 526 | 526 |
> | local_train_x3.txt | 814 | 814 |
> | B_train.txt | 1414 | 814 |
> Boxes dropped (centre outside the near zone): train D00 12, train D10 11, train D20 2, train D40 6.
> D10/D20/D40 train frames repeated x3: 144. Replay: 600 images (random of 15294 six-country RDD2022 train, seed 42). Test frames reviewed so far: 270 of 270 (rebuild with --final before the test evaluation).

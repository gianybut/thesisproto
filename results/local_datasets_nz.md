# Local YOLO datasets (human labels only), near zone

Export 20261111_013653: 1,066 reviewed frames + annotation-site frames from `backups/labels_FINAL_20261111_013131.db`.

| Split | Frames | No damage | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|
| train | 5571 | 4044 | 1450 | 556 | 152 | 779 |
| val | 1624 | 1314 | 214 | 150 | 51 | 244 |
| test | 270 | 207 | 36 | 8 | 34 | 21 |

| Of which new from the annotation site | Frames | No damage | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|
| train | 5045 | 3729 | 1285 | 453 | 129 | 682 |
| val | 1354 | 1107 | 184 | 127 | 34 | 192 |

Val lists: val_reviewed.txt 270 (single-reviewer), val_new.txt 1354 (annotation site), val.txt 1624 (both; yamls val_reviewed / val_new / val_full).

| Training list | Images per epoch |
|---|---|
| local_train.txt (A) | 5571 |
| local_train_x3.txt (B_noreplay, D10/D20/D40 x3) | 7327 |

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

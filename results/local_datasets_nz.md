# Local YOLO datasets (human-reviewed labels only), near zone

| Split | Frames | No damage | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|
| train | 526 | 315 | 165 | 103 | 23 | 97 |
| val | 270 | 207 | 30 | 23 | 17 | 52 |
| test | 270 | 207 | 36 | 8 | 34 | 21 |

| Training list | Images per epoch | of which local |
|---|---|---|
| local_train.txt | 526 | 526 |
| local_train_x3.txt | 814 | 814 |
| B_train.txt | 1414 | 814 |

Boxes dropped (centre outside the near zone): train D00 12, train D10 11, train D20 2, train D40 6.

D10/D20/D40 train frames repeated x3: 144. Replay: 600 images (random of 15294 six-country RDD2022 train, seed 42). Test frames reviewed so far: 270 of 270 (rebuild with --final before the test evaluation).

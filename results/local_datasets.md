# Local YOLO datasets (human-reviewed labels only)

| Split | Frames | No damage | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|
| train | 526 | 306 | 177 | 114 | 25 | 103 |
| val | 270 | 207 | 30 | 23 | 17 | 52 |
| test | 270 | 207 | 36 | 8 | 34 | 21 |

| Training list | Images per epoch | of which local |
|---|---|---|
| local_train.txt | 526 | 526 |
| local_train_x3.txt | 736 | 736 |
| B_train.txt | 1336 | 736 |

D10/D20 train frames repeated x3: 105. Replay: 600 images (random of 15294 six-country RDD2022 train, seed 42). Test frames reviewed so far: 270 of 270 (rebuild with --final before the test evaluation).

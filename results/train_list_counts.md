# Run v1 training list (per epoch)

Data: data/local/yolo_nz from `backups/labels_FINAL_20261111_013131.db`. Built by ml/local/build_v1_list.py --max-negatives 1500 --repeat 3 --seed 0.

| | Images | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|
| Per epoch (after x3) | 4783 | 2416 | 1668 | 456 | 2337 |
| Unique frames | 3027 | 1450 | 556 | 152 | 779 |

Damage frames: 1527, all kept (Gian 85, Janmikael 844, Kyle 387, reviewed 211); 878 with D10/D20/D40 repeated x3.
Negatives: 1500 of 4044 (cap 1500): Gian 374, Kyle 811, reviewed 315. Order: single-reviewer negatives all (315), then a random sample (seed 0) of Kyle's and Gian's site negatives (2217 available), Janmikael's (1512) only if needed.
Negatives are 31% of the images per epoch. No RDD2022 replay.

Ultralytics trains on this list every epoch (mosaic mixes four images per sample until the last 10 epochs).

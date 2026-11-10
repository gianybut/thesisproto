# Annotation-site label quality (final freeze)

Snapshot `backups/labels_FINAL_20261111_013131.db`. Labelled 6399 frames (1563 with damage, 4836 no damage), skipped 1. Pre-labels: S5_v8m_1280, conf 0.15.

## Final boxes kept unchanged from the model pre-labels (same class, IoU >= 0.9)

| Labeller | D00 | D10 | D20 | D40 | All boxes | Drafts kept / drafts shown |
|---|---|---|---|---|---|---|
| Gian | 38% (31/82) | 51% (18/35) | 15% (3/20) | 6% (3/52) | 29% (55/189) | 53% (55/103) |
| Janmikael | 66% (584/880) | 66% (209/315) | 44% (42/96) | 65% (235/364) | 65% (1070/1655) | 55% (1070/1954) |
| Kyle | 14% (71/507) | 13% (31/230) | 9% (4/47) | 9% (42/458) | 12% (148/1242) | 13% (148/1102) |
| all | 47% (686/1469) | 44% (258/580) | 30% (49/163) | 32% (280/874) | 41% (1273/3086) | 40% (1273/3159) |

"Unchanged" share = of the final boxes, how many are a draft accepted as is. Last column = of the drafts the labeller saw, how many survived unchanged (the rest were deleted, re-classed or redrawn).

## Pace (seconds since the same labeller's previous save; breaks over 10 min left out)

| Labeller | Frames | Damage frames: n, median s | No-damage frames: n, median s | No-damage share | Saves under 2 s | Span |
|---|---|---|---|---|---|---|
| Gian | 942 | 104, 10.3 | 843, 2.2 | 89% | 398 (42%) | 8.2 h |
| Janmikael | 2849 | 976, 3.3 | 1968, 1.0 | 67% | 1756 (60%) | 8.1 h |
| Kyle | 2608 | 549, 11.0 | 2131, 1.3 | 80% | 1477 (55%) | 8.1 h |

## Per labeller and split

| Labeller | Train damage | Train no damage | Val damage | Val no damage |
|---|---|---|---|---|
| Gian | 85 | 662 | 20 | 175 |
| Janmikael | 844 | 1512 | 96 | 397 |
| Kyle | 387 | 1555 | 131 | 535 |

## Spot check

`results/spotcheck_list.csv`: 50 damage + 50 no-damage frames, random, seed 0. Fill in "correct (yes/no)".

## Negatives used for training (run v1)

Damage frames: 1527, all kept (Gian 85, Janmikael 844, Kyle 387, reviewed 211); 878 with D10/D20/D40 repeated x3.
Negatives: 1500 of 4044 (cap 1500): Gian 374, Kyle 811, reviewed 315. Order: single-reviewer negatives all (315), then a random sample (seed 0) of Kyle's and Gian's site negatives (2217 available), Janmikael's (1512) only if needed.

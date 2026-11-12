# Damage log: automatic checks of the survey 3 sample

Written by `tools/damage_log_auto.py`. Source: checklist `results/damage_log_check/survey3_checklist.csv` (times rounded to 0.1 s) and GPX `frontend/public/samples/alfonso-bayan-national-road/track.gpx` (session 20261031T021049-3x76, 607 points, timeOffsetS 9.607); the backend database was not available.

Checklist: `results/damage_log_check/survey3_checklist.csv` (50 records, drawn at random with seed 42 by `tools/damage_log_check.py export`).

| Check | Consistent | Not consistent | Definition |
|---|---|---|---|
| Time | 50 | 0 | stored time = frame / FPS (Formula 13) within 0.05 s |
| Location | 50 | 0 | record within (1 m + speed x 0.05 s) of the track interpolated at time + offset, not clamped |
| Duplicate candidate | 10 | 40 | another record, same class, <= 15 m and <= 5 s (among the 50 sampled records only) |

Sync error (record vs track at its time), m: mean 0.152, SD 0.111, max 0.440 (n = 50).
Distance from record to the route, m: mean 0.001, SD 0.003, max 0.010.

Duplicate candidates (to be confirmed on the review page):

- item 5, record 445 (D40, 91.8 s): 446 (0.5 m, +0.2 s)
- item 6, record 446 (D40, 92.0 s): 445 (0.5 m, -0.2 s)
- item 10, record 453 (D40, 128.0 s): 454 (9.7 m, +1.0 s)
- item 11, record 454 (D40, 129.0 s): 453 (9.7 m, -1.0 s)
- item 19, record 477 (D40, 286.0 s): 478 (12.1 m, +1.4 s)
- item 20, record 478 (D40, 287.4 s): 477 (12.1 m, -1.4 s)
- item 33, record 513 (D40, 508.7 s): 514 (0.8 m, +0.2 s)
- item 34, record 514 (D40, 508.9 s): 513 (0.8 m, -0.2 s)
- item 41, record 532 (D10, 546.4 s): 531 (3.3 m, +0.5 s)
- item 42, record 531 (D10, 546.9 s): 532 (3.3 m, -0.5 s)

Notes:

- The database at /Users/gpybut/Documents/THESIS/thesisproto/backend/pothole_detection.db does not hold survey 3 as 20261031T021049-3x76.mov (it has 20261020T002142-rnbm.mov); it was not used.
- Frame rates consistent with all 50 (frame, time) pairs: 29.9975 to 29.9983 fps.
- Duplicates were looked for among the 50 sampled records only (no database): a lower bound. Run this script on the computer that holds survey 3 for the full check.
- These are consistency checks: they show the stored time and position follow from the frame and the GPS track as the method intends. Whether the damage is really at that time and place is decided by the reviewer.
- Per-record values: `results/damage_log_check/survey3_autocheck.csv`.

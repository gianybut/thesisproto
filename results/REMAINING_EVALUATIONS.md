# Remaining evaluations: numbers, sources, definitions

Written 2026-11-12. Nothing here has been put into the manuscript. The test set was not used for anything.

**Where the work could run.** This file was produced on the MacBook. The recordings (`VID+GPX/`), `data/local/`,
`runs/`, and the backend database that holds survey 3 (R07) with its snapshots and video are on the Windows
training PC only. On the Mac: the code, the model weights, the committed results, the damage-log checklist (50
records with their frame, time and coordinates) and five full GPX tracks of study recordings (the public samples:
R05, R06, R07 and two from 3 Nov). So every number below is marked:

- **final**: computed from the data it needs;
- **provisional**: computed from what is on the Mac, to be re-run on the PC (the command is given);
- **pending**: needs the PC or a person; the tool is ready and tested on dev data.

---

## 1. Second-stage classifier (manuscript 3.3.1, 4.2.4, 5.1)

Full report: `results/classifier_report.md`. Metric definitions (validation only): `results/classifier_metric_definitions.md`.

| Number | Value | Status | Source | Definition |
|---|---|---|---|---|
| Classifier model | YOLOv8n-cls, 224 px, 4 classes | final | `ml/models/classifier.pt` (`train_args`, `model.names`) | |
| Trained | 2026-11-12 10:17:49, run `road_damage_retry`, at commit `4d46a1f` | final | checkpoint `date`, `train_args.name`, `git` | |
| Epochs | 30 of 50 run (patience 20), epoch 10 kept | final | checkpoint `train_results` | best = highest val top-1 (Ultralytics fitness) |
| Val crops | 122 (the boxes of the 270 reviewed val frames) | final | checkpoint `train_metrics` (0.81967 = 100/122) | crop = box + 25% each side |
| Train crops | most likely 388 (D00 165, D10 103, D20 23, D40 97) | to confirm | `results/local_datasets_nz_export.md`; confirm in `data/local/classification/dataset_metadata.json` (PC) | |
| Val top-1 | 0.820 (100 of 122) | final, selection figure | checkpoint `train_metrics` | reviewed boxes, training-style crops; epoch chosen on them |
| Fusion's own class accuracy, val (reference) | 92.5% (37/40; 95% CI 80.1-97.4%) | final | `results/test_evaluation.md` Table 5.D | matched detections (IoU >= 0.5, any class) at 0.25 |
| Classifier vs fusion on the same matched val detections | - | pending (PC) | `python ml/local/classifier_val_compare.py` -> `results/classifier_val_compare.md` | `classifier_metric_definitions.md` section 1 |
| Deployed output changed? | yes: relabels every record's `damage_type`; same records, times, positions, confidences | final | `backend/services/video_processor.py` (`save_track`), `damage_tracker.py` (class-agnostic) | |
| Test evaluation of the classifier | almost certainly printed ~10:17-10:20 on 2026-11-12 by `train_classifier.py`, after the one test evaluation (2026-11-11 17:09) and with no metric definitions; number not in the repo | final (from the code) | `git show 5d796a1:ml/train_classifier.py`, `:ml/build_classifier_dataset.py`; checkpoint `train_args.data` | must not be reported as a result |

## 2. Damage log correctness (manuscript 5.3, RQ2)

Sample: 50 records of survey 3 (R07, `20261031T021049-3x76.mov`), seed 42, drawn 2026-11-11 17:09
(`results/damage_log_check/survey3_checklist.csv`, commit `6117fb5`), before the classifier existed.

Automatic checks (`tools/damage_log_auto.py` -> `results/damage_log_check/survey3_autocheck.md/.csv`). Provisional:
run on the Mac from the checklist (times rounded to 0.1 s) and R07's GPX
(`frontend/public/samples/alfonso-bayan-national-road/track.gpx`, sessionId = R07, 607 points, timeOffsetS 9.607);
on the PC it uses the database (exact timestamps, stored track, all 112 records).

| Number | Value | Status | Definition |
|---|---|---|---|
| Time consistent | 50 of 50 | provisional | stored time = frame / FPS (Formula 13) within 0.05 s; all 50 (frame, time) pairs fit one frame rate, 29.9975 to 29.9983 fps |
| Location consistent | 50 of 50 | provisional | record within 1 m + speed x 0.05 s of the track interpolated at time + offset (as `interpolate_gps`), not clamped to a track end |
| Sync error | mean 0.152 m, SD 0.111, max 0.440 (n = 50) | provisional | Haversine distance, record vs track at its time; non-zero only because the checklist rounds time to 0.1 s |
| Distance to the route | mean 0.001 m, max 0.010 m | provisional | shortest distance from record to the track polyline |
| Duplicate candidates | 10 of 50 records (5 pairs: 445/446, 453/454, 477/478, 513/514, 531/532) | provisional, lower bound | another record, same class, <= 15 m and <= 5 s of video time; on the Mac only among the 50 sampled |
| Type correct | - | pending (review page) | reviewer: the snapshot / video shows the damage type named |
| Time / location / duplicate correct | - | pending (review page) | reviewer confirms or overrides each automatic result |
| Correctness rates, duplicate rate, fully correct | - | pending | `tools/damage_log_check.py score` (rate = yes / (yes + no), 95% Wilson; Equation 24) |

What the automatic checks show: the stored time and position follow from the frame and the GPS track exactly as the
method intends. They do not show that the damage is at that place; that is the review. Coordinates are the phone's
position when the damage was best seen (a few metres before it), so two damages side by side across the lane get
almost the same position: the 0.5-0.8 m candidate pairs (445/446, 513/514) need a look at both snapshots.

## 3. AI-flagged records of R07 (manuscript 5.1.6)

| Number | Value | Status | Source | Definition |
|---|---|---|---|---|
| Records flagged | 36 of 112 | final | `results/train_runs.md:72-75` | `ai_check_score` < 0.6 (`damage_verifier.VERIFY_THRESHOLD`) |
| Flags correct, per class | - | pending (review page, batch 2) | `tools/damage_log_check.py flagged results/damage_log_check/survey3_flagged_review.csv` | flag correct = reviewer marks "not real road damage"; share = correct / (correct + wrong), 95% Wilson |

This is the precision of the flag among flagged records only; the flag's recall (false detections it did not flag)
would need every record reviewed.

## 4. Positional consistency between repeat drives (manuscript 5.4, RQ3; not absolute accuracy)

`tools/repeat_drive.py find | process | pair` -> `results/repeat_drive/`. Pending: needs `data/local/recordings.csv`,
`route_groups.csv`, `VID+GPX/` and the backend on the PC. Tested on two overlapping October dev drives on the Mac
(1.6 km overlap, 8 pairs); those numbers are not results and are not in `results/`.

| Number | Status | Definition |
|---|---|---|
| Overlapping recording pairs (train/val only; test groups G05, G13, G15 = R06, R19, R21 excluded) | pending | video seconds of A within 15 m of B's track; >= 100 m kept; direction from headings |
| Pairs of the same damage | pending | same class, Haversine <= 15 m, one-to-one, closest first, both inside the overlap |
| Distance: n, mean, SD, median, max (all; same direction; opposite direction) | pending | Haversine (Equation 25) between the two drives' coordinates |
| Pairs at 5 / 10 / 20 / 30 m | pending | how much the 15 m cut decides |
| GPS accuracy, rate, time offset, clock skew per recording | pending (5 of 18 known, section 5) | GPX `<bk:capture>` and `<bk:accuracy>` |

Must be described as repeatability of positions between drives, not accuracy: no reference position was surveyed.
Opposite-direction pairs include about twice the camera look-ahead. Train recordings' detections are in-sample.

## 5. Device tests (manuscript 4.2.5, 5.5)

`tools/device_tests.py` -> `results/device_tests.md/.csv` (PC, all 18 recordings, with video size and bitrate).
Provisional, GPX only (5 of 18): `results/device_tests_gpx_in_repo.md/.csv`.

| Recording | Part | Duration (s) | GPS fixes | GPS rate (Hz) | Gaps > 3 s | Accuracy mean / max (m) | Offset (s) | Skew (ms) | Gap after previous part (s) |
|---|---|---|---|---|---|---|---|---|---|
| R05 | 2 | 590.00 | 606 | 1.003 | 0 | 5.0 / 10.0 | 9.314 | 102 | (part 1 not here) |
| R06 | 3 | 590.04 | 607 | 1.003 | 0 | 4.7 / 4.7 | 9.957 | 102 | 0.644 |
| R07 | 4 | 590.00 | 607 | 1.003 | 0 | 4.7 / 7.9 | 9.607 | 98 | 0.606 |
| 20261103T032025-13ow (R id on the PC) | 1 | 589.17 | 560 | 0.941 | 4 (longest 12.0 s) | 4.7 / 4.7 | 0.131 | 99 | - |
| 20261103T033015-slko (R id on the PC) | 2 | 590.04 | 607 | 1.003 | 0 | 4.7 / 4.7 | 9.793 | 98 | 1.490 |

Definitions and sources: duration = the original video's duration from `frontend/public/samples/samples.json`
(`full_duration_s`, ffprobe at export); GPS rate = (fixes - 1) / track span; gap = more than 3 s between fixes
(the app's own rule, `mobile/src/gpx.js` `findGaps`); accuracy = iOS `horizontalAccuracy` written per fix
(`<bk:accuracy>`): iOS reports 4.7 m for 97-100% of fixes, so it is the device's floor value, not a measurement;
offset and skew = `timeOffsetS` (Equation 16) and `clockSkewMs` from the GPX; gap after previous part =
videoStart(N) - videoStart(N-1) - duration(N-1), using the app's record-call clock times. Offsets of about 9.3-10 s
on parts 2-4 are the GPS pre-roll kept before each part's video start, not an error.

Pending on the PC: file size and bitrate (the app requests 5 Mbit/s), all 18 recordings, ended-early parts.
**Not performed** (cannot be measured from files): the video start-time gap (stopwatch), the midday heat test,
observed full-length sessions in a moving vehicle. Whether a part was interrupted by locking the phone is stored
only on the phone (`endReason`), not in the GPX or video; a part shorter than 585 s is listed as "ended early".

---

## Run order on the Windows PC

From the repo (`C:\Users\GIAN\Downloads\thesisproto`), after pulling this commit. **Do not "Analyse again" survey 3.**

1. Classifier, first, because the repeat drives need the decision:
   - `rmdir /s data\local\classification\test`; look for the printed test number (section 3 of `classifier_report.md`).
   - `python ml/local/classifier_val_compare.py` (validation only) -> `results/classifier_val_compare.md`.
   - Decide (rule proposed in `classifier_metric_definitions.md`). To match the evaluated system: set
     `"enabled": false` under `"classifier"` in `ml/models/model_config.json`, restart the backend.
2. Damage log and AI flags:
   - `python tools/damage_log_auto.py` (now from the database: exact times, all 112 records for duplicates).
   - `python tools/review_log/server.py`, open http://127.0.0.1:8771; batch 1 (50) then batch 2 (36). Autosaves.
   - `python tools/damage_log_check.py score results/damage_log_check/survey3_checklist.csv`
   - `python tools/damage_log_check.py flagged results/damage_log_check/survey3_flagged_review.csv`
3. Repeat drives (classifier off, backend restarted):
   - `python tools/repeat_drive.py find`, then check `results/repeat_drive/overlaps.md`.
   - `python tools/repeat_drive.py process --password <admin password>` (about 12 min per recording; R07 = survey 3
     is reused; R05's survey 2 is from an earlier model and is re-analysed).
   - `python tools/repeat_drive.py pair` -> `results/repeat_drive/positional_consistency.md`.
4. Device tests: `python tools/device_tests.py` -> `results/device_tests.md`.
5. Commit the results and update this file.

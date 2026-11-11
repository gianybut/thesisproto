# Final metrics for the paper (single authoritative list)

Compiled 2026-11-11 from existing result files and logs only. Nothing was run on the test set to write this file.
Every number cites its source as `file:line` (or a file plus column). "NOT MEASURED" means no result file holds the number.
Arithmetic done for this file (sums, one division) is marked **(computed here)** with the inputs it used.

Abbreviations: **reviewed val** = the 270 single-reviewer val frames (122 boxes), the model-selection set;
**full val** = all 1,624 val frames (659 boxes); **test** = the 270 reviewed test frames (99 boxes).

---

## 1. The deployed model

| Item | Value | Source |
|---|---|---|
| Members | `oculubak_v2b.pt` at 1024 px; `oculubak_v3.pt` at 1280 px; `oculubak_S5_v8m_1920.pt` at 1280 px | `ml/models/model_config.json` (`weights`, `imgsz`, `ensemble`) |
| Fusion | weighted box fusion of the three members' boxes (`backend/services/box_fusion.py`); each member runs at conf 0.05, then the threshold applies to the fused score | `results/deployment.md:7`; `ml/local/calibrate_threshold.py:95` (`MEMBER_CONF`) |
| Input | the near-zone crop of the road band, 1920x432, with 24 px of grey added above and below; TTA off | `model_config.json` (`border_px` 24, `tta` false); `results/final_selection.md:3` |
| Threshold | 0.25 on the fused score, NMS IoU 0.45 | `model_config.json` (`conf_threshold`, `iou_threshold`); `results/threshold_calibration.md:5` |
| How the threshold was chosen | max overall F1 over conf 0.01-0.50 on reviewed val | `ml/local/calibrate_threshold.py:7-12`, `:43` |
| Deployed | 2026-11-11 13:14, before the test evaluation | `results/deployment.md:3` |

How each member (and its ancestors) was trained. Optimizer, epochs and image size are from each run's `args.yaml` and `run_info.json`.
"Epochs run / best" is from each run's `results.csv`. best.pt = the epoch with the highest mAP@50-95 on the run's own val list (see §12).

| Model | Starting weights | Training data | RDD2022 replay | imgsz | Batch | Optimizer, lr0 | Epochs set / run / best (best.pt) | Val list used during training | Sources |
|---|---|---|---|---|---|---|---|---|---|
| **v2b** (member) | external YOLOv8s RDD2022 checkpoint (SreekarAditya, CC BY 4.0, `yolov8s_seed0_best.pt`) | v1's list `v1_train.txt`: 4,783 local near-zone images per epoch (every damage frame, D10/D20/D40 x3, 1,500 no-damage frames) | none | 1024 | 12 | SGD, 0.001, close_mosaic 10 | 40 / 40 / 13 | full val (1,624) | `runs/local/v2b/args.yaml:3-9,19,26,74`; `runs/local/v2b/data/v1.yaml`; `results/train_runs.md:19,42,77-86`; `runs/local/v2b/results.csv` |
| **v3** (member) | S5_v8m_1920 (ours) | v1's list, 4,783 local images per epoch | none in this stage (its ancestors had replay) | 1280 | 4 | SGD, 0.001, close_mosaic 5 | 20 / 20 / 16 | reviewed val (270) | `runs/local/v3/args.yaml:3-9,19,26,74`; `runs/local/v3/data/v1.yaml`; `results/train_runs.md:43`; `runs/local/v3/results.csv` |
| **S5_v8m_1920** (member) | B v2 (ours) | `B_train.txt`: 1,414 images per epoch = 814 local near-zone (526 reviewed train frames, D10/D20/D40 x3) + 600 RDD2022 | **yes, 600 images** | **1920** (trained) / 1280 (deployed) | 2 | AdamW, 0.0005, cos_lr | 40 / 10 / 8 (stopped by its time limit, unfinished) | reviewed val (270) | `runs/v3/S5_v8m_1920/args.yaml:3-9,19,74`; `runs/v3/S5_v8m_1920/data/B_train.txt` (1,414 lines, 600 RDD2022 paths); `results/local_datasets_nz.md:34-38`; `results/train_runs.md:18`; `runs/v3/S5_v8m_1920/results.csv` |
| B v2 (ancestor of S5) | teacher | `B_train.txt`: 1,336 = 736 local (road band) + 600 RDD2022 | yes, 600 | 1280 | 4 | SGD, 0.001 | 40 / 26 / 16 | reviewed val (270) | `runs/v2/Bv2/args.yaml`; `runs/v2/Bv2/data/B_train.txt`; `results/local_datasets.md:13-15`; `results/train_runs.md:16` |
| teacher (ancestor of B v2) | yolov8m.pt (COCO) | RDD2022 six countries, 5,750 train images | n/a (RDD2022 only) | 960 | 6 | auto, 0.01 | 30 / 30 / 28 | RDD2022 `val_small.txt` (900) | `runs/teacher/teacher/run_info.json`; `runs/teacher/teacher/args.yaml:4-9`; `data/rdd2022/teacher/data.yaml`, `train.txt`; `runs/teacher/teacher/results.csv` |

The v2b starting checkpoint was trained by its author on RDD2022 at 640 px, 100 epochs (`results/train_runs.md:81`).

## 2. Local test (PRIMARY): the deployed fusion

Near-zone, run once on 2026-11-11 (17:09:20 to 17:27:37, `results/test_eval_done.json`), team-approved. AP at conf 0.001, NMS IoU 0.7, grey border 24 px.

**Test set:** 270 frames (207 with no damage), 99 boxes: D00 36, D10 8, D20 34, D40 21. Sources: `results/local_datasets_nz.md:9`; `results/test_evaluation.md:5`.

| Row | mAP@50 | mAP@50-95 | AP@50 D00 | AP@50 D10 | AP@50 D20 | AP@50 D40 | Source |
|---|---|---|---|---|---|---|---|
| **Near zone (primary), fused** | **0.173** | **0.057** | 0.381 | 0.124 | 0.152 | 0.035 | `results/test_evaluation.md:13-18` |
| Full band (secondary) | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | `test_eval.py` (full band) was never run; `results/test_eval_done.json` records only `test_eval_nz.py`, run 1 |

At the deployed threshold (0.25), near zone, fused:

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 | Source |
|---|---|---|---|---|---|---|---|---|
| D00 | 36 | 17 | 22 | 19 | 0.44 | 0.47 | 0.45 | `test_evaluation.md:31` |
| D10 | 8 | 3 | 18 | 5 | 0.14 | 0.38 | 0.21 | `test_evaluation.md:32` |
| D20 | 34 | 3 | 6 | 31 | 0.33 | 0.09 | 0.14 | `test_evaluation.md:33` |
| D40 | 21 | 1 | 8 | 20 | 0.11 | 0.05 | 0.07 | `test_evaluation.md:34` |
| **All classes** | 99 | 24 | 54 | 75 | **0.31** (95% CI 21.6%-41.7%) | **0.24** (95% CI 16.9%-33.5%) | **0.27** | `test_evaluation.md:25,35` |

Each member alone, from the same single run. Only mAP was computed per member; P/R/F1 at a threshold for single members on test: NOT MEASURED.

| Model | P* | R* | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | Source |
|---|---|---|---|---|---|---|---|---|---|
| fused (deployed) | 0.227 | 0.311 | 0.173 | 0.057 | 0.381 | 0.124 | 0.152 | 0.035 | `test_evaluation.md:80` |
| v2b alone (1024) | 0.157 | 0.264 | 0.146 | 0.056 | 0.334 | 0.077 | 0.130 | 0.041 | `test_evaluation.md:81` |
| v3 alone (1280) | 0.162 | 0.281 | 0.160 | 0.055 | 0.337 | 0.171 | 0.100 | 0.032 | `test_evaluation.md:82` |
| S5_v8m_1920 alone (1280) | 0.423 | 0.132 | 0.141 | 0.051 | 0.350 | 0.130 | 0.070 | 0.016 | `test_evaluation.md:83` |

\* P and R in this table are Ultralytics' summary values (at the confidence of best F1), not the values at the 0.25 threshold. Do not mix them with the table above.

## 3. Validation results (model selection)

Selection table: `results/final_selection.md:7-33` (25 single models and fusions, 24 px border, conf 0.001). The deployed row:

| Set | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | Source |
|---|---|---|---|---|---|---|---|
| **Reviewed val (270 frames, 122 boxes), selection set** | **0.275** | 0.095 | 0.519 | 0.179 | 0.027 | 0.376 | `final_selection.md:10`; same in `test_evaluation.md:13-18,76` |
| Full val (1,624 frames, 659 boxes) | 0.161 | 0.062 | NOT MEASURED (per-class AP on full val not in the file) | | | | `final_selection.md:10` |

At the 0.25 threshold:

| Set | P | R | F1 | Source |
|---|---|---|---|---|
| Reviewed val | 0.37 | 0.30 | 0.33 | `threshold_calibration.md:15`; `test_evaluation.md:24` |
| 1,354 annotation-site val frames | 0.31 | 0.17 | 0.22 | `threshold_calibration.md:25` |
| Full val | 0.32 | 0.19 | 0.24 | `threshold_calibration.md:35` |

**The two figures in plain words.**
- **0.275** comes from the 270 val frames that one reviewer labelled by hand, with the same rules as the test frames. We picked the model and the threshold by looking at these frames, so the figure is optimistic.
- **0.161** comes from all 1,624 val frames: the same 270 frames plus 1,354 frames labelled on the shared annotation site. Those site labels were made from pre-drawn model boxes and are not labelled the same way as the test set (`results/val_sets_comparison.md:5`).

**Which one the paper should use:** **0.275 (reviewed val)** as the validation figure, named as the selection set, with 0.161 (full val) beside it.
- It is the only validation set labelled the same way as the test set, so validation and test can be compared directly.
- Full val is not untouched by selection either: a candidate was adopted only if full val agreed (`results/train_runs.md:65-67`).

## 4. Where does "41.1% mAP@50" come from?

**It does not appear as an mAP@50 in any result file.** I searched all result files, docs, commit messages and every training run's `results.csv`. No mAP@50 of 0.411 exists; the highest mAP@50 in any of our training logs is the teacher's 0.4796 on RDD2022 val (`runs/teacher/teacher/results.csv`, epoch 30).

The only 0.411 values found are **precision**, not mAP@50:
- `results/test_evaluation.md:68` (and `results/final_S5_v8m_1920_foreign_test.md:7`): **S5_v8m_1920 alone, foreign test (RDD2022, six countries), P = 0.411**. Its mAP@50 there is 0.318.
- `results/weights_benchmark_nz_val.csv:27`: an external SreekarAditya YOLOv9s checkpoint, precision 0.4116 at conf 0.15 on reviewed val (column `P_at_0.15`).

If "41.1% mAP@50" is quoted anywhere, it is wrong and must be removed.

## 5. Foreign test (SECONDARY): Table 5.F as finalised

RDD2022 test part, 15% of each of six countries (seed 42), 3,277 images. Standard Ultralytics validation (conf 0.001, NMS IoU 0.7).
Each member alone at its deployed size; the fusion was not scored on foreign images. Source: `results/test_evaluation.md:62-70`.
Per-country tables: `results/final_v2b_foreign_test.md`, `results/final_v3_foreign_test.md`, `results/final_S5_v8m_1920_foreign_test.md`.

| Model | Eval size | Images | P | R | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | Held out | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v2b | 1024 | 3277 | 0.323 | 0.269 | 0.200 | 0.068 | 0.290 | 0.179 | 0.190 | 0.143 | **NOT HELD OUT** | `test_evaluation.md:66` |
| v3 | 1280 | 3277 | 0.337 | 0.305 | 0.239 | 0.084 | 0.330 | 0.242 | 0.230 | 0.154 | yes | `test_evaluation.md:67` |
| S5_v8m_1920 | 1280 | 3277 | 0.411 | 0.369 | 0.318 | 0.127 | 0.406 | 0.284 | 0.328 | 0.254 | yes | `test_evaluation.md:68` |

- **v2b is not held out:** it starts from an external checkpoint trained on its author's own split of RDD2022, which very likely includes these test images (`results/train_runs.md:84-86`; `results/pretrained_sources.md`).
- **v3 and S5_v8m_1920 count as held out:** their RDD2022 images (teacher training data and the 600 replay images) come from our own six-country train split, which is disjoint from this test part (`ml/eval_foreign.py:6-7`).

## 6. Extra metrics, fixed before the test

Both were defined in `results/metric_definitions.md` (§3 and §4) before the test run.

| Event | Time (+08:00) | Source |
|---|---|---|
| `metric_definitions.md` committed | **2026-11-11 17:05:42** | git commit `7fbc094` |
| Test run started | **2026-11-11 17:09:20** | `results/test_eval_done.json` (`started`) |
| Test run finished | 2026-11-11 17:27:37 | `results/test_eval_done.json` (`finished`) |
| Test report committed | 2026-11-11 17:27:49 | git commit `a3b6d00` |

The definitions were fixed 3 min 38 s before the test started.

**Classification accuracy among detections** (threshold 0.25; detections matched to a reviewed box at IoU >= 0.5, any class):

| Set | Matched | Correct class | Accuracy (95% CI) | Source |
|---|---|---|---|---|
| Test | 25 | 24 | **96.0%** (80.5%-99.3%) | `test_evaluation.md:42` |
| Reviewed val | 40 | 37 | 92.5% (80.1%-97.4%) | `test_evaluation.md:41` |

The only wrong class on test was one D10 box detected as D40 (`test_evaluation.md:48-51`).

**High-confidence operating point** (lowest threshold with reviewed-val precision >= 0.80):

| Set | Threshold | Correct | False alarms | Missed | Precision | Recall | Source |
|---|---|---|---|---|---|---|---|
| Reviewed val | 0.62 | 1 | 0 | 121 | 1.00 | 0.01 | `test_evaluation.md:57` |
| Test | 0.62 | 4 | 0 | 95 | 1.00 | 0.04 | `test_evaluation.md:58` |

On val this point rests on a single detection, so it is not a usable operating point (`test_evaluation.md:60`). Report it as "precision >= 0.80 is reached only at near-zero recall".

## 7. Second-stage classifier

**NOT MEASURED.** No second-stage classifier was trained: there is no classification run under `runs/` and no `-cls` weights in `ml/models/`.

The app's "AI check" (`backend/services/damage_verifier.py`) is a different thing. It is a zero-shot CLIP ViT-B/16 that flags likely false detections, and it was never trained on our data. Its only figures come from 38 records of one survey (AUC 0.94; 14 of 15 real damages passed, 18 of 23 false detections flagged; `damage_verifier.py:14-19`). That file itself says to check a second survey before citing them.

## 8. Other evaluations

| Evaluation | Status | Result | Source |
|---|---|---|---|
| Damage log correctness (RQ2) | checklist exported, **not filled in** | **NOT MEASURED** | `results/damage_log_check/survey3_checklist.csv` (50 random records of survey 3, seed 42; answer columns blank); scorer `tools/damage_log_check.py score` |
| Localization accuracy in metres (RQ3) | no measurement made | **NOT MEASURED** | no result file |
| Annotation agreement with the expert validator | Google Form not used (too slow); the two-page validation sheet and certification letter were prepared but are **not yet signed** | **NOT MEASURED** (no agreement figure) | `data/local/validation_sheet/OcuLubak_dataset_validation.docx`; `ml/local/annotation_agreement.py` was never run on answers |
| User acceptance testing | not done | **NOT MEASURED** | no result file |

## 9. Comparison: the RDD2022-only teacher and the stand-in model on local val

Both were evaluated zero-shot (no local training) on reviewed val. Neither is the deployed model.

| Model | What it is | Set | imgsz | mAP@50 | D00 | D10 | D20 | D40 | Source |
|---|---|---|---|---|---|---|---|---|---|
| Teacher (ours, YOLOv8m, RDD2022 only) | trained on 5,750 RDD2022 images, never deployed | reviewed val | 1280 | **0.090** | 0.224 | 0.017 | 0.014 | 0.105 | `results/zero_shot_nz_val.md:10` |
| Teacher | same | reviewed val | 640 | 0.066 | 0.205 | 0.014 | 0.004 | 0.042 | `results/zero_shot_nz_val.md:16` |
| Teacher | same, at its training size 960 | reviewed val | 960 | NOT MEASURED | | | | | — |
| Teacher, for reference | same | **foreign** RDD2022 val | 960 | 0.472 | 0.535 | 0.430 | 0.544 | 0.379 | `results/teacher_foreign_val.md:7` |
| Stand-in `rdd2022_pretrained.pt` (external 7-class YOLOv8n, MIT; **NOT ours**) | the demo placeholder before v1 | reviewed val, val style | 1280 | **0.155** | 0.213 | 0.000 | 0.340 | 0.069 | `results/val_sets_comparison.md:34` |
| Stand-in | same | full val, val style | 1280 | 0.037 | 0.031 | 0.000 | 0.097 | 0.020 | `results/val_sets_comparison.md:19` |
| Deployed fusion, for comparison | ours | reviewed val / full val | 1024+1280 | 0.275 / 0.161 | | | | | `results/final_selection.md:10` |

**Wording for Chapter V:**
- The teacher drops from 0.472 mAP@50 on foreign val to 0.090 on our local roads. That is the domain gap that motivated the local labels.
- The stand-in's numbers must never be reported as our results. It may appear only as an external baseline.
- None of the teacher, the stand-in or the deployed fusion has a test figure except the deployed fusion; the comparison is on val only.

## 10. Dataset numbers

| Item | Value | Source |
|---|---|---|
| Recordings made | 21 (R01-R21) | `data/local/recordings.csv` (21 rows) |
| Recordings used | 18 (R04-R21, vehicle-mounted); R01-R03 excluded (hand-held) | `recordings.csv` (`status`); `results/step1_split.md:3` |
| Hours of video used | 9,769.2 s = **2.71 h** **(computed here: sum of `duration_s`, R04-R21)** | `recordings.csv` |
| Route length | **78.26 km** **(computed here: sum of `route_km`, R04-R21; routes driven twice count twice)** | `recordings.csv` |
| Extracted frames (1 per second, R04-R21) | **9,778** | `data/local/frames_all.csv` (rows) |
| Kept after near-duplicate removal | 9,590 | `frames_all.csv` (`kept` = 1); `data/local/splits.csv` (rows) |
| Route groups | 15 defined (G01-G15); 14 hold used recordings (G02 held only hand-held ones) | `data/local/route_groups.csv`; `splits.csv` |
| Split by route group | train 8 groups / 6,103 frames; val 3 groups (G04, G06, G10) / 1,717; test 3 groups (G05, G13, G15) / 1,661 | `results/step1_split.md:9-11` |
| Frames dropped by the 50 m rule | **109** (val 19, test 90) | `results/step1_split.md:13,23`; `splits.csv` (`dropped_by_location`) |
| Human-labelled frames (near zone, final) | **7,465**: train 5,571 / val 1,624 / test 270 | `results/local_datasets_nz.md:7-9` |
| of which single-reviewer | 1,066: train 526 / val 270 / test 270 | `results/local_datasets_nz.md:29-31`; `ml/local/check_counts.py` output in the test run log ("reviewed frames 1066") |
| of which annotation site | train 5,045 / val 1,354 | `results/local_datasets_nz.md:13-14` |
| Frames with no damage | train 4,044 / val 1,314 / test 207 | `results/local_datasets_nz.md:7-9` |
| Boxes, train | D00 1,450, D10 556, D20 152, D40 779 (2,937 **(computed here)**) | `results/local_datasets_nz.md:7` |
| Boxes, val | D00 214, D10 150, D20 51, D40 244 (659) | `results/local_datasets_nz.md:8`; `results/val_sets_comparison.md:7` |
| Boxes, test | D00 36, D10 8, D20 34, D40 21 (99) | `results/local_datasets_nz.md:9`; `results/test_evaluation.md:5` |
| Boxes, all splits | 3,695 (D00 1,700, D10 714, D20 237, D40 1,044 **(computed here)**) | `check_counts.py` output: "total frames 7465, boxes 3695" |
| Reviewed val subset | 270 frames, 122 boxes (D00 30, D10 23, D20 17, D40 52) | `results/val_sets_comparison.md:22` |
| Reviewers of val/test labels | one person | `tools/review_labels/reviewers.txt` |

## 11. System performance

| Item | Value | Source |
|---|---|---|
| Model-only inference, S5_v8m_1920 alone at 1280 on a 1920x432 crop | 10.7 ms per image (this PC, RTX 4060) | `results/weights_benchmark_nz_val.md:9` (`ms/img`) |
| Model-only inference, v2b alone / v3 alone / the fusion | NOT MEASURED | — |
| R07 end to end (590 s video, the deployed fusion) | analysed in **729 s** (about 1.2x the recording length); 3,539 frames analysed at 5 fps; three models per frame | `results/train_runs.md:72-75` |
| End-to-end time per analysed frame | 0.206 s **(computed here: 729 s / 3,539 frames; includes decoding, three models, tracking, AI check and video writing)** | inputs from `results/train_runs.md:73` |
| R07 output | 112 damage records (D00 23, D10 15, D20 10, D40 64), all GPS-placed, 36 flagged by the AI check | `results/train_runs.md:74-75` |

## 12. Caveats the paper must state

1. **Small evaluation sets.**
   - Reviewed val has 122 boxes (`val_sets_comparison.md:22`); test has 99 boxes, only 8 of them D10 and 21 D40 (`test_evaluation.md:5,16,18`).
   - Differences of about 0.02 mAP are noise (`results/train_runs.md:66-67`).
   - The test precision and recall intervals are about ±10 points (`test_evaluation.md:25`).
   - Per-class test AP rests on 8 to 36 boxes.
2. **Not held out.**
   - v2b's foreign-test figure (`test_evaluation.md:66`).
   - The 0.275 reviewed-val figure: the deployed fusion, its threshold and the v3 and S5 checkpoints (best.pt) were all chosen on these 270 frames (`runs/local/v3/data/v1.yaml`, `runs/v3/S5_v8m_1920/data/B.yaml`: val = the reviewed list). It is a selection figure; **only the test figures are unbiased**.
3. **best.pt was selected on mAP@50-95.** Ultralytics' fitness weights are 0/0/0/1 on P/R/mAP@50/mAP@50-95 (`.venv/Lib/site-packages/ultralytics/utils/metrics.py:965`, Ultralytics 8.4.48), while our models are compared on mAP@50.
4. **Near-zone setting.**
   - All local figures are on the 1920x432 near-zone crop of the road band, not the whole frame.
   - Damage farther ahead is outside the evaluated area.
   - Full-band test figures: NOT MEASURED (§2).
5. **S5_v8m_1920's evaluation size differs from its training size.** It was trained at 1920 (`runs/v3/S5_v8m_1920/args.yaml:9`) but is deployed and evaluated at 1280 (`model_config.json`); on reviewed val, inference at 1280 / 1600 / 1920 gives 0.200 / 0.205 / 0.201 (`results/train_runs.md:49`). Its training also stopped unfinished at epoch 10 of 40 (`runs/v3/S5_v8m_1920/results.csv`; `results/train_runs.md:18`).
6. **Not "local labels only".** S5_v8m_1920 (a member) was trained with 600 RDD2022 replay images, and v3 starts from it (`results/train_runs.md:43,54-55`). v2b starts from an external CC BY 4.0 checkpoint, which needs attribution (`results/train_runs.md:77-91`).
7. **Validation does not predict per-class test results.**
   - Potholes (D40) fall from 0.376 AP@50 on reviewed val to 0.035 on test (1 of 21 found at 0.25).
   - Alligator cracks (D20) rise from 0.027 to 0.152 (`test_evaluation.md:17-18,34`).
8. **One reviewer** labelled all val and test boxes (`tools/review_labels/reviewers.txt`); expert validation is not yet signed (§8).

---

## Numbers to quote

**Abstract**
- Test, deployed fusion (v2b + v3 + S5_v8m_1920): **mAP@50 0.173** (17.3%), mAP@50-95 0.057 (`test_evaluation.md:13-14`).
- Test, deployed fusion, threshold 0.25: **precision 0.31, recall 0.24, F1 0.27** (`test_evaluation.md:25`).
- Test, deployed fusion: **96.0% of matched detections have the correct damage type** (24/25) (`test_evaluation.md:42`).
- Dataset: 18 recordings, 2.71 h, 78.26 km **(computed here)**; 7,465 human-labelled frames, 3,695 boxes (`local_datasets_nz.md:7-9`).
- System, R07: a 590 s survey analysed in 729 s, 112 damage records, all GPS-placed (`train_runs.md:72-75`).

**Chapter V**
- Table 5.A-5.F as in `results/test_evaluation.md`: validation = reviewed val (selection set), test = test.
- Val (reviewed, selection set), deployed fusion: mAP@50 0.275; P 0.37 / R 0.30 / F1 0.33 at 0.25. Full val beside it: 0.161 and F1 0.24.
- Test, deployed fusion, per class AP@50: D00 0.381, D10 0.124, D20 0.152, D40 0.035.
- Test, members alone (mAP@50): v2b 0.146, v3 0.160, S5_v8m_1920 0.141. The fusion (0.173) beats each member.
- Foreign test (secondary), members alone (mAP@50): v3 0.239 (held out), S5_v8m_1920 0.318 (held out), v2b 0.200 (**not held out**).
- Comparison on reviewed val: RDD2022-only teacher 0.090 (foreign val 0.472); external stand-in 0.155 (not ours); deployed fusion 0.275.
- High-confidence point, test: threshold 0.62, P 1.00, R 0.04. Not a usable operating point.
- NOT MEASURED, to be stated as future work or pending: damage log correctness (RQ2), localization in metres (RQ3), expert agreement, user acceptance, second-stage classifier, full-band test.

**Message to the adviser**
- "On the held-out local test set (270 frames, 99 boxes), the deployed model, a fusion of three YOLOv8 models, reaches **mAP@50 0.173**, with **precision 0.31, recall 0.24 and F1 0.27** at its threshold of 0.25. **96% of the damages it finds are given the correct type.**"
- "On the validation frames used to choose the model it scored 0.275 mAP@50. The drop shows how much optimism model selection adds on a set this small."
- "Potholes are the weakest class on test (AP@50 0.035), although they were the second-best class on validation."
- "Damage log correctness, localization accuracy, the expert's validation and user acceptance are not measured yet."

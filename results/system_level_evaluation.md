# System-level evaluation of the deployed pipeline (local test, 270 frames)

> **Note.** These system-level metrics were adopted after the initial box-level evaluation, at the
> adviser's recommendation, to reflect how the system is used. (Decision: `docs/decisions.md`,
> 2026-11-15, per adviser consultation.)

Computed 2026-11-15 by `ml/local/system_level_eval.py`; every number below is in
`results/system_level_evaluation.json`. Nothing was retrained. The deployed model, fusion, threshold
(0.25) and road band were not changed, and the test set was not used to select anything. Each
comparator's threshold was chosen on the 270 reviewed val frames only. All values are reported as
they came out.

## 0. Data, pipeline and how the predictions were obtained

- **Test set:** `data/local/yolo_nz/test.txt`, 270 near-zone frames (1920×432) from route groups G05,
  G13 and G15. **63 frames show damage and 207 show none.** There are 99 reviewed boxes (D00 36, D10 8,
  D20 34, D40 21). Frames containing each class: D00 26, D10 5, D20 27, D40 17. All labels were
  reviewed by one person (`results/metric_definitions.md`, "Data").
- **Validation set** (threshold choice for the comparators only): `val_reviewed.txt`, 270 frames,
  63 with damage. These are the frames the deployed model and its 0.25 threshold were chosen on.
- **Deployed fusion** (`ml/models/model_config.json`, deployed 2026-11-11 13:14):
  - members: v2b (1024 px), v3 (1280 px) and S5_v8m_1920 (1280 px)
  - each member at conf 0.05 and NMS IoU 0.45, with a 24 px grey border
  - members combined by weighted box fusion (`backend/services/box_fusion.py`); the fused score must be ≥ 0.25
  - this is the configuration test-evaluated on 2026-11-11 (`results/test_evaluation.md`)
- **Saved predictions:** none existed. `test_eval_nz.py` kept its detections in memory only.
  Inference was therefore re-run on the 270 test and 270 val frames only. Raw detections are cached
  in `data/local/system_eval/` (gitignored).
- **Reproduction check:** at 0.25 the re-run gives box-level 24 correct, 54 false alarms and 75
  missed, and classification 24/25. Both are identical to `results/test_evaluation.md`
  Tables 5.B and 5.D (JSON `fusion.box_check_test`).
- **Second-stage classifier (found during this evaluation):** since commit `5d796a1` (2026-11-12
  10:40), `model_config.json` has `classifier.enabled: true`.
  - The backend runs `ml/models/classifier.pt` (YOLOv8n-cls, = `runs/classify/road_damage_retry/weights/best.pt`) on every detected box.
  - Its top-1 class **replaces** the detector's class (`backend/services/video_processor.py` ~l.561-568, `damage_classifier.py`).
  - **So the pipeline deployed today is the fusion followed by this classifier.** It was not part of the 2026-11-11 test evaluation.
  - It changes only the damage type; which frames have detections is unchanged.
  - It is reported as a second row ("fusion + classifier"), and in §4.
  - `results/FINAL_METRICS_FOR_PAPER.md` §7 ("No second-stage classifier was trained") was written before this commit and is out of date on this point.

## 1. Definitions (and sources)

| Measure | Definition | Source |
|---|---|---|
| Frame positive (reviewed) | The frame has ≥ 1 reviewed box | Adopted 2026-11-15 (this task) |
| **A. Damage present** | Predicted positive = ≥ 1 detection at the threshold. TP = reviewed-positive and predicted positive; FP = reviewed-negative and predicted positive; FN = reviewed-positive and not predicted; TN = neither | Adopted 2026-11-15 |
| Hit | A detection hits a reviewed box if the detection's centre lies inside the reviewed box, or IoU ≥ 0.25 | Adopted 2026-11-15 |
| **B. Damage present with the correct type** | Reviewed-positive frame: TP if some detection hits a reviewed box **of the same class**, otherwise FN (also when the frame has detections, but none hits a box of its class). Reviewed-negative frame: FP if it has any detection, otherwise TN | Adopted 2026-11-15 |
| **C. Per class c** | B restricted to class c. Positive = the frame has a reviewed c box. TP = a c detection hits a c box. FP = a frame with no reviewed c box but a c detection (that frame may show another class). TN = neither. A presence-only variant (no hit needed) is in the JSON (`per_class_present`) | Adopted 2026-11-15 |
| Accuracy | (TP + TN) / N, N = 270 | standard |
| Precision | TP / (TP + FP) | standard |
| Recall | TP / (TP + FN) | standard |
| F1 | 2·P·R / (P + R) = 2TP / (2TP + FP + FN) | standard |
| 95% CI | Wilson score interval for accuracy, precision and recall (as in `test_eval_nz.wilson`). F1 is not a proportion, so it has no Wilson interval: its interval is a frame-level bootstrap percentile interval (10,000 resamples, seed 42) | Wilson: `results/metric_definitions.md` §2-3; bootstrap: this task |
| Classification accuracy | Among detections at 0.25 matched one-to-one to a reviewed box at IoU ≥ 0.5 (any class), the share whose class equals the reviewed class | `results/metric_definitions.md` §3 (unchanged) |
| Comparator threshold | The threshold in 0.01…0.99 maximising definition-A F1 on the 270 reviewed val frames (ties: higher threshold) | This task |
| Record-level measures | Record precision (real damage), type correctness, location correctness and duplicate rate on 50 random R07 records (seed 42) | `tools/damage_log_check.py` |

**Reading accuracy.** 207 of 270 test frames (76.7%, CI 71.3–81.3%) have no damage. A system that
never reports damage would therefore score accuracy 0.767 with recall 0. Accuracy must be read next
to recall and precision. The same holds even more for the per-class accuracies, where 243–265 of
270 frames are negatives.

## 2. Frame-level detection, deployed fusion at 0.25 (headline)

**Table S1. Test, 270 frames (63 with damage).**

| Measure | Pipeline | TP | FP | FN | TN | Accuracy (95% CI) | Precision (95% CI) | Recall (95% CI) | F1 (95% CI, bootstrap) |
|---|---|---|---|---|---|---|---|---|---|
| A. Damage present | fusion | 34 | 24 | 29 | 183 | **0.804** (75.2–84.7%) | 0.586 (45.8–70.4%) | 0.540 (41.8–65.7%) | 0.562 (44.9–66.2%) |
| A. Damage present | fusion + classifier | 34 | 24 | 29 | 183 | 0.804 (75.2–84.7%) | 0.586 (45.8–70.4%) | 0.540 (41.8–65.7%) | 0.562 (44.9–66.2%) |
| B. Correct type | fusion | 25 | 24 | 38 | 183 | 0.770 (71.7–81.7%) | 0.510 (37.5–64.4%) | 0.397 (28.5–52.0%) | 0.446 (32.7–55.6%) |
| B. Correct type | fusion + classifier | 23 | 24 | 40 | 183 | 0.763 (70.9–81.0%) | 0.489 (35.3–62.8%) | 0.365 (25.7–48.9%) | 0.418 (29.8–52.9%) |

78 detections at 0.25 on test. In 34 − 25 = 9 positive frames the fusion fired, but no detection hit
a reviewed box of the right class.

**Table S2. For comparison: the same on the 270 reviewed val frames (the selection set, so optimistic).**

| Measure | Pipeline | TP | FP | FN | TN | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| A. Damage present | fusion | 43 | 33 | 20 | 174 | 0.804 | 0.566 | 0.683 | 0.619 |
| B. Correct type | fusion | 37 | 33 | 26 | 174 | 0.781 | 0.529 | 0.587 | 0.556 |
| B. Correct type | fusion + classifier | 36 | 33 | 27 | 174 | 0.778 | 0.522 | 0.571 | 0.545 |

**Table S2b. All 1,624 validation frames** (270 reviewed + 1,354 annotation-site frames; 310 with damage). Added
2026-11-15 for manuscript Table 5.1.4 with `python ml/local/system_level_eval.py --val-all`. Validation only; nothing
is selected on it. JSON `val_all_1624`.

| Measure | Pipeline | TP | FP | FN | TN | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| A. Damage present | fusion (= fusion + classifier) | 165 | 147 | 145 | 1167 | 0.820 | 0.529 | 0.532 | 0.531 |
| B. Correct type | fusion | 135 | 147 | 175 | 1167 | 0.802 | 0.479 | 0.435 | 0.456 |
| B. Correct type | fusion + classifier | 129 | 147 | 181 | 1167 | 0.798 | 0.467 | 0.416 | 0.440 |

## 3. Per class (definition C), test, 270 frames

**Table S3. Deployed fusion at 0.25.**

| Class | Frames with the class | TP | FP | FN | TN | Accuracy (95% CI) | Precision (95% CI) | Recall (95% CI) | F1 (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| Longitudinal crack (D00) | 26 | 14 | 15 | 12 | 229 | 0.900 (85.8–93.0%) | 0.483 (31.4–65.6%) | 0.538 (35.5–71.2%) | 0.509 (33.3–65.7%) |
| Transverse crack (D10) | 5 | 3 | 15 | 2 | 250 | 0.937 (90.1–96.0%) | 0.167 (5.8–39.2%) | 0.600 (23.1–88.2%) | 0.261 (0.0–48.5%) |
| Alligator crack (D20) | 27 | 7 | 0 | 20 | 243 | 0.926 (88.8–95.2%) | 1.000 (64.6–100%) | 0.259 (13.2–44.7%) | 0.412 (18.2–60.9%) |
| Pothole (D40) | 17 | 1 | 6 | 16 | 247 | 0.919 (88.0–94.6%) | 0.143 (2.6–51.3%) | 0.059 (1.0–27.0%) | 0.083 (0.0–25.0%) |

**Table S4. Fusion + classifier (deployed since 2026-11-12) at 0.25.**

| Class | Frames | TP | FP | FN | TN | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| D00 | 26 | 14 | 16 | 12 | 228 | 0.896 | 0.467 | 0.538 | 0.500 |
| D10 | 5 | 2 | 12 | 3 | 253 | 0.944 | 0.143 | 0.400 | 0.211 |
| D20 | 27 | 6 | 1 | 21 | 242 | 0.919 | 0.857 | 0.222 | 0.353 |
| D40 | 17 | 1 | 10 | 16 | 243 | 0.904 | 0.091 | 0.059 | 0.071 |

Rare classes: D10 has 5 positive frames and D40 17, so their intervals are very wide. The
per-class accuracies (0.90–0.94) come almost entirely from true negatives. For example, D40 accuracy
is 0.919 while D40 recall is 0.059 (1 of 17 frames).

## 4. Classification accuracy

**Box-level (definition from `results/metric_definitions.md` §3), test, at 0.25:**

| Pipeline | Matched detections | Correct class | Accuracy (95% Wilson CI) |
|---|---|---|---|
| Fusion (as test-evaluated 2026-11-11) | 25 | 24 | **96.0% (80.5–99.3%)**, confirmed (`test_evaluation.md` Table 5.D, reproduced by this re-run) |
| Fusion + classifier (deployed since 2026-11-12) | 25 | 23 | 92.0% (75.0–97.8%) |

- Fusion errors: one D10 labelled D40.
- Fusion + classifier errors: two D10 labelled D40. Its matched pairs, reviewed × assigned: D00 17/0/0/0; D10 0/2/0/2; D20 0/0/3/0; D40 0/0/0/1.
- In this pipeline the classifier did not improve type decisions. It made them slightly worse: 23 vs 24 of 25 matched, and 23 vs 25 frames under definition B. The differences are 1-2 detections, within the intervals.

**Second-stage classifier on held-out crops.**

- Test crops: `data/local/classification/test`, 99 crops of the reviewed test boxes, 25% context padding, built by `ml/build_classifier_dataset.py`.
- Its training list (`local_train.txt`, 5,571 frames) shares no frame with `test.txt`.
- Its checkpoint was picked by Ultralytics on val top-1 (0.820; `runs/classify/road_damage_retry/results.csv`).

| | Predicted D00 | Predicted D10 | Predicted D20 | Predicted D40 | Recall (95% CI) |
|---|---|---|---|---|---|
| **Reviewed D00** (36) | 35 | 0 | 0 | 1 | 97.2% (85.8–99.5%) |
| **Reviewed D10** (8) | 0 | 4 | 0 | 4 | 50.0% (21.5–78.5%) |
| **Reviewed D20** (34) | 4 | 1 | 25 | 4 | 73.5% (56.9–85.4%) |
| **Reviewed D40** (21) | 0 | 0 | 0 | 21 | 100.0% (84.5–100%) |
| Precision (95% CI) | 89.7% (76.4–95.9%) | 80.0% (37.6–96.4%) | 100.0% (86.7–100%) | 70.0% (52.1–83.3%) | |

**Overall top-1 accuracy on held-out test crops: 85/99 = 85.9% (95% CI 77.7–91.4%).**

- This scores the classifier on **reviewed** boxes (ideal crops with padding).
- In the app it sees the **detector's** boxes, cropped without padding (`classify_crop`). That is a train/deploy mismatch, and it may explain why it does not help in the pipeline (above).
- It is part of the deployed pipeline (`classifier.enabled: true`). All 112 R07 records (survey 3, analysed 2026-11-12 02:52 UTC) carry a `classification_type`.

## 5. Comparison with pretrained models (same 270 test frames, same frame-level metrics)

**Comparator settings:**
- the app's settings: imgsz 1280 (`INFERENCE_IMGSZ`), NMS IoU 0.45, grey border 24 px
- classes mapped as the backend maps them (`DAMAGE_CLASS_MAP`); the stand-in's `block`, `crack` and `edge` classes are dropped, as the app drops them
- each comparator at its definition-A best-F1 threshold on the 270 reviewed val frames

The deployed fusion keeps its 0.25. That threshold was chosen on **box-level** F1 on the same val
frames and is not re-tuned. **This asymmetry favours the comparators.**

**Table S5. Test, 270 frames. Deployed fusion first.**

| Model | Threshold (chosen on val) | Detections | A: Accuracy | A: Precision | A: Recall | A: F1 (95% CI) | B: Accuracy | B: Precision | B: Recall | B: F1 |
|---|---|---|---|---|---|---|---|---|---|---|
| **Deployed fusion (v2b + v3 + S5_v8m_1920)** | 0.25 (box-level F1, 2026-11-11) | 78 | 0.804 | 0.586 | 0.540 | 0.562 (44.9–66.2%) | 0.770 | 0.510 | 0.397 | 0.446 |
| Deployed fusion + classifier | 0.25 | 78 | 0.804 | 0.586 | 0.540 | 0.562 | 0.763 | 0.489 | 0.365 | 0.418 |
| Teacher (ours, RDD2022 only, YOLOv8m; never deployed) | 0.16 | 83 | 0.767 | 0.500 | 0.429 | 0.462 (34.5–56.8%) | 0.763 | 0.491 | 0.413 | 0.448 |
| SreekarAditya YOLOv8s RDD2022, seed 0 (CC BY 4.0) | 0.02 | 115 | 0.811 | 0.611 | 0.524 | 0.564 (44.7–66.7%) | 0.785 | 0.553 | 0.413 | 0.473 |
| SreekarAditya YOLOv12s RDD2022, seed 0 (CC BY 4.0) | 0.02 | 132 | 0.815 | 0.603 | 0.603 | 0.603 (50.0–69.9%) | 0.781 | 0.537 | 0.460 | 0.496 |
| Stand-in (external MIT 7-class YOLOv8n RDD2022; not the team's model) | 0.13 | 234 | 0.644 | 0.354 | 0.635 | 0.455 (35.8–54.3%) | 0.578 | 0.232 | 0.349 | 0.278 |

Full TP/FP/FN/TN, Wilson intervals, val scores and per-class rows for every comparator are in the
JSON (`comparators[*]`).

| Model | A on test: TP / FP / FN / TN | B on test: TP / FP / FN / TN | A on val: F1 |
|---|---|---|---|
| Deployed fusion | 34 / 24 / 29 / 183 | 25 / 24 / 38 / 183 | 0.619 |
| Teacher | 27 / 27 / 36 / 180 | 26 / 27 / 37 / 180 | 0.612 |
| SA YOLOv8s | 33 / 21 / 30 / 186 | 26 / 21 / 37 / 186 | 0.661 |
| SA YOLOv12s | 38 / 25 / 25 / 182 | 29 / 25 / 34 / 182 | 0.583 |
| Stand-in | 40 / 73 / 23 / 134 | 22 / 73 / 41 / 134 | 0.527 |

**What the comparison shows, plainly:**
- On frame-level damage presence, the deployed fusion (F1 0.562) is **not better** than the two public SreekarAditya checkpoints: YOLOv8s scores 0.564 and YOLOv12s scores 0.603.
- On damage with the correct type, the fusion scores B-F1 0.446, against 0.473 (YOLOv8s) and 0.496 (YOLOv12s). Every interval overlaps; none of these differences can be told apart on 63 positive frames.
- The fusion is ahead of the stand-in (A-F1 0.455, B-F1 0.278) and the teacher (A-F1 0.462).
- The SA thresholds (0.02) sit at the bottom of the sweep. Those models score low on local roads, and val chose a near-zero cut.
- Per class on test (definition C, F1):

| Model | D00 | D10 | D20 | D40 |
|---|---|---|---|---|
| Deployed fusion | 0.509 | 0.261 | 0.412 | 0.083 |
| Teacher | 0.444 | 0.000 | 0.571 | 0.000 |
| SA YOLOv8s | 0.500 | 0.182 | 0.419 | 0.133 |
| SA YOLOv12s | 0.540 | 0.000 | 0.426 | 0.250 |
| Stand-in | 0.513 | 0.000 | 0.244 | 0.128 |

## 6. Record-level results (R07 damage log)

**Not measured: the review is not done.**

- `results/damage_log_check/survey3_checklist.csv` lists 50 random records (seed 42) of survey 3.
  Survey 3 is R07 (`20261031T021049-3x76.mov`, Alfonso Bayan National Road; 112 records, fusion + classifier).
- All four answer columns (`type_correct`, `time_correct`, `location_correct`, `duplicate`) are
  blank in all 50 rows. Record precision, type correctness, location correctness and duplicate rate
  therefore cannot be computed yet.
- When filled in, `python tools/damage_log_check.py score results/damage_log_check/survey3_checklist.csv` gives them.
  Record precision (real damage) = rows whose snapshot shows road damage of any type. The scorer's
  `type_correct = no` mixes "another type" with "not damage", so the "not road damage" cases should
  be written in `notes` to separate the two.
- **The 36 AI-flagged R07 records** (`ai_check_score` < 0.6) have **not been reviewed**: there is no
  review file in the repository (`docs/MANUSCRIPT_TODO.md`, `[PENDING: review of flagged records]`).

## 7. The 0.80 criterion (system performance ≥ 0.80 in accuracy, precision, recall or F1)

Test set, deployed fusion at 0.25 unless stated. Point estimates against 0.80.

| Measure | Value (95% CI) | ≥ 0.80? |
|---|---|---|
| A. Damage present, accuracy | 0.804 (75.2–84.7%) | **Yes**, by 0.004. The interval reaches down to 0.752, and the "never report damage" baseline is 0.767 |
| A. Damage present, precision | 0.586 (45.8–70.4%) | No |
| A. Damage present, recall | 0.540 (41.8–65.7%) | No |
| A. Damage present, F1 | 0.562 (44.9–66.2%) | No |
| B. Correct type, accuracy | 0.770 (71.7–81.7%) (fusion + classifier 0.763) | No |
| B. Correct type, precision | 0.510 (37.5–64.4%) (0.489) | No |
| B. Correct type, recall | 0.397 (28.5–52.0%) (0.365) | No |
| B. Correct type, F1 | 0.446 (32.7–55.6%) (0.418) | No |
| C. Per-class accuracy, D00 / D10 / D20 / D40 | 0.900 / 0.937 / 0.926 / 0.919 | Yes, all four. Driven by true negatives; see §3 |
| C. Per-class precision, D00 / D10 / D20 / D40 | 0.483 / 0.167 / **1.000** (7/7, CI 64.6–100%) / 0.143 | D20 only (7 detections) |
| C. Per-class recall, D00 / D10 / D20 / D40 | 0.538 / 0.600 / 0.259 / 0.059 | No |
| C. Per-class F1, D00 / D10 / D20 / D40 | 0.509 / 0.261 / 0.412 / 0.083 | No |
| Classification accuracy among matched detections | 96.0% (80.5–99.3%), 24/25 (fusion + classifier: 92.0%, 75.0–97.8%) | Yes (lower bound 0.805 for the fusion; 0.750 with the classifier) |
| Second-stage classifier, held-out test crops | 85.9% (77.7–91.4%), 85/99 | Yes (lower bound below 0.80) |
| Record-level (R07): precision, type, location, duplicates | not measured | Pending |

**In one line.** The only frame-level measure at or above 0.80 is damage-present accuracy (0.804).
It rests largely on the 207 empty frames, and it is not distinguishable from 0.80 or from the
all-negative baseline. Precision, recall and F1 for damage detection are all below 0.80.
Classification of the damage that is found is above 0.80.

## 8. What still needs a decision or input

1. **Decided 2026-11-15: the fusion + classifier (the deployed pipeline).** The question was which pipeline the manuscript reports as "the system":
   - the fusion as test-evaluated on 2026-11-11, or
   - the fusion + classifier that has been deployed since 2026-11-12 (and that produced the R07 records).
   - Detection measures are identical; only type measures differ (slightly lower with the classifier).
2. **The R07 50-record review and the 36 flagged records** (your review, before Stage 2).
3. "17.4%": **not found** anywhere in the repository, its git history, or the four manuscript
   versions in Google Drive (revision draft 1SaaJn…, OCULUBAK_Manuscript of 2026-11-14, _combined,
   _filled) or the original "CHAPTER 1-6". The final value is **0.173** (0.17312 = mean of AP@50
   0.3807, 0.1240, 0.1524, 0.0354; `results/test_evaluation.json`, `test.maps[0]`), i.e. 17.3%.
   It does not round to 17.4% at any precision.

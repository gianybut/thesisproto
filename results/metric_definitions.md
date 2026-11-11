# Metric definitions for the test evaluation (fixed before the test is run)

Written 2026-11-11 17:06 (+08:00), before any test evaluation: `results/test_eval_done.json` does not
exist and no script has read the test labels for scoring. The git commit that adds this file is the
timestamp of record. Nothing here may be changed after the test has been evaluated.

**Model evaluated:** the deployed model as `ml/models/model_config.json` defines it on this date:
v2b (1024 px) + v3 (1280 px) + S5_v8m_1920 (1280 px), weighted box fusion (`backend/services/box_fusion.py`),
grey border 24 px, deployed threshold **0.25** (calibrated on the 270 reviewed val frames,
`results/threshold_calibration.md`). Script: `ml/local/test_eval_nz.py --team-approved`, run once.

**Data:** local test = `data/local/yolo_nz/test.txt`, 270 near-zone frames (1920x432) from route groups
G05, G13 and G15, labels reviewed by one person; 207 frames have no damage; 99 boxes (D00 36, D10 8,
D20 34, D40 21). Validation figures quoted next to the test figures come from the 270 reviewed val
frames (`val_reviewed.txt`, 122 boxes), the set the model and the threshold were chosen on.

## Matching rule (used by every metric below except mAP)

A detection and a reviewed box are paired one-to-one, greedily, highest IoU first
(`ml/local/label_quality.match`); a pair needs IoU >= 0.5. "Same class" matching only pairs boxes of
the same class; "any class" matching ignores the class.

## 1. Detection mAP@50, overall and per class (D00, D10, D20, D40)

- Every member at conf 0.001, NMS IoU 0.7, max 300 boxes, its own image size, grey border 24 px; the
  members' boxes fused with the app's weighted box fusion.
- AP per class = Ultralytics' `ap_per_class` (101-point interpolated area under the precision-recall
  curve, same-class matching at IoU 0.5); mAP@50 = mean over the four classes. mAP@50-95 is reported
  next to it (IoU 0.50:0.95). Each member alone is reported too, for information.
- The deployment threshold does not apply to mAP.

## 2. Precision, recall and F1 at the deployed threshold (0.25)

- App settings: each member at conf 0.05 and NMS IoU 0.45, fused, fused score >= 0.25.
- Same-class matching. Precision = correct / all detections; recall = correct / all reviewed boxes;
  F1 = 2PR / (P + R). Overall (all classes pooled) and per class.
- 95% Wilson intervals are given for overall precision and recall (counts are small: 99 test boxes).

## 3. Classification accuracy among detections

- At the deployed threshold (0.25), app settings as in 2.
- Any-class matching at IoU >= 0.5. Accuracy = matched detections whose class equals the reviewed
  box's class / all detections matched to a reviewed box (any class). A 4x4 table (reviewed class x
  detected class) of the matched pairs is given for information. 95% Wilson interval.
- It measures the class decision only for damage that was found; unmatched detections and missed
  boxes are in 2.

## 4. High-confidence operating point

- Thresholds 0.01 to 0.99 in steps of 0.01, app settings as in 2, on the 270 reviewed val frames.
- The operating point = the lowest threshold at which val precision (overall, same-class) >= 0.80.
- Reported: that threshold, its val precision and recall, and its precision and recall on test.
- If no threshold reaches 0.80 on val, the result is "not reached", with the highest val precision
  and its threshold; no test figure is then reported for this point.

## 5. Which result is primary

- **Primary:** the local test (sections 1 to 4).
- **Secondary:** the foreign test (RDD2022 test part of six countries, 15% per country, seed 42,
  `ml/eval_foreign.py --split test`), each member alone (the fusion is not scored on foreign
  images), standard Ultralytics validation (conf 0.001, NMS IoU 0.7). A member that starts from an
  external checkpoint (v2b: the CC BY 4.0 YOLOv8s RDD2022 model, whose own RDD2022 split is unknown)
  is marked **NOT HELD OUT**, because its starting model has very likely seen images of this test part.

## Rules

- The test is evaluated once. `results/test_eval_done.json` blocks a second run. The only allowed
  re-run is `test_eval_nz.py --team-approved --labels-corrected`, after corrections to the test
  labels (the test hash must differ from the one recorded at the first run); both runs are kept.
- No test figure may be used to change the model, the threshold or the operating point.
- All values are reported whatever they are.

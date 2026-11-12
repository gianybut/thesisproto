# Metric definitions for the second-stage classifier (validation only)

Written 2026-11-12, before `ml/local/classifier_val_compare.py` has been run on any data. The git commit
that adds this file is the timestamp of record. These definitions cover validation only: **the test set is
not used for the classifier**. The one test evaluation (`results/test_evaluation.md`, 2026-11-11, metrics
fixed in `results/metric_definitions.md`) scored the fusion without the classifier and stays the only test
result of this study.

**Classifier evaluated:** `ml/models/classifier.pt` (YOLOv8n-cls, 224 px, trained 2026-11-12 10:17 on the
Windows training PC, run `runs/classify/road_damage_retry`, best epoch 10 of 30), applied as the app applies
it: `backend/services/damage_classifier.classify_crop`, the detector's box cut from the frame with no padding,
threshold `classifier.conf_threshold` in `ml/models/model_config.json` (0.0).

**Data:** the 270 reviewed validation frames (`data/local/yolo_nz/val_reviewed.txt`, 122 boxes: D00 30,
D10 23, D20 17, D40 52), labelled by one reviewer in the same way as the test frames. The classifier's best
epoch was chosen on crops of these same 122 boxes, so every classifier figure here is a selection figure and
optimistic.

## 1. Primary: class decision on the deployed fusion's detections

- The deployed fusion (`ml/models/model_config.json`: v2b + v3 + S5_v8m_1920, grey border 24 px, weighted box
  fusion, threshold 0.25) detects on the 270 frames with the app's settings, as `test_eval_nz.py` does.
- Detections are paired one-to-one with reviewed boxes, greedily, highest IoU first, IoU >= 0.5, **any class**
  (`ml/local/label_quality.match`), the matching rule of `results/metric_definitions.md`.
- On the same matched detections: **fusion accuracy** = matched detections whose fused class equals the
  reviewed class / matched detections; **classifier accuracy** = matched detections whose classifier class
  equals the reviewed class / matched detections. 95% Wilson intervals. 4 x 4 tables (reviewed x given).
- **Exact McNemar test** (two-sided binomial on the detections where exactly one of the two is right).

Reported number of matched detections is the same for both, since the classifier only relabels.

## 2. Reference: classifier top-1 on the reviewed boxes

Top-1 accuracy on the 122 reviewed boxes cut like the training crops (25% padding,
`ml/build_classifier_dataset.py`). This is what Ultralytics reported during training (0.8197 = 100 / 122 at
the kept epoch). It is not comparable with section 1: it uses the reviewed boxes, not the detector's boxes,
and the training-style padding.

## Decision rule (proposed)

The classifier changes the class of every stored record (`damage_type`), so it should stay enabled only if it
classifies the deployed fusion's own detections better. Proposed: keep it enabled only if its accuracy in
section 1 is higher than the fusion's **and** the exact McNemar p < 0.05. Otherwise disable it
(`"enabled": false`), so that the deployed system is the test-evaluated one, and report it as a validation-only
experiment. Either way no test figure is reported for the classifier.

# Training runs (one row per run)

Val numbers on the near-zone val sets after the final label freeze (`labels_FINAL_20261111_013131.db`),
from `ml/local/eval_val_sets.py` (details and per-class tables in `results/val_sets_comparison.md`).
"val" style = Ultralytics' validation input (with its grey border); "app" style = the crop exactly as the app
passes it. Full = 1,624 frames, 659 boxes; reviewed = the 270 single-reviewer frames, 122 boxes. Test is not
touched (no `test_eval.py` run for any model).

**Fair comparison set: reviewed.** The annotation-site pre-labels came from S5_v8m_1280, and 22% of the site
val boxes are its own predictions kept unchanged, so on full val S5_v8m_1280 is partly marked on its own answers.

| Run | Setup | Starts from | Data | imgsz | Batch | Optimizer | Epochs set / run / best | Training h | mAP@50 full (val / app) | mAP@50-95 full (val) | mAP@50 reviewed (val / app) | mAP@50-95 reviewed (val) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | run A: local only | yolov8m.pt (COCO) | old `yolo/` local train (road band, before the site labels) | 1280 | 4 | SGD 0.01 | 40 / 26 / 16 | 0.3 | 0.049 / 0.049 | 0.016 | 0.127 / 0.122 | 0.051 | superseded |
| Bv1 | run B | RDD2022 teacher | local + RDD2022 replay | 1280 | 4 | SGD 0.001 | 40 / 26 / 16 | 0.9 | not re-evaluated | | | | superseded by Bv2 |
| Bv2 | run B | RDD2022 teacher | local + RDD2022 replay | 1280 | 4 | SGD 0.001 | 40 / 26 / 16 | 1.0 | 0.105 / 0.100 | 0.041 | 0.155 / 0.139 | 0.066 | superseded |
| S5_v8m_1280 | run B, near zone | Bv2 | B list on near-zone crops (+ replay) | 1280 | 4 | AdamW 0.0005 | 40 / 18 / 8 | 0.7 | 0.137 / 0.122 (biased, see above) | 0.070 | 0.167 / 0.125 | 0.066 | pre-label model of the site; has RDD2022 replay (excluded by §9) |
| S5_v8m_1920 | run B, near zone | Bv2 | as S5_v8m_1280 | 1920 | 2 | AdamW 0.0005 | 40 / 10 / 8 | | not evaluated | | | | stopped, unfinished |
| **v1** | **final freeze, local labels only, no replay** | yolov8m.pt (COCO) | `v1_train.txt`: every damage frame of the local train set, D10/D20/D40 frames x3, 1,500 no-damage frames; 4,783 images per epoch | 1024 | 6 | SGD 0.01 | 60 / 33 / 18 (early stop, patience 15) | 2.8 | **0.109 / 0.102** (model.val: 0.116) | 0.039 (model.val: 0.043) | **0.171 / 0.160** (model.val: 0.182) | 0.062 | **deployed 2026-11-11 04:48**, conf 0.24, not test-evaluated |
| placeholder | external, NOT ours | rdd2022_pretrained.pt (7-class YOLOv8n) | RDD2022 | 1280 (app) | | | | | 0.037 / 0.026 | 0.019 | 0.155 / 0.133 | 0.099 | previous app model (rollback target) |

v1 per class, mAP@50 on full val (val style): D00 0.137, D10 0.140, D20 0.057, D40 0.102; on reviewed: D00 0.289,
D10 0.137, D20 0.037, D40 0.220. v1 beats the placeholder on every val set and style, so it is deployed (decision 3).

v1 threshold (`results/threshold_v1.md`, max overall F1 on full val, app style, NMS IoU 0.45, imgsz 1024):
**0.24**, P 0.20 / R 0.18 / F1 0.19 on full val; F1 0.24 on reviewed; F1 0.18 on the site frames.

Plots: `runs/local/v1/` (confusion matrix, PR / F1 / P / R curves on full val, from the end of training) and
`runs/eval/v1_val_reviewed/` (same on the 270 reviewed frames). Examples: `results/v1_examples.md`.

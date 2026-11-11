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
| **v1** | **final freeze, local labels only, no replay** | yolov8m.pt (COCO) | `v1_train.txt`: every damage frame of the local train set, D10/D20/D40 frames x3, 1,500 no-damage frames; 4,783 images per epoch | 1024 | 6 | SGD 0.01 | 60 / 33 / 18 (early stop, patience 15) | 2.8 | **0.109 / 0.102** (model.val: 0.116) | 0.039 (model.val: 0.043) | **0.171 / 0.160** (model.val: 0.182) | 0.062 | **deployed 2026-11-11 04:48** (conf 0.24), redeployed 07:49 at conf 0.32; not test-evaluated |
| placeholder | external, NOT ours | rdd2022_pretrained.pt (7-class YOLOv8n) | RDD2022 | 1280 (app) | | | | | 0.037 / 0.026 | 0.019 | 0.155 / 0.133 | 0.099 | previous app model (rollback target) |

v1 per class, mAP@50 on full val (val style): D00 0.137, D10 0.140, D20 0.057, D40 0.102; on reviewed: D00 0.289,
D10 0.137, D20 0.037, D40 0.220. v1 beats the placeholder on every val set and style, so it is deployed (decision 3).

v1 threshold (`results/threshold_v1.md`; team, 2026-11-11 morning: sweep conf 0.01-0.50 in 0.01 steps,
selection set = the 270 reviewed frames, max overall F1, app style, NMS IoU 0.45, imgsz 1024): **0.32**,
P 0.30 / R 0.25 / F1 0.27 on reviewed; F1 0.17 on full val; F1 0.15 on the site frames. Redeployed 07:49
(it replaced 0.24, chosen on full val over 0.05-0.90). The threshold is for deployment only: every mAP here is
at Ultralytics' default validation conf (0.001).

No hyperparameter tuning (`model.tune`): not enough GPU time, and the selection set is too small (team).

## Queued 2026-11-11 08:00: v2b, then v2 (hard stop for both Fri 13 Nov 22:00)

The final model is chosen on the 270 reviewed frames (main column), full val as the second column
(`ml/local/eval_val_sets.py`). Test stays untouched until the team approves the single run.

| Run | Setup | Starts from | Data | imgsz | Batch | Optimizer | Epochs / patience | Other |
|---|---|---|---|---|---|---|---|---|
| v2 | v1 recipe | yolov8m.pt (COCO) | v1's own training list (frozen copy `runs/local/v1/data/v1_train.txt`; there was no label freeze 2) | 1024 | 6 | SGD 0.01 | 60 / 15 | save_period 1 |
| v2b | external RDD2022 start, local data only | YOLOv8s RDD2022 checkpoint (below) | v1's own training list (frozen copy `runs/local/v1/data/v1_train.txt`) | 1024 | 12 (largest that fits: 6.42 GiB; 16 needs 8.84 GiB, `results/bench_batch.md`) | SGD 0.001 | 40 / 100 | close_mosaic 10, save_period 1 |

**v2b starting checkpoint.** `yolov8s_seed0_best.pt` from
https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark (file `yolo-rdd2022-benchmark/yolov8s_seed0_best.pt`,
revision 6bec4bbcf77738e69aa96419bf324c2b9357519c, sha256 565aae6915e34e4f7f4c44dac0bdcf9fff21b83c4adc74cc97ca09cc31882ce8),
licence **CC BY 4.0** (attribution required). Saved in `ml/models/pretrained/` (gitignored). Trained by its author with
Ultralytics 8.4.24 (2026-03-20) on RDD2022 at 640 px, 100 epochs, batch 64, seed 0; reported RDD2022 global val
mAP@50 0.5995 (3-seed mean) on the author's split. Its pickles import only torch, ultralytics, collections.OrderedDict
and set (checked with `pickletools` before loading). Classes (index order): longitudinal_crack, transverse_crack,
alligator_crack, pothole: the model card maps them to D00, D10, D20, D40, the same ids as our `v1.yaml`; on
fine-tuning the names become ours. Its RDD2022 training images likely overlap our six-country foreign val/test
slices, so a foreign-test score of v2b is not held out (local val/test unaffected; `results/pretrained_sources.md`).
Cite the dataset as the model card asks:

> Arya, D., Maeda, H., Ghosh, S. K., Toshniwal, D., Mraz, A., Kashiyama, T., & Sekimoto, Y. (2022). RDD2022: A
> multi-national image dataset for automatic Road Damage Detection. arXiv:2209.08538.

Plots: `runs/local/v1/` (confusion matrix, PR / F1 / P / R curves on full val, from the end of training) and
`runs/eval/v1_val_reviewed/` (same on the 270 reviewed frames). Examples: `results/v1_examples.md`.

# Training plan from 2026-11-10 (replaces Steps 4-6)

All training done by Tuesday 2026-11-10 21:30 (hard stop); final choice, calibration, test and
deployment by 23:00. Runs automatically: `tools/pipeline_v2.py` (status: `results/pipeline_status.md`).

## Settings for every run (for Chapter III)

| Setting | Value |
|---|---|
| Model | YOLOv8m |
| Input size | 1280 |
| Batch | 4 (fixed; AutoBatch is unreliable on this PC) |
| Optimizer | SGD, momentum 0.937, weight decay 0.0005; lr0 0.01 from COCO weights (A), 0.001 from the teacher's weights (B). Set explicitly: Ultralytics' default `optimizer=auto` ignores lr0 |
| Epochs / early stopping | up to 40 / patience 10 |
| Augmentation | horizontal flip 0.5, vertical flip 0, mixup 0, rotation up to 5 degrees, scale 0.5, translate 0.1, mosaic 1.0 (switched off for the last 10 epochs), HSV hue 0.015 / saturation 0.7 / value 0.4 (Ultralytics defaults), no shear, perspective or copy-paste |
| Other | AMP, seed 42, deterministic, data-loader workers 2 (RAM), validation on the reviewed local val set (270 frames) every epoch |
| Labels | human-reviewed only, all by one reviewer (Gian Paolo Ybut): val and test (batches 1 and 2; self-check of test frames marked "no damage"), train (batch "train", 376 frames, then "AL", about 150) |

The teacher (2026-11-09) used Ultralytics' augmentation defaults, which differ from the above only in
rotation (0), and ran at 960, batch 6.

## Runs (`python ml/local/runs_v2.py --list`)

| Run | Starts from | Training data | lr0 |
|---|---|---|---|
| A | COCO | local train | 0.01 |
| B v1 | teacher | local train, D10/D20 frames x3, + 600 random six-country RDD2022 train images (fixed sample) | 0.001 |
| B v2 | teacher | as B v1 after the AL batch | 0.001 |
| B v2 no replay | teacher | as B v2 without the 600 RDD2022 images | 0.001 |
| B v2 freeze 10 | teacher | as B v2, first 10 layers frozen (only if it can start by 20:00) | 0.001 |

C (local + India) is skipped.

## Time estimates (measured: about 10 images/s at 1280, batch 4; 11.6 with 10 layers frozen)

Assumes 376 reviewed train frames, about 100 of them with D10/D20 (x3 adds about 200), and 150 AL
frames (about 50 more with D10/D20). Upper bounds: all 40 epochs; patience 10 can end a run sooner.

| Run | Images per epoch | Minutes per epoch | Hours (40 epochs) |
|---|---|---|---|
| B v1 | ~1,180 | ~2.4 | ~1.6 |
| A | ~380 | ~1.1 | ~0.7 |
| B v2 | ~1,430 | ~2.8 | ~1.9 |
| B v2 no replay | ~830 | ~1.8 | ~1.2 |
| B v2 freeze 10 | ~1,430 | ~2.5 | ~1.7 |

Plus about 2 minutes per Chapter V table update and about 4 minutes for the AL selection.

## Latest start times (working back from 20:00 and 21:30)

| To still fit | Train batch reviewed (B v1 starts) by |
|---|---|
| Everything, including freeze 10 by 20:00 | ~14:10 (and the AL review done about an hour after B v1 ends) |
| B v2 and no replay before the 21:30 hard stop | ~16:00 |
| B v2 alone before 21:30 | ~17:00 |

If the train batch is reviewed by late morning, every run finishes in the afternoon.

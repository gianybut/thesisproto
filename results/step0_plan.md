# Step 0: schedule and proposed changes

Measured on 2026-11-09 (Monday). Timings and estimates are in [step0_benchmark.md](step0_benchmark.md),
written by `python ml/benchmark_step0.py`.

## Environment

| Item | Value |
|---|---|
| PyTorch | 2.11.0+cu128 (was 2.11.0+cpu; CUDA build installed 2026-11-09) |
| CUDA / cuDNN | 12.8 / 9.19 |
| Ultralytics | 8.4.48 |
| Python | 3.14.3 (project `.venv`) |
| GPU | NVIDIA GeForce RTX 4060, 8 GB, driver 610.88 |

## AutoBatch does not work on this PC

`batch=-1` picked batch 3 at 640 and batch 1 at 960, 1024 and 1280. Its memory profile spills past
8 GB into shared system memory under the Windows driver (it measured 16.8 GB for batch 16 at 640),
so it underestimates what fits. Batch 1 also breaks BatchNorm statistics. Fixed batches ran 1.1 to
1.5 times faster with peak memory well inside the card:

| imgsz | proposed fixed batch | peak torch reserved | notes |
|---|---|---|---|
| 640 | 16 | 6.1 GiB | |
| 960 | 6 | (8 measured 6.9 GiB, card 7.4 of 8.2 GB with the desktop) | 8 is too tight for a 2 h run |
| 1024 | 6 | 5.7 GiB | |
| 1280 | 4 | 6.2 GiB | only if chosen |

## GPU timeline (upper bounds: every epoch run, no early stopping)

| When | Run | Est. hours |
|---|---|---|
| Mon evening to Tue noon | GPU idle (Steps 1-3 are CPU work; Step 4 needs the reviewed val set) | |
| Tue 12:00 to ~14:20 | Step 4 safety model, local 600 + India 2,256, 960, 40 ep | 2.3 |
| Tue ~14:20 to ~19:15 | Step 5: local only + 6 singles + 3 pairs, 640, 20 ep | 4.9 |
| Tue ~19:30 to Wed 06:00 | Step 6.1 window | 10.5 available |
| | 6.1 at 1024, largest single (Japan, 7,330 images) | 6.8 |
| | 6.1 at 1024, largest pair (Japan + United States, 10,693 images) | 9.7 |
| | 6.1 at 1280, singles except Japan | 4.0 to 7.7 |
| | 6.1 at 1280, Japan or any pair with Japan or United States | 10.7 to 15.4 (does not fit) |
| Wed 06:00 to ~07:30 | Step 6.2 local fine-tune at 1024, 30 ep | 0.7 to 1.5 |

The plan fits at 1024 with no cuts, but if a pair with Japan wins Step 5, the margin is under an hour.

## Data facts that change the plan

- **India has 2,256 filtered train images, not 3,000.** India has 3,223 annotated images with a
  D00/D10/D20/D40 box, and 70% of that is 2,256. Step 4 can use all 2,256.
- **`N_foreign` = 750.** Czech is the smallest pool (750 train images), so each single-country
  run uses 750 foreign images and each pair 375 + 375.
- RDD2022 is already extracted in `RDD2022_raw/RDD2022/` (full release, per-country folders; only
  `train/` is annotated). Step 3 can read it instead of downloading the per-country archives.

## Proposed cuts and rules (need "continue")

1. Use the fixed batches above instead of `batch=-1`, and log them.
2. Final model at **1024**, not 1280. 1280 fits only for a single non-Japan country and leaves no
   slack before Step 6.2.
3. If Step 5's best mix is estimated above 9 h at 1024, or Step 4 starts after 13:00 Tuesday, run
   6.1 for **40 epochs** instead of 50 (saves about 20%).
4. If Step 4 starts after 15:00 Tuesday, skip the Step 5 pairs (saves about 1.5 h), as the task's
   fallback allows.

## Why the estimates are probably high

- GPU utilisation was only 16-46%: the data loader (JPEG decoding, mosaic) limits speed, not the
  GPU. The sample includes Norway's 3,650 x 2,044 images; local road-band frames and Japan/US
  images (600-640 px) decode faster.
- Validation time was measured on an untrained model, which outputs many boxes and makes NMS
  slow. Trained models validate faster.
- Loader start-up is counted every epoch, but Ultralytics keeps its workers between epochs.
- The local counts (600 train, 120 val) are the task's caps. Real counts come from Steps 1-2.

## Approved by the team (2026-11-09 evening)

- Fixed batches: 16 at 640, 6 at 960 and 1024. Final model at 1024. The fallbacks above apply.
- Step 4 uses all 2,256 India train images. `N_foreign` = 750.
- Before Step 4: a pre-resized copy of every RDD2022 image used for training (longest side at
  most 1280, labels unchanged); train from that copy.
- `workers=6`; drop to 4 if system RAM exceeds 85%.
- Build `tools/watch_training.py` before Step 4.

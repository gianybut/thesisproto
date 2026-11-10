# Step 0 benchmark (YOLOv8m, RTX 4060 8 GB)

Generated 2026-11-09 17:40. Sample: 300 train / 60 val RDD2022 images (6 countries, no China_Drone), 1 epoch, batch=-1, amp, cache=False, workers=4, seed 42.

| imgsz | batch | chosen by | epoch (s) | train part (s) | val part (s) | steady train img/s | peak torch reserved (GiB) | peak card used (MiB, incl. desktop) | peak temp (°C) | mean util | used for estimate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 640 | 16 | fixed | 36.6 | 15.8 | 20.8 | 37.57 | 6.12 | 6917 | 56 | 16% | yes |
| 640 | 3 | AutoBatch (batch=-1) | 19.9 | 12.1 | 7.8 | 29.05 | 8.74 | 7844 | 56 | 31% | no, too close to 8 GB |
| 960 | 8 | fixed | 39.5 | 24.8 | 14.7 | 16.77 | 6.91 | 7414 | 59 | 33% | yes |
| 960 | 1 | AutoBatch (batch=-1) | 36.8 | 28.4 | 8.4 | 11.54 | 14.56 | 7936 | 57 | 38% | no, too close to 8 GB |
| 1024 | 6 | fixed | 36.8 | 21.7 | 15.1 | 16.02 | 5.7 | 6176 | 60 | 36% | yes |
| 1024 | 1 | AutoBatch (batch=-1) | 37.5 | 29.2 | 8.2 | 10.89 | 14.61 | 7886 | 57 | 42% | no, too close to 8 GB |
| 1280 (extra) | 4 | fixed | 48.9 | 32.8 | 16.1 | 10.0 | 6.21 | 6699 | 62 | 46% | yes |
| 1280 (extra) | 1 | AutoBatch (batch=-1) | 46.9 | 36.5 | 10.5 | 8.97 | 14.63 | 7811 | 60 | 56% | no, too close to 8 GB |

## Estimated wall-clock of the planned runs (all epochs; early stopping can only shorten)

Assumed: local train 600 (pseudo-labelled cap), local val 120; foreign train pools = 70% of the annotated images with a target class: Japan 5530, India 2256, Czech 750, Norway 2039, United_States 3363, China_MotorBike 1353. N_foreign = 750.

| Step | Run | train images | imgsz | epochs | est. hours |
|---|---|---|---|---|---|
| 4 | Safety: local + India 2256 | 2856 | 960 | 40 | 2.32 |
| 5 | Local only | 600 | 640 | 20 | 0.39 |
| 5 | Local + Japan 750 | 1350 | 640 | 20 | 0.50 |
| 5 | Local + India 750 | 1350 | 640 | 20 | 0.50 |
| 5 | Local + Czech 750 | 1350 | 640 | 20 | 0.50 |
| 5 | Local + Norway 750 | 1350 | 640 | 20 | 0.50 |
| 5 | Local + United_States 750 | 1350 | 640 | 20 | 0.50 |
| 5 | Local + China_MotorBike 750 | 1350 | 640 | 20 | 0.50 |
| 5 | Pair 1 of top 3 (375 + 375) | 1350 | 640 | 20 | 0.50 |
| 5 | Pair 2 of top 3 (375 + 375) | 1350 | 640 | 20 | 0.50 |
| 5 | Pair 3 of top 3 (375 + 375) | 1350 | 640 | 20 | 0.50 |
| | **Steps 4 + 5 total** | | | | **7.2** |

### Step 6 (mix decided in Step 5; local ×3 = 1800 in 6.1)

| imgsz | mix | 6.1 train images | 6.1 hours (50 ep) | 6.2 train images | 6.2 hours (30 ep) |
|---|---|---|---|---|---|
| 960 | Czech | 2550 | 2.6 | 750 | 0.7 |
| 960 | China_MotorBike | 3153 | 3.1 | 870 | 0.8 |
| 960 | Norway | 3839 | 3.7 | 1007 | 0.8 |
| 960 | India | 4056 | 3.9 | 1051 | 0.8 |
| 960 | United_States | 5163 | 4.8 | 1272 | 1.0 |
| 960 | Japan | 7330 | 6.6 | 1706 | 1.2 |
| 960 | Japan + United_States | 10693 | 9.4 | 2378 | 1.5 |
| 1024 | Czech | 2550 | 2.7 | 750 | 0.7 |
| 1024 | China_MotorBike | 3153 | 3.2 | 870 | 0.7 |
| 1024 | Norway | 3839 | 3.8 | 1007 | 0.8 |
| 1024 | India | 4056 | 4.0 | 1051 | 0.8 |
| 1024 | United_States | 5163 | 5.0 | 1272 | 1.0 |
| 1024 | Japan | 7330 | 6.8 | 1706 | 1.2 |
| 1024 | Japan + United_States | 10693 | 9.7 | 2378 | 1.5 |
| 1280 | Czech | 2550 | 4.0 | 750 | 0.9 |
| 1280 | China_MotorBike | 3153 | 4.9 | 870 | 1.0 |
| 1280 | Norway | 3839 | 5.8 | 1007 | 1.2 |
| 1280 | India | 4056 | 6.1 | 1051 | 1.2 |
| 1280 | United_States | 5163 | 7.7 | 1272 | 1.4 |
| 1280 | Japan | 7330 | 10.7 | 1706 | 1.7 |
| 1280 | Japan + United_States | 10693 | 15.4 | 2378 | 2.3 |

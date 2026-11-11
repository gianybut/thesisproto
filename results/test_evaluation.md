# Test evaluation of the deployed model (v2b + v3 + S5_v8m_1920), done once

Model as deployed (`ml/models/model_config.json`): `ml/models/oculubak_v2b.pt` at 1024 px; `ml/models/oculubak_v3.pt` at 1280 px; `ml/models/oculubak_S5_v8m_1920.pt` at 1280 px, fused (weighted box fusion); grey border 24 px; confidence threshold 0.25, calibrated on the 270 reviewed val frames (results/threshold_calibration.md). Chosen on those frames (results/final_selection.md). Metrics as fixed in results/metric_definitions.md. Evaluated 2026-11-11 17:27.

Test: 270 near-zone frames (207 with no damage), 99 reviewed boxes. Validation: 270 reviewed frames (207 with no damage), 122 boxes. Class counts are small (see the box counts), so per-class figures are uncertain.

## Chapter V tables (ready to paste)

**Table 5.A. Detection accuracy of the deployed model (AP at IoU 0.5; conf 0.001, NMS IoU 0.7).**

| Metric | Validation (270 reviewed frames) | Test (270 frames) |
|---|---|---|
| mAP@50 | 0.275 | 0.173 |
| mAP@50-95 | 0.095 | 0.057 |
| AP@50, Longitudinal crack (D00) | 0.519 (30 boxes) | 0.381 (36 boxes) |
| AP@50, Transverse crack (D10) | 0.179 (23 boxes) | 0.124 (8 boxes) |
| AP@50, Alligator crack (D20) | 0.027 (17 boxes) | 0.152 (34 boxes) |
| AP@50, Pothole (D40) | 0.376 (52 boxes) | 0.035 (21 boxes) |

**Table 5.B. Precision, recall and F1 at the deployed threshold (0.25), all classes.**

| Set | Boxes | Correct | False alarms | Missed | Precision (95% CI) | Recall (95% CI) | F1 |
|---|---|---|---|---|---|---|---|
| Validation | 122 | 37 | 64 | 85 | 0.37 (27.9% to 46.4%) | 0.30 (22.9% to 39.0%) | 0.33 |
| Test | 99 | 24 | 54 | 75 | 0.31 (21.6% to 41.7%) | 0.24 (16.9% to 33.5%) | 0.27 |

**Table 5.C. Test: precision, recall and F1 per class at 0.25.**

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 36 | 17 | 22 | 19 | 0.44 | 0.47 | 0.45 |
| D10 | 8 | 3 | 18 | 5 | 0.14 | 0.38 | 0.21 |
| D20 | 34 | 3 | 6 | 31 | 0.33 | 0.09 | 0.14 |
| D40 | 21 | 1 | 8 | 20 | 0.11 | 0.05 | 0.07 |
| All classes | 99 | 24 | 54 | 75 | 0.31 | 0.24 | 0.27 |

**Table 5.D. Classification accuracy among detections (threshold 0.25; detections matched to a reviewed box at IoU >= 0.5, any class).**

| Set | Matched detections | Correct class | Accuracy (95% CI) |
|---|---|---|---|
| Validation | 40 | 37 | 92.5% (80.1% to 97.4%) |
| Test | 25 | 24 | 96.0% (80.5% to 99.3%) |

Test: matched pairs by reviewed class (rows) and detected class (columns):

| Reviewed \ Detected | D00 | D10 | D20 | D40 |
|---|---|---|---|---|
| D00 | 17 | 0 | 0 | 0 |
| D10 | 0 | 3 | 0 | 1 |
| D20 | 0 | 0 | 3 | 0 |
| D40 | 0 | 0 | 0 | 1 |

**Table 5.E. High-confidence operating point (lowest threshold with validation precision >= 0.80).**

| Set | Threshold | Correct | False alarms | Missed | Precision | Recall |
|---|---|---|---|---|---|---|
| Validation | 0.62 | 1 | 0 | 121 | 1.00 | 0.01 |
| Test | 0.62 | 4 | 0 | 95 | 1.00 | 0.04 |

Note: on validation this point rests on 1 detection(s) out of 122 reviewed boxes, so it is not a usable operating point; it is reported as defined (results/metric_definitions.md, section 4).

## Each model alone and the fusion (mAP, for information)

| Set | Model | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |
|---|---|---|---|---|---|---|---|---|---|
| Validation | **v2b + v3 + S5_v8m_1920 (fused, deployed)** | 0.385 | 0.242 | 0.275 | 0.095 | 0.519 | 0.179 | 0.027 | 0.376 |
| Validation | v2b alone | 0.260 | 0.204 | 0.163 | 0.062 | 0.271 | 0.143 | 0.020 | 0.216 |
| Validation | v3 alone | 0.367 | 0.256 | 0.253 | 0.086 | 0.504 | 0.177 | 0.016 | 0.315 |
| Validation | S5_v8m_1920 alone | 0.376 | 0.188 | 0.200 | 0.080 | 0.361 | 0.183 | 0.003 | 0.251 |
| Test | **v2b + v3 + S5_v8m_1920 (fused, deployed)** | 0.227 | 0.311 | 0.173 | 0.057 | 0.381 | 0.124 | 0.152 | 0.035 |
| Test | v2b alone | 0.157 | 0.264 | 0.146 | 0.056 | 0.334 | 0.077 | 0.130 | 0.041 |
| Test | v3 alone | 0.162 | 0.281 | 0.160 | 0.055 | 0.337 | 0.171 | 0.100 | 0.032 |
| Test | S5_v8m_1920 alone | 0.423 | 0.132 | 0.141 | 0.051 | 0.350 | 0.130 | 0.070 | 0.016 |

## Validation per class at 0.25 (for comparison with Table 5.C)

| Class | Boxes | Correct | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| D00 | 30 | 15 | 22 | 15 | 0.41 | 0.50 | 0.45 |
| D10 | 23 | 5 | 20 | 18 | 0.20 | 0.22 | 0.21 |
| D20 | 17 | 0 | 8 | 17 | 0.00 | 0.00 | 0.00 |
| D40 | 52 | 17 | 14 | 35 | 0.55 | 0.33 | 0.41 |
| All classes | 122 | 37 | 64 | 85 | 0.37 | 0.30 | 0.33 |

## Foreign test in full (RDD2022, six countries), each member alone

The fusion is not scored on foreign images; these are the single models at their own sizes.

### v2b (1024 px) - NOT HELD OUT

**Not held out:** this model starts from an external checkpoint trained on its own split of the public RDD2022 images, which very likely includes images of this foreign test split (results/pretrained_sources.md).

Weights `ml/models/oculubak_v2b.pt`, imgsz 1024. Test = 15% of each country (seed 42), never used for training. Standard Ultralytics validation (conf 0.001, NMS IoU 0.7).

| Test set | Images | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |
|---|---|---|---|---|---|---|---|---|---|
| **all six countries** | 3277 | 0.323 | 0.269 | 0.200 | 0.068 | 0.290 | 0.179 | 0.190 | 0.143 |
| Japan | 1185 | 0.229 | 0.242 | 0.145 | 0.046 | 0.152 | 0.124 | 0.181 | 0.123 |
| India | 483 | 0.272 | 0.195 | 0.171 | 0.058 | 0.207 | 0.009 | 0.203 | 0.267 |
| Czech | 161 | 0.220 | 0.312 | 0.190 | 0.057 | 0.291 | 0.104 | 0.163 | 0.202 |
| Norway | 437 | 0.353 | 0.160 | 0.131 | 0.039 | 0.232 | 0.085 | 0.159 | 0.048 |
| United_States | 721 | 0.381 | 0.454 | 0.361 | 0.145 | 0.534 | 0.355 | 0.457 | 0.097 |
| China_MotorBike | 290 | 0.369 | 0.140 | 0.131 | 0.040 | 0.110 | 0.085 | 0.030 | 0.300 |


### v3 (1280 px)

Weights `ml/models/oculubak_v3.pt`, imgsz 1280. Test = 15% of each country (seed 42), never used for training. Standard Ultralytics validation (conf 0.001, NMS IoU 0.7).

| Test set | Images | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |
|---|---|---|---|---|---|---|---|---|---|
| **all six countries** | 3277 | 0.337 | 0.305 | 0.239 | 0.084 | 0.330 | 0.242 | 0.230 | 0.154 |
| Japan | 1185 | 0.277 | 0.263 | 0.177 | 0.061 | 0.139 | 0.162 | 0.235 | 0.173 |
| India | 483 | 0.226 | 0.201 | 0.155 | 0.052 | 0.146 | 0.007 | 0.285 | 0.182 |
| Czech | 161 | 0.201 | 0.258 | 0.151 | 0.048 | 0.287 | 0.104 | 0.085 | 0.128 |
| Norway | 437 | 0.296 | 0.220 | 0.182 | 0.065 | 0.316 | 0.163 | 0.088 | 0.161 |
| United_States | 721 | 0.371 | 0.418 | 0.360 | 0.151 | 0.535 | 0.424 | 0.391 | 0.091 |
| China_MotorBike | 290 | 0.315 | 0.354 | 0.284 | 0.087 | 0.239 | 0.283 | 0.278 | 0.337 |


### S5_v8m_1920 (1280 px)

Weights `ml/models/oculubak_S5_v8m_1920.pt`, imgsz 1280. Test = 15% of each country (seed 42), never used for training. Standard Ultralytics validation (conf 0.001, NMS IoU 0.7).

| Test set | Images | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |
|---|---|---|---|---|---|---|---|---|---|
| **all six countries** | 3277 | 0.411 | 0.369 | 0.318 | 0.127 | 0.406 | 0.284 | 0.328 | 0.254 |
| Japan | 1185 | 0.394 | 0.352 | 0.312 | 0.122 | 0.314 | 0.289 | 0.349 | 0.295 |
| India | 483 | 0.249 | 0.231 | 0.180 | 0.066 | 0.158 | 0.003 | 0.330 | 0.229 |
| Czech | 161 | 0.326 | 0.267 | 0.247 | 0.079 | 0.397 | 0.258 | 0.117 | 0.216 |
| Norway | 437 | 0.382 | 0.237 | 0.216 | 0.084 | 0.363 | 0.199 | 0.101 | 0.200 |
| United_States | 721 | 0.446 | 0.439 | 0.429 | 0.205 | 0.620 | 0.431 | 0.357 | 0.306 |
| China_MotorBike | 290 | 0.422 | 0.363 | 0.340 | 0.117 | 0.296 | 0.338 | 0.339 | 0.388 |



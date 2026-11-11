# Final model choice: single models and fusions on near-zone val

2026-11-11 12:32. Each model at its training size with a 24 px grey border above and below the crop (as the app now adds it), conf 0.001, NMS IoU 0.7; fusion = weighted box fusion (`backend/services/box_fusion.py`). **Selection set: the 270 reviewed frames** (122 boxes); full val (1,624 frames, 659 boxes) is the second column. Test is not touched.

Candidates: **v1** = `runs/local/v1/weights/best.pt` at 1024; **v2b** = `runs/local/v2b/weights/best.pt` at 1024; **v3** = `runs/local/v3/weights/best.pt` at 1280; **S5_1920** = `runs/v3/S5_v8m_1920/weights/best.pt` at 1280.

| Model(s) | mAP@50 reviewed | mAP@50-95 reviewed | D00 | D10 | D20 | D40 | mAP@50 full | mAP@50-95 full |
|---|---|---|---|---|---|---|---|---|
| v2b + v3 + S5_1920 | 0.275 | 0.095 | 0.519 | 0.179 | 0.027 | 0.376 | 0.161 | 0.062 |
| v1 + v3 + S5_1920 | 0.275 | 0.095 | 0.535 | 0.182 | 0.027 | 0.355 | 0.160 | 0.063 |
| v1 + v2b + S5_1920 | 0.273 | 0.099 | 0.572 | 0.197 | 0.021 | 0.302 | 0.159 | 0.061 |
| v2b + S5_1920 | 0.262 | 0.087 | 0.548 | 0.200 | 0.016 | 0.282 | 0.153 | 0.055 |
| v3 + S5_1920 | 0.259 | 0.089 | 0.471 | 0.155 | 0.022 | 0.390 | 0.152 | 0.058 |
| v3 | 0.253 | 0.086 | 0.504 | 0.177 | 0.016 | 0.315 | 0.139 | 0.058 |
| v1 + S5_1920 | 0.250 | 0.094 | 0.493 | 0.193 | 0.026 | 0.287 | 0.149 | 0.057 |
| v1 + v2b + v3 | 0.240 | 0.089 | 0.460 | 0.160 | 0.028 | 0.310 | 0.151 | 0.060 |
| v1 + v3 | 0.237 | 0.082 | 0.469 | 0.124 | 0.029 | 0.325 | 0.139 | 0.055 |
| v2b + v3 | 0.237 | 0.082 | 0.477 | 0.135 | 0.028 | 0.306 | 0.146 | 0.056 |
| v1 + v2b | 0.201 | 0.075 | 0.396 | 0.152 | 0.022 | 0.235 | 0.133 | 0.050 |
| S5_1920 | 0.200 | 0.080 | 0.361 | 0.183 | 0.003 | 0.251 | 0.119 | 0.047 |
| v1 | 0.171 | 0.063 | 0.301 | 0.132 | 0.037 | 0.215 | 0.111 | 0.040 |
| v2b | 0.163 | 0.062 | 0.271 | 0.143 | 0.020 | 0.216 | 0.106 | 0.040 |

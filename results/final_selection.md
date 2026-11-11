# Final model choice: single models and fusions on near-zone val

2026-11-11 09:46. Each model at its training size with a 24 px grey border above and below the crop (as the app now adds it), conf 0.001, NMS IoU 0.7; fusion = weighted box fusion (`backend/services/box_fusion.py`). **Selection set: the 270 reviewed frames** (122 boxes); full val (1,624 frames, 659 boxes) is the second column. Test is not touched.

Candidates: **v1** = `runs/local/v1/weights/best.pt` at 1024; **v2b** = `runs/local/v2b/weights/best.pt` at 1024; **S5_1920** = `runs/v3/S5_v8m_1920/weights/best.pt` at 1280.

| Model(s) | mAP@50 reviewed | mAP@50-95 reviewed | D00 | D10 | D20 | D40 | mAP@50 full | mAP@50-95 full |
|---|---|---|---|---|---|---|---|---|
| v1 + v2b + S5_1920 | 0.273 | 0.099 | 0.572 | 0.197 | 0.021 | 0.302 | 0.159 | 0.061 |
| v2b + S5_1920 | 0.262 | 0.087 | 0.548 | 0.200 | 0.016 | 0.282 | 0.153 | 0.055 |
| v1 + S5_1920 | 0.250 | 0.094 | 0.493 | 0.193 | 0.026 | 0.287 | 0.149 | 0.057 |
| v1 + v2b | 0.201 | 0.075 | 0.396 | 0.152 | 0.022 | 0.235 | 0.133 | 0.050 |
| S5_1920 | 0.200 | 0.080 | 0.361 | 0.183 | 0.003 | 0.251 | 0.119 | 0.047 |
| v1 | 0.171 | 0.063 | 0.301 | 0.132 | 0.037 | 0.215 | 0.111 | 0.040 |
| v2b | 0.163 | 0.062 | 0.271 | 0.143 | 0.020 | 0.216 | 0.106 | 0.040 |

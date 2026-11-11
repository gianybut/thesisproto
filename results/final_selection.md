# Final model choice: single models and fusions on near-zone val

2026-11-11 09:19. Each model at its training size with a 24 px grey border above and below the crop (as the app now adds it), conf 0.001, NMS IoU 0.7; fusion = weighted box fusion (`backend/services/box_fusion.py`). **Selection set: the 270 reviewed frames** (122 boxes); full val (1,624 frames, 659 boxes) is the second column. Test is not touched.

Candidates: **v1** = `runs/local/v1/weights/best.pt` at 1024; **S5_1280** = `runs/v3/S5_v8m_1280/weights/best.pt` at 1280; **S5_1920** = `runs/v3/S5_v8m_1920/weights/best.pt` at 1280.

| Model(s) | mAP@50 reviewed | mAP@50-95 reviewed | D00 | D10 | D20 | D40 | mAP@50 full | mAP@50-95 full |
|---|---|---|---|---|---|---|---|---|
| v1 + S5_1920 | 0.250 | 0.094 | 0.493 | 0.193 | 0.026 | 0.287 | 0.149 | 0.057 |
| v1 + S5_1280 + S5_1920 | 0.232 | 0.086 | 0.452 | 0.190 | 0.025 | 0.260 | 0.163 | 0.069 |
| S5_1280 + S5_1920 | 0.212 | 0.080 | 0.406 | 0.207 | 0.012 | 0.223 | 0.158 | 0.069 |
| v1 + S5_1280 | 0.200 | 0.071 | 0.416 | 0.148 | 0.027 | 0.212 | 0.146 | 0.062 |
| S5_1920 | 0.200 | 0.080 | 0.361 | 0.183 | 0.003 | 0.251 | 0.119 | 0.047 |
| v1 | 0.171 | 0.063 | 0.301 | 0.132 | 0.037 | 0.215 | 0.111 | 0.040 |
| S5_1280 | 0.169 | 0.066 | 0.345 | 0.159 | 0.011 | 0.163 | 0.137 | 0.071 |

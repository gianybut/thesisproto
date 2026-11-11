# Inference options on near-zone val (infer_sweep.py)

conf 0.001, NMS IoU 0.7; border = grey rows above and below the 1920x432 crop. Test is not touched.

## v1 (`runs/local/v1/weights/best.pt`), reviewed set, 270 frames (2026-11-11 08:59, device cpu)

| imgsz | Border (px) | TTA | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 | s/frame |
|---|---|---|---|---|---|---|---|---|---|
| 1024 | 0 | no | 0.160 | 0.062 | 0.277 | 0.093 | 0.043 | 0.227 | 0.16 |
| 1024 | 24 | no | 0.171 | 0.063 | 0.301 | 0.132 | 0.037 | 0.215 | 0.17 |
| 1280 | 0 | no | 0.144 | 0.046 | 0.202 | 0.118 | 0.030 | 0.226 | 0.25 |
| 1280 | 24 | no | 0.158 | 0.057 | 0.252 | 0.098 | 0.038 | 0.242 | 0.28 |
| 1536 | 0 | no | 0.143 | 0.048 | 0.233 | 0.041 | 0.087 | 0.212 | 0.34 |
| 1536 | 24 | no | 0.144 | 0.050 | 0.200 | 0.056 | 0.081 | 0.238 | 0.39 |


# Candidate models on the new near-zone val sets (step 6, final freeze)

Near-zone crops (1920x432) of the val recordings. Each model at its own training size (the placeholder at the app's 1280), conf 0.001, NMS IoU 0.7, Ultralytics' matching and AP (`ml/local/eval_val_sets.py`). The placeholder is mapped to the four codes as the app maps it and is NOT the team's model. Style **val** = with the grey border of Ultralytics' rect validation (the conventional figures, close to model.val()); **app** = the crop as the app passes it to the model (no border). Test is not touched.

**Caution:** the annotation-site pre-labels came from S5_v8m_1280. 119 of the 537 site val boxes (22%) are its own predictions kept unchanged (IoU >= 0.95, same class, conf >= 0.15; v1, A, B v2: 0-1%), so on the "new" and "full" sets S5_v8m_1280 is partly marked on its own answers. Only the 270 single-reviewer frames compare it fairly.

## Full val (selection set): 1624 frames, 659 boxes (D00 214, D10 150, D20 51, D40 244)

| Model | Style | imgsz | P | R | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|---|---|---|---|
| v1 (local labels only, near zone, 1024) | val | 1024 | 0.194 | 0.168 | 0.109 | 0.039 | 0.137 | 0.140 | 0.057 | 0.102 |
| v1 (local labels only, near zone, 1024) | app | 1024 | 0.198 | 0.164 | 0.102 | 0.037 | 0.139 | 0.099 | 0.065 | 0.103 |
| run A (local only, old data) | val | 1280 | 0.102 | 0.107 | 0.049 | 0.016 | 0.101 | 0.049 | 0.005 | 0.042 |
| run A (local only, old data) | app | 1280 | 0.103 | 0.104 | 0.049 | 0.018 | 0.095 | 0.051 | 0.005 | 0.043 |
| run B v2 (teacher + local + replay) | val | 1280 | 0.173 | 0.211 | 0.105 | 0.041 | 0.097 | 0.174 | 0.060 | 0.088 |
| run B v2 (teacher + local + replay) | app | 1280 | 0.202 | 0.189 | 0.100 | 0.045 | 0.083 | 0.180 | 0.048 | 0.091 |
| S5_v8m_1280 (B v2 + near zone) | val | 1280 | 0.230 | 0.233 | 0.137 | 0.070 | 0.160 | 0.237 | 0.057 | 0.093 |
| S5_v8m_1280 (B v2 + near zone) | app | 1280 | 0.246 | 0.240 | 0.122 | 0.080 | 0.126 | 0.252 | 0.026 | 0.083 |
| placeholder rdd2022_pretrained.pt (NOT ours) | val | 1280 | 0.177 | 0.060 | 0.037 | 0.019 | 0.031 | 0.000 | 0.097 | 0.020 |
| placeholder rdd2022_pretrained.pt (NOT ours) | app | 1280 | 0.098 | 0.048 | 0.026 | 0.015 | 0.038 | 0.000 | 0.053 | 0.015 |

## The 270 single-reviewer frames: 270 frames, 122 boxes (D00 30, D10 23, D20 17, D40 52)

| Model | Style | imgsz | P | R | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|---|---|---|---|
| v1 (local labels only, near zone, 1024) | val | 1024 | 0.235 | 0.265 | 0.171 | 0.062 | 0.289 | 0.137 | 0.037 | 0.220 |
| v1 (local labels only, near zone, 1024) | app | 1024 | 0.270 | 0.226 | 0.160 | 0.062 | 0.277 | 0.093 | 0.043 | 0.227 |
| run A (local only, old data) | val | 1280 | 0.687 | 0.130 | 0.127 | 0.051 | 0.320 | 0.070 | 0.006 | 0.113 |
| run A (local only, old data) | app | 1280 | 0.871 | 0.093 | 0.122 | 0.057 | 0.314 | 0.041 | 0.005 | 0.127 |
| run B v2 (teacher + local + replay) | val | 1280 | 0.203 | 0.216 | 0.155 | 0.066 | 0.279 | 0.120 | 0.011 | 0.210 |
| run B v2 (teacher + local + replay) | app | 1280 | 0.204 | 0.229 | 0.139 | 0.061 | 0.204 | 0.158 | 0.005 | 0.189 |
| S5_v8m_1280 (B v2 + near zone) | val | 1280 | 0.257 | 0.188 | 0.167 | 0.066 | 0.347 | 0.150 | 0.011 | 0.162 |
| S5_v8m_1280 (B v2 + near zone) | app | 1280 | 0.203 | 0.215 | 0.125 | 0.048 | 0.200 | 0.180 | 0.009 | 0.111 |
| placeholder rdd2022_pretrained.pt (NOT ours) | val | 1280 | 0.268 | 0.202 | 0.155 | 0.099 | 0.213 | 0.000 | 0.340 | 0.069 |
| placeholder rdd2022_pretrained.pt (NOT ours) | app | 1280 | 0.267 | 0.149 | 0.133 | 0.081 | 0.193 | 0.000 | 0.282 | 0.055 |

## The 1,354 annotation-site frames: 1354 frames, 537 boxes (D00 184, D10 127, D20 34, D40 192)

| Model | Style | imgsz | P | R | mAP@50 | mAP@50-95 | D00 | D10 | D20 | D40 |
|---|---|---|---|---|---|---|---|---|---|---|
| v1 (local labels only, near zone, 1024) | val | 1024 | 0.181 | 0.149 | 0.103 | 0.039 | 0.115 | 0.149 | 0.075 | 0.075 |
| v1 (local labels only, near zone, 1024) | app | 1024 | 0.190 | 0.151 | 0.095 | 0.036 | 0.118 | 0.108 | 0.083 | 0.071 |
| run A (local only, old data) | val | 1280 | 0.085 | 0.099 | 0.038 | 0.012 | 0.072 | 0.048 | 0.007 | 0.024 |
| run A (local only, old data) | app | 1280 | 0.088 | 0.102 | 0.038 | 0.013 | 0.069 | 0.055 | 0.007 | 0.022 |
| run B v2 (teacher + local + replay) | val | 1280 | 0.201 | 0.206 | 0.115 | 0.046 | 0.079 | 0.208 | 0.116 | 0.058 |
| run B v2 (teacher + local + replay) | app | 1280 | 0.206 | 0.189 | 0.109 | 0.051 | 0.070 | 0.198 | 0.095 | 0.073 |
| S5_v8m_1280 (B v2 + near zone) | val | 1280 | 0.303 | 0.225 | 0.153 | 0.087 | 0.139 | 0.264 | 0.126 | 0.081 |
| S5_v8m_1280 (B v2 + near zone) | app | 1280 | 0.270 | 0.248 | 0.133 | 0.100 | 0.116 | 0.274 | 0.059 | 0.082 |
| placeholder rdd2022_pretrained.pt (NOT ours) | val | 1280 | 0.020 | 0.049 | 0.006 | 0.002 | 0.008 | 0.000 | 0.008 | 0.009 |
| placeholder rdd2022_pretrained.pt (NOT ours) | app | 1280 | 0.024 | 0.049 | 0.006 | 0.002 | 0.016 | 0.000 | 0.004 | 0.005 |


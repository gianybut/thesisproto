# Deployment

2026-11-11 13:14: model **v2b** deployed **before the test evaluation**.

- Weights: `runs/local/v2b/weights/best.pt` copied to `ml/models/oculubak_v2b.pt`
- `ml/models/model_config.json`: conf 0.25, imgsz 1024, grey border 24 px, TTA off, NMS IoU 0.45, classes D00, D10, D20, D40
- Fused with: `ml/models/oculubak_v3.pt` (run v3, imgsz 1280), `ml/models/oculubak_S5_v8m_1920.pt` (run S5_v8m_1920, imgsz 1280) (weighted box fusion, `backend/services/box_fusion.py`; the threshold applies to the fused score)
- Threshold calibrated on reviewed val (270 frames): P 0.37, R 0.30, F1 0.33
- Data snapshot: `labels_FINAL_20261111_013131.db`
- Previous model: `ml/models/oculubak_v1.pt` (config kept as `ml/models/model_config.previous.json`; `python ml/local/deploy_model.py --rollback`)
- Unchanged: road band, near zone, NMS IoU 0.45, tracking, fixed-spot filter, AI check.

Next: restart the backend, then check one survey end to end.

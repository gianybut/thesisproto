# Deployment

2026-11-11 04:48: model **v1** deployed **before the test evaluation**.

- Weights: `runs/local/v1/weights/best.pt` copied to `ml/models/oculubak_v1.pt`
- `ml/models/model_config.json`: conf 0.24, imgsz 1024, NMS IoU 0.45, classes D00, D10, D20, D40
- Threshold calibrated on full val (1624 frames): P 0.20, R 0.18, F1 0.19
- Data snapshot: `labels_FINAL_20261111_013131.db`
- Previous model: `ml/models/rdd2022_pretrained.pt` (config kept as `ml/models/model_config.previous.json`; `python ml/local/deploy_model.py --rollback`)
- Unchanged: road band, near zone, NMS IoU 0.45, tracking, fixed-spot filter, AI check.

Next: restart the backend, then check one survey end to end.

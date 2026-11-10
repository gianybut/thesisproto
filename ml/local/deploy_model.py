"""Deploy the chosen, calibrated, tested model to the app (the last step of the training plan).

    python ml/local/deploy_model.py --run Bv2

Only the weights and the confidence threshold change; the detection algorithm (road band,
imgsz 1280, NMS IoU 0.45, tracking, fixed-spot filter, AI check) stays as it is.

1. Checks the run is the one calibrated (results/threshold_calibration.json) and tested once
   (results/test_eval_done.json), and that the model has the four classes D00, D10, D20, D40.
2. Keeps the current ml/models/best.pt as ml/models/best_previous.pt (once; never overwritten),
   then copies runs/v2/<run>/weights/best.pt to ml/models/best.pt.
3. backend/app.py: MODEL_PATH -> ml/models/best.pt (it pointed at the rdd2022_pretrained.pt demo
   placeholder).
4. backend/services/video_processor.py: CONF_THRESHOLD -> the calibrated threshold.
5. Writes results/deployment.md. Restart the backend afterwards (Stop OcuLubak / start it again),
   then check one survey end to end: python tools/upload_recording.py R06
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime

import calibrate_threshold as cal
from common import ROOT

MODELS = ROOT / 'ml' / 'models'
APP = ROOT / 'backend' / 'app.py'
PROC = ROOT / 'backend' / 'services' / 'video_processor.py'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    a = ap.parse_args()
    calib = json.loads(cal.RESULT.read_text()) if cal.RESULT.exists() else None
    if not calib or calib['run'] != a.run:
        sys.exit(f'{a.run} has no calibrated threshold (calibrate_threshold.py --run {a.run}).')
    done = ROOT / 'results' / 'test_eval_done.json'
    if not done.exists() or json.loads(done.read_text()).get('run') != a.run:
        sys.exit(f'{a.run} has not been through the one test evaluation (test_eval.py --run {a.run}).')
    src = cal.weights_for(a.run)
    from ultralytics import YOLO
    names = YOLO(str(src)).names
    if [names[i] for i in range(len(names))] != cal.CODES:
        sys.exit(f'Unexpected classes {names}; not deployed.')
    thr = calib['threshold']

    dst = MODELS / 'best.pt'
    keep = MODELS / 'best_previous.pt'
    if dst.exists() and not keep.exists():
        shutil.copy2(dst, keep)
    shutil.copy2(src, dst)

    s = APP.read_text(encoding='utf-8')
    line = re.search(r"^\s*app\.config\['MODEL_PATH'\] = .*$", s, flags=re.M)
    if not line:
        sys.exit('MODEL_PATH line not found in backend/app.py; the weights were copied but the app was not switched.')
    new_line = re.sub(r"'[^']+\.pt'", "'best.pt'", line.group(0))
    APP.write_text(s.replace(line.group(0), new_line, 1), encoding='utf-8')

    s = PROC.read_text(encoding='utf-8')
    line = re.search(r'^CONF_THRESHOLD = [0-9.]+.*$', s, flags=re.M)
    if not line:
        sys.exit('CONF_THRESHOLD line not found in video_processor.py; the model was switched but not the threshold.')
    old_thr = line.group(0)
    PROC.write_text(s.replace(old_thr, f'CONF_THRESHOLD = {thr:.2f}    # calibrated on the reviewed local val set '
                                       f'(results/threshold_calibration.md, model {a.run})', 1), encoding='utf-8')

    md = ['# Deployment', '', f'{datetime.now():%Y-%m-%d %H:%M}: model **{a.run}** deployed.', '',
          f'- Weights: `{src.relative_to(ROOT).as_posix()}` copied to `ml/models/best.pt`'
          + (' (the previous best.pt is kept as `ml/models/best_previous.pt`)' if keep.exists() else ''),
          f'- `backend/app.py`: `{new_line.strip()}`',
          f'- `backend/services/video_processor.py`: CONF_THRESHOLD {re.search(r"[0-9.]+", old_thr.split("=")[1]).group(0)} -> {thr:.2f}',
          f'- Classes: {", ".join(cal.CODES)}', '- Unchanged: road band, imgsz 1280, NMS IoU 0.45, tracking, fixed-spot filter, AI check.',
          '', 'Next: restart the backend, then `python tools/upload_recording.py R06` (one survey end to end).']
    (ROOT / 'results' / 'deployment.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

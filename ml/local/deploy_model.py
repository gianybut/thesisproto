"""Deploy the chosen, calibrated model to the app (the last step of the training plan).

    python ml/local/deploy_model.py --run v1 --before-test     # Wednesday: v1, test not run yet (§7)
    python ml/local/deploy_model.py --run v2                   # Saturday: the final, test-evaluated model
    python ml/local/deploy_model.py --rollback                 # back to the previous model_config.json
    python ml/local/deploy_model.py --restore placeholder      # a named config: model_config.placeholder.json

Named configs kept in ml/models/: model_config.placeholder.json (the demo placeholder,
rdd2022_pretrained.pt at conf 0.15 / 1280) and model_config.v1_conf024.json (v1 at conf 0.24, chosen on
full val).

Only the weights, the confidence threshold and the input size change; the detection algorithm (road
band, near zone, NMS IoU 0.45, tracking, fixed-spot filter, AI check) stays as it is.

1. Checks the run is the one calibrated (results/threshold_calibration.json) and has the four classes
   D00, D10, D20, D40. Without --before-test it must also have had the one test evaluation
   (results/test_eval_done.json).
2. Copies <run dir>/weights/best.pt to ml/models/oculubak_<run>.pt (no existing file is overwritten
   or deleted, so every earlier model stays available for rollback). If that file already holds the
   same weights (a new threshold for the same run), it is reused and only the config changes.
3. Writes ml/models/model_config.json (weights, conf threshold, imgsz = the calibration's = the
   run's training size, class names, run, data snapshot) and keeps the version it replaces as
   ml/models/model_config.previous.json. The backend reads it at start (backend/model_config.py).
4. Writes results/deployment.md. Restart the backend afterwards, then check one survey end to end.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime

import calibrate_threshold as cal
from common import ROOT

MODELS = ROOT / 'ml' / 'models'
CONFIG = MODELS / 'model_config.json'
PREVIOUS = MODELS / 'model_config.previous.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run')
    ap.add_argument('--before-test', action='store_true',
                    help='deploy before the one test evaluation (it is then reported as not test-evaluated)')
    ap.add_argument('--rollback', action='store_true', help='restore model_config.previous.json')
    ap.add_argument('--restore', metavar='NAME',
                    help='restore a named config, ml/models/model_config.NAME.json (e.g. placeholder)')
    a = ap.parse_args()
    if a.restore:
        src = MODELS / f'model_config.{a.restore}.json'
        if not src.exists():
            sys.exit(f'No {src.name}.')
        old = CONFIG.read_text(encoding='utf-8') if CONFIG.exists() else None
        if old:
            PREVIOUS.write_text(old, encoding='utf-8')
        shutil.copy2(src, CONFIG)
        print(f'Restored {src.name}: {json.loads(CONFIG.read_text())["weights"]}. The replaced config is in '
              f'{PREVIOUS.name}. Restart the backend.')
        return
    if a.rollback:
        if not PREVIOUS.exists():
            sys.exit('No model_config.previous.json to roll back to.')
        cur = CONFIG.read_text(encoding='utf-8')
        shutil.copy2(PREVIOUS, CONFIG)
        PREVIOUS.write_text(cur, encoding='utf-8')
        print(f'Rolled back to {json.loads(CONFIG.read_text())["weights"]}. Restart the backend.')
        return
    if not a.run:
        sys.exit('--run is required')
    calib = json.loads(cal.RESULT.read_text()) if cal.RESULT.exists() else None
    if not calib or calib['run'] != a.run:
        sys.exit(f'{a.run} has no calibrated threshold (calibrate_threshold.py --run {a.run} --dataset nz --val ...).')
    done = ROOT / 'results' / 'test_eval_done.json'
    tested = done.exists() and json.loads(done.read_text()).get('run') == a.run
    if not tested and not a.before_test:
        sys.exit(f'{a.run} has not been through the one test evaluation; pass --before-test to deploy it anyway.')
    src = cal.weights_for(a.run)
    from ultralytics import YOLO
    names = YOLO(str(src)).names
    if [names[i] for i in range(len(names))] != cal.CODES:
        sys.exit(f'Unexpected classes {names}; not deployed.')

    dst = MODELS / f'oculubak_{a.run}.pt'
    if dst.exists():
        import hashlib
        same = hashlib.sha256(dst.read_bytes()).digest() == hashlib.sha256(src.read_bytes()).digest()
        if not same:
            sys.exit(f'{dst.name} exists already with other weights; not overwritten. Move it away first if this is a new {a.run}.')
        print(f'{dst.name} is already these weights: redeploying with the new calibration only.')
    else:
        shutil.copy2(src, dst)
    snap_p = ROOT / 'results' / 'FINAL_SNAPSHOT.txt'
    snapshot = snap_p.read_text().split()[0] if snap_p.exists() else None
    old = CONFIG.read_text(encoding='utf-8') if CONFIG.exists() else None
    if old:
        PREVIOUS.write_text(old, encoding='utf-8')
    cfg = {
        'weights': dst.relative_to(ROOT).as_posix(),
        'conf_threshold': calib['threshold'],
        'iou_threshold': cal.NMS_IOU,
        'imgsz': calib['imgsz'],
        'class_names': cal.CODES,
        'run': a.run,
        'data_snapshot': snapshot,
        'deployed_at': datetime.now().isoformat(timespec='seconds'),
        'calibration': {k: calib.get(k) for k in ('dataset', 'val_set', 'val_frames', 'val_precision', 'val_recall', 'val_f1')},
        'test_evaluated': tested,
        'note': "The team's model (" + a.run + '), trained on local human labels only.'
                + ('' if tested else ' Not test-evaluated yet: its numbers are val numbers.'),
        'previous': json.loads(old)['weights'] if old else None,
    }
    CONFIG.write_text(json.dumps(cfg, indent=1) + '\n', encoding='utf-8')

    md = ['# Deployment', '', f'{datetime.now():%Y-%m-%d %H:%M}: model **{a.run}** deployed'
          + ('' if tested else ' **before the test evaluation**') + '.', '',
          f'- Weights: `{src.relative_to(ROOT).as_posix()}` copied to `{cfg["weights"]}`',
          f'- `ml/models/model_config.json`: conf {cfg["conf_threshold"]:.2f}, imgsz {cfg["imgsz"]}, NMS IoU {cfg["iou_threshold"]}, '
          f'classes {", ".join(cal.CODES)}',
          f'- Threshold calibrated on {calib.get("val_set", "val")} val ({calib.get("val_frames", "?")} frames): '
          f'P {calib["val_precision"]:.2f}, R {calib["val_recall"]:.2f}, F1 {calib["val_f1"]:.2f}',
          f'- Data snapshot: `{snapshot}`',
          f'- Previous model: `{cfg["previous"]}` (config kept as `ml/models/model_config.previous.json`; '
          '`python ml/local/deploy_model.py --rollback`)',
          '- Unchanged: road band, near zone, NMS IoU 0.45, tracking, fixed-spot filter, AI check.',
          '', 'Next: restart the backend, then check one survey end to end.']
    (ROOT / 'results' / 'deployment.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

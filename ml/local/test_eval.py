"""The ONE test evaluation of the chosen model: local test and foreign (RDD2022) test.

    python ml/local/test_eval.py --run Bv2

Run it after the model is chosen on local val (results/chapter5_val_table.md) and its threshold is
calibrated on val (calibrate_threshold.py --run <same run>). Test is evaluated once: this script
refuses if results/test_eval_done.json exists (it records what was tested and when). Nothing it
reports may be used to change the model or the threshold afterwards.

1. build_local_yolo.py --final: the local test set from the reviewed, self-checked test labels
   (refuses if any test frame is not reviewed).
2. Local test: Ultralytics validation at imgsz 1280 (P, R, mAP@50, mAP@50-95, AP@50 per class),
   and precision / recall / F1 at the calibrated threshold with the app's settings (as in
   calibrate_threshold.py).
3. Foreign test: ml/eval_foreign.py --split test (six countries' 15% test parts, never trained on;
   the 600 replay images come from the train parts).

Writes results/test_evaluation.md (+ results/final_foreign_test.md from step 3).
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime

import calibrate_threshold as cal
from common import OUT, ROOT

DONE = ROOT / 'results' / 'test_eval_done.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True, help='the run chosen on local val (name under runs/v2)')
    a = ap.parse_args()
    if DONE.exists():
        sys.exit(f'Test was already evaluated ({DONE.read_text().strip()}). It is evaluated once only.')
    if not cal.RESULT.exists():
        sys.exit('Calibrate the threshold on val first: python ml/local/calibrate_threshold.py --run ' + a.run)
    calib = json.loads(cal.RESULT.read_text())
    if calib['run'] != a.run:
        sys.exit(f'The threshold was calibrated for {calib["run"]}, not {a.run}. Calibrate the chosen model first.')
    w = cal.weights_for(a.run)
    thr = calib['threshold']
    env = {**__import__('os').environ, 'PYTHONUTF8': '1'}

    r = subprocess.run([sys.executable, str(ROOT / 'ml' / 'local' / 'build_local_yolo.py'), '--final'], cwd=ROOT, env=env)
    if r.returncode:
        sys.exit('build_local_yolo.py --final refused or failed; nothing was evaluated.')
    DONE.write_text(json.dumps({'run': a.run, 'weights': str(w.relative_to(ROOT)), 'threshold': thr,
                                'started': datetime.now().isoformat(timespec='seconds')}))

    from ultralytics import YOLO
    m = YOLO(str(w)).val(data=str(OUT / 'yolo' / 'test.yaml'), imgsz=cal.IMGSZ, batch=4, workers=2, device=0,
                         split='val', plots=True, project=str(ROOT / 'runs' / 'eval'), name=f'localtest_{a.run}',
                         exist_ok=True, verbose=False)
    ap50 = dict(zip([int(i) for i in m.box.ap_class_index], [float(x) for x in m.box.ap50]))
    frames = cal.frames_of('test')
    rows = cal.table(frames, cal.predict(w, frames), thr)

    r = subprocess.run([sys.executable, str(ROOT / 'ml' / 'eval_foreign.py'), '--weights', str(w.relative_to(ROOT)),
                        '--imgsz', str(cal.IMGSZ), '--name', 'final', '--split', 'test', '--batch', '4'], cwd=ROOT, env=env)
    start_model = json.loads((w.parent.parent / 'run_info.json').read_text()).get('model', '')
    external = 'data/pretrained' in start_model.replace('\\', '/')
    foreign = (ROOT / 'results' / 'final_foreign_test.md')
    foreign_md = foreign.read_text(encoding='utf-8').split('\n', 2)[2] if r.returncode == 0 and foreign.exists() \
        else '_Foreign test evaluation failed; see the console output._\n'

    md = [f'# Test evaluation of the chosen model ({a.run}), done once', '',
          f'Weights `{w.relative_to(ROOT).as_posix()}`, chosen on local val (results/chapter5_val_table.md). '
          f'Confidence threshold {thr:.2f}, calibrated on local val (results/threshold_calibration.md). '
          f'Evaluated {datetime.now():%Y-%m-%d %H:%M}.', '',
          f'## Local test ({len(frames)} reviewed frames; test "no damage" frames self-checked)', '',
          'Ultralytics validation, imgsz 1280 (conf 0.001, NMS IoU 0.7):', '',
          '| P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |', '|---|---|---|---|---|---|---|---|',
          f'| {m.box.mp:.3f} | {m.box.mr:.3f} | {m.box.map50:.3f} | {m.box.map:.3f} | '
          + ' | '.join(f'{ap50.get(i, 0.0):.3f}' for i in range(4)) + ' |', '',
          f'At the app\'s settings (threshold {thr:.2f}, imgsz {cal.IMGSZ}, NMS IoU {cal.NMS_IOU}; correct = same class '
          f'and IoU >= {cal.MATCH_IOU}):', ''] + cal.md_rows(rows) + \
         ['', 'Classes with fewer than 20 test boxes (figures uncertain): '
          + (', '.join(f'{r[0]} ({r[1]})' for r in rows[:-1] if r[1] < 20) or 'none') + '.', '',
          '## Foreign test (RDD2022, six countries)' + (' - NOT HELD OUT' if external else ''), '',
          (f'**Not held out:** this model starts from an external checkpoint (`{start_model}`) trained on its '
           'own split of the public RDD2022 images, which very likely includes images of this foreign test '
           'split. These figures are not a held-out result (results/pretrained_sources.md).\n' if external else ''),
          foreign_md.replace('| **all six countries** |', '| **all six countries** (not held out) |') if external else foreign_md]
    (ROOT / 'results' / 'test_evaluation.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    d = json.loads(DONE.read_text())
    d['finished'] = datetime.now().isoformat(timespec='seconds')
    DONE.write_text(json.dumps(d))
    print('\n'.join(md))


if __name__ == '__main__':
    main()

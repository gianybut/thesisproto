"""The ONE test evaluation of the DEPLOYED near-zone model (a single model or a fusion).

    python ml/local/test_eval_nz.py --dry-run [--device cpu]   same code on the 270 reviewed VAL frames;
                                                               test is not read, nothing is recorded
    python ml/local/test_eval_nz.py --team-approved            the one test run (needs the team's OK)

test_eval.py (unchanged) scores one model on the old full-frame data at 1280. The deployed model
works on the near-zone crops (data/local/yolo_nz) and may be a fusion of several models, so this
script scores exactly what ml/models/model_config.json deploys: its weights and ensemble members,
each at its own size, the grey border, weighted box fusion (backend/services/box_fusion.py) and the
calibrated threshold. The one-run rule is shared with test_eval.py: both refuse when
results/test_eval_done.json exists, and nothing reported here may be used to change the model or
the threshold afterwards.

1. check_counts.py: the dataset counts and the test hash must be unchanged.
2. Local test (yolo_nz/test.txt, 270 reviewed frames; "no damage" frames self-checked):
   - precision / recall / F1 at the deployed threshold with the app's settings (calibrate_threshold's
     code: members at conf 0.05, fused, threshold on the fused score);
   - mAP@50 / mAP@50-95 / AP@50 per class at conf 0.001, NMS IoU 0.7 (Ultralytics' AP,
     eval_val_sets.metrics), for the fusion and for each member alone.
3. Foreign test (RDD2022, six countries' test parts): ml/eval_foreign.py --split test for each
   member alone (the fusion is not scored on foreign images). A member that starts from an external
   RDD2022 checkpoint is marked NOT HELD OUT.

Writes results/test_evaluation.md and sets "test_evaluated": true in model_config.json.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime

import calibrate_threshold as cal
import eval_val_sets as ev
from common import OUT, ROOT
from infer_sweep import run as sweep_run

sys.path.insert(0, str(ROOT / 'backend' / 'services'))
from box_fusion import fuse  # noqa: E402

DONE = ROOT / 'results' / 'test_eval_done.json'
CONFIG = ROOT / 'ml' / 'models' / 'model_config.json'
YDIR = OUT / 'yolo_nz'
EXTERNAL_START = ('data/pretrained', 'ml/models/pretrained')


def gts_from(split):
    """eval_val_sets.gts reads labels/val; the same for another split's folder."""
    def gts(stem, w, h):
        lab = YDIR / 'labels' / split / f'{stem}.txt'
        out = []
        if lab.exists():
            for row in lab.read_text().split('\n'):
                p = row.split()
                if len(p) == 5:
                    c, x, y, bw, bh = int(p[0]), *map(float, p[1:])
                    out.append((c, (x - bw / 2) * w, (y - bh / 2) * h, (x + bw / 2) * w, (y + bh / 2) * h))
        return out
    return gts


def external_start(run):
    """True if the run was started from a checkpoint the team did not train (its RDD2022 split is unknown)."""
    try:
        start = json.loads((cal.run_dir(run) / 'run_info.json').read_text()).get('model', '')
    except (OSError, ValueError, SystemExit):
        return False
    return any(k in start.replace('\\', '/') for k in EXTERNAL_START)


def map_row(name, m):
    return f'| {name} | {m["p"]:.3f} | {m["r"]:.3f} | {m["m50"]:.3f} | {m["m5095"]:.3f} | ' + \
           ' | '.join(f'{x:.3f}' for x in m['ap50']) + ' |'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='the 270 reviewed val frames instead of test; records nothing')
    ap.add_argument('--team-approved', action='store_true', help='the team approved the single test run')
    ap.add_argument('--device', default='0', help="'cpu' to leave the GPU to a training run")
    ap.add_argument('--skip-foreign', action='store_true', help='local test only')
    a = ap.parse_args()
    if a.dry_run == a.team_approved:
        sys.exit('Give exactly one of --dry-run (val, nothing recorded) or --team-approved (the one test run).')
    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
    members = [(cfg.get('run', 'model'), ROOT / cfg['weights'], int(cfg['imgsz']))] + \
              [(m.get('run', 'member'), ROOT / m['weights'], int(m['imgsz'])) for m in cfg.get('ensemble') or []]
    thr, border = float(cfg['conf_threshold']), int(cfg.get('border_px') or 0)
    if cfg.get('tta'):
        sys.exit('The deployed config uses TTA, which this script does not score.')
    title = ' + '.join(n for n, _, _ in members)
    env = {**__import__('os').environ, 'PYTHONUTF8': '1'}

    if a.dry_run:
        split, list_name, what = 'val', 'val_reviewed.txt', 'DRY RUN on the 270 reviewed val frames (test not read)'
    else:
        if DONE.exists():
            sys.exit(f'Test was already evaluated ({DONE.read_text().strip()}). It is evaluated once only.')
        if cfg.get('test_evaluated'):
            sys.exit('model_config.json says this model is already test-evaluated.')
        r = subprocess.run([sys.executable, str(ROOT / 'ml' / 'local' / 'check_counts.py')], cwd=ROOT, env=env)
        if r.returncode:
            sys.exit('check_counts.py failed (dataset counts or test hash changed); nothing was evaluated.')
        split, list_name, what = 'test', 'test.txt', 'local test'
        DONE.write_text(json.dumps({'run': title, 'weights': [str(w.relative_to(ROOT)) for _, w, _ in members],
                                    'threshold': thr, 'script': 'test_eval_nz.py',
                                    'started': datetime.now().isoformat(timespec='seconds')}))

    # 2a. At the deployed threshold, the app's settings.
    frames = cal.frames_of(split, ydir=YDIR, list_name=list_name)
    if len(members) > 1:
        det = cal.predict_fused([(w, sz) for _, w, sz in members], frames, a.device, border)
    else:
        det = cal.predict(members[0][1], frames, a.device, members[0][2], border)
    rows = cal.table(frames, det, thr)

    # 2b. mAP at conf 0.001: each member, then the fusion.
    from ultralytics import YOLO
    stems = [img.stem for img, _ in frames]
    paths = {img.stem: str(img) for img, _ in frames}
    per = {n: sweep_run(YOLO(str(w)), stems, paths, sz, border, 0, a.device) for n, w, sz in members}
    ev.gts = gts_from(split)
    maps = []
    if len(members) > 1:
        first = members[0][0]
        fused = {s: {'wh': per[first][s]['wh'], 'pred': fuse([per[n][s]['pred'] for n, _, _ in members])} for s in stems}
        maps.append((f'**{title}** (fused, deployed)', ev.metrics(fused, stems)))
    maps += [(f'{n} alone ({sz} px)', ev.metrics(per[n], stems)) for n, _, sz in members]

    # 3. Foreign test, each member alone.
    foreign_md = []
    if not a.dry_run and not a.skip_foreign:
        for n, w, sz in members:
            name = f'final_{n}'
            r = subprocess.run([sys.executable, str(ROOT / 'ml' / 'eval_foreign.py'), '--weights', w.relative_to(ROOT).as_posix(),
                                '--imgsz', str(sz), '--name', name, '--split', 'test', '--batch', '4'], cwd=ROOT, env=env)
            f = ROOT / 'results' / f'{name}_foreign_test.md'
            held_out = not external_start(n)
            foreign_md += [f'### {n} ({sz} px)' + ('' if held_out else ' - NOT HELD OUT'), '']
            if not held_out:
                foreign_md += ['**Not held out:** this model starts from an external checkpoint trained on its own split of '
                               'the public RDD2022 images, which very likely includes images of this foreign test split '
                               '(results/pretrained_sources.md).', '']
            foreign_md += [f.read_text(encoding='utf-8').split('\n', 2)[2] if r.returncode == 0 and f.exists()
                           else '_Foreign test evaluation failed; see the console output._', '']

    md = [f'# Test evaluation of the deployed model ({title}), done once' if not a.dry_run
          else f'# DRY RUN of the test evaluation code ({title}) on the 270 reviewed val frames', '',
          'Model as deployed (`ml/models/model_config.json`): '
          + '; '.join(f'`{w.relative_to(ROOT).as_posix()}` at {sz} px' for _, w, sz in members)
          + (', fused (weighted box fusion)' if len(members) > 1 else '')
          + f'; grey border {border} px; confidence threshold {thr:.2f}, calibrated on the 270 reviewed val frames '
          f'(results/threshold_calibration.md). Chosen on those frames (results/final_selection.md). '
          f'Evaluated {datetime.now():%Y-%m-%d %H:%M}.', '',
          f'## {what.capitalize() if a.dry_run else "Local test"} ({len(frames)} near-zone frames'
          + ('' if a.dry_run else '; test "no damage" frames self-checked') + ')', '',
          f'At the app\'s settings (threshold {thr:.2f}, NMS IoU {cal.NMS_IOU}; correct = same class and IoU >= {cal.MATCH_IOU}):',
          ''] + cal.md_rows(rows) + \
         ['', 'Classes with fewer than 20 boxes (figures uncertain): '
          + (', '.join(f'{r[0]} ({r[1]})' for r in rows[:-1] if r[1] < 20) or 'none') + '.', '',
          f'Ranking metrics (conf 0.001, NMS IoU 0.7, grey border {border} px; Ultralytics\' AP):', '',
          '| Model | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |', '|---|---|---|---|---|---|---|---|---|'] + \
         [map_row(n, m) for n, m in maps]
    if foreign_md:
        md += ['', '## Foreign test (RDD2022, six countries), each member alone', '',
               'The fusion is not scored on foreign images; these are the single models at their own sizes.', ''] + foreign_md
    text = '\n'.join(md) + '\n'
    if a.dry_run:
        print(text)
        return
    (ROOT / 'results' / 'test_evaluation.md').write_text(text, encoding='utf-8')
    d = json.loads(DONE.read_text())
    d['finished'] = datetime.now().isoformat(timespec='seconds')
    DONE.write_text(json.dumps(d))
    cfg['test_evaluated'] = True
    CONFIG.write_text(json.dumps(cfg, indent=1), encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()

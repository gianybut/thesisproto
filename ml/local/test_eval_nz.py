"""The ONE test evaluation of the DEPLOYED near-zone model (a single model or a fusion).

    python ml/local/test_eval_nz.py --dry-run [--device cpu]   same code with the 270 reviewed VAL frames in
                                                               place of test; test is not read, nothing recorded
    python ml/local/test_eval_nz.py --team-approved            the one test run (needs the team's OK)
    python ml/local/test_eval_nz.py --team-approved --labels-corrected
                                                               the only allowed re-run: after corrections to the
                                                               test labels (the test hash must have changed)

The metrics are fixed in results/metric_definitions.md (written and committed before the test run).

test_eval.py (unchanged) scores one model on the old full-frame data at 1280. The deployed model
works on the near-zone crops (data/local/yolo_nz) and may be a fusion of several models, so this
script scores exactly what ml/models/model_config.json deploys: its weights and ensemble members,
each at its own size, the grey border, weighted box fusion (backend/services/box_fusion.py) and the
calibrated threshold. The one-run rule is shared with test_eval.py: both refuse when
results/test_eval_done.json exists, and nothing reported here may be used to change the model, the
threshold or the operating point afterwards.

1. check_counts.py: the dataset counts and the test hash must be unchanged.
2. Local test (yolo_nz/test.txt, 270 reviewed frames) and, beside it, the 270 reviewed val frames:
   - mAP@50 / mAP@50-95 / AP@50 per class at conf 0.001, NMS IoU 0.7 (Ultralytics' AP,
     eval_val_sets.metrics), for the fusion and for each member alone;
   - precision / recall / F1 at the deployed threshold with the app's settings (members at conf 0.05,
     fused, threshold on the fused score), 95% Wilson intervals;
   - classification accuracy among detections matched to a reviewed box at IoU >= 0.5 (any class);
   - the high-confidence operating point: lowest threshold with val precision >= 0.80, scored on test.
3. Foreign test (RDD2022, six countries' test parts): ml/eval_foreign.py --split test for each
   member alone. A member that starts from an external RDD2022 checkpoint is marked NOT HELD OUT.

Writes results/test_evaluation.md (with Chapter V tables), results/test_evaluation.json, the DONE
marker, and sets "test_evaluated": true in model_config.json.
"""

import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime

import calibrate_threshold as cal
import eval_val_sets as ev
from check_counts import test_hash
from common import OUT, ROOT
from infer_sweep import run as sweep_run
from label_quality import match

sys.path.insert(0, str(ROOT / 'backend' / 'services'))
from box_fusion import fuse  # noqa: E402

DONE = ROOT / 'results' / 'test_eval_done.json'
CONFIG = ROOT / 'ml' / 'models' / 'model_config.json'
REPORT = ROOT / 'results' / 'test_evaluation.md'
YDIR = OUT / 'yolo_nz'
EXTERNAL_START = ('data/pretrained', 'ml/models/pretrained')
CODES = cal.CODES
NAMES = {'D00': 'Longitudinal crack', 'D10': 'Transverse crack', 'D20': 'Alligator crack', 'D40': 'Pothole'}
HIGH_P = 0.80
SWEEP = [round(0.01 * i, 2) for i in range(1, 100)]


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


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def class_accuracy(frames, det, thr):
    """Matched (any class, IoU >= 0.5) detections with the reviewed class / all matched. Plus the 4x4 table."""
    conf_m = [[0] * 4 for _ in range(4)]
    for img, gts in frames:
        preds = [d for d in det[img] if d['conf'] >= thr]
        for i, j in match(preds, gts, cal.MATCH_IOU, same_class=False).items():
            conf_m[gts[j]['cls']][preds[i]['cls']] += 1
    right = sum(conf_m[c][c] for c in range(4))
    n = sum(map(sum, conf_m))
    return {'correct': right, 'matched': n, 'accuracy': right / n if n else 0.0, 'ci': wilson(right, n), 'table': conf_m}


def overall(frames, det, thr):
    r = cal.table(frames, det, thr)[-1]
    return {'boxes': r[1], 'tp': r[2], 'fp': r[3], 'fn': r[4], 'p': r[5], 'r': r[6], 'f1': r[7]}


def high_conf_point(frames, det):
    pts = [(t, overall(frames, det, t)) for t in SWEEP]
    ok = [(t, o) for t, o in pts if o['tp'] + o['fp'] and o['p'] >= HIGH_P]
    if ok:
        return {'reached': True, 'threshold': ok[0][0], 'val': ok[0][1]}
    t, o = max(pts, key=lambda x: (x[1]['p'], -x[0]))
    return {'reached': False, 'best_threshold': t, 'best_val': o}


def evaluate(split, list_name, members, border, thr, device):
    """Everything for one frame set: app-setting detections, P/R/F1, class accuracy, mAP (fusion + members)."""
    from ultralytics import YOLO
    frames = cal.frames_of(split, ydir=YDIR, list_name=list_name)
    if len(members) > 1:
        det = cal.predict_fused([(w, sz) for _, w, sz in members], frames, device, border)
    else:
        det = cal.predict(members[0][1], frames, device, members[0][2], border)
    stems = [img.stem for img, _ in frames]
    paths = {img.stem: str(img) for img, _ in frames}
    per = {n: sweep_run(YOLO(str(w)), stems, paths, sz, border, 0, device) for n, w, sz in members}
    ev.gts = gts_from(split)
    maps = []
    if len(members) > 1:
        first = members[0][0]
        fused = {s: {'wh': per[first][s]['wh'], 'pred': fuse([per[n][s]['pred'] for n, _, _ in members])} for s in stems}
        maps.append(('fusion', ev.metrics(fused, stems)))
    maps += [(n, ev.metrics(per[n], stems)) for n, _, _ in members]
    return {'frames': frames, 'det': det, 'rows': cal.table(frames, det, thr), 'overall': overall(frames, det, thr),
            'cls_acc': class_accuracy(frames, det, thr), 'maps': maps,
            'n_frames': len(frames), 'n_empty': sum(1 for _, g in frames if not g)}


def f3(x):
    return f'{x:.3f}'


def pct(x):
    return f'{100 * x:.1f}%'


def ci(c):
    return f'{pct(c[0])} to {pct(c[1])}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='the 270 reviewed val frames in place of test; records nothing')
    ap.add_argument('--team-approved', action='store_true', help='the team approved the single test run')
    ap.add_argument('--labels-corrected', action='store_true',
                    help='with --team-approved: the one allowed re-run, after corrections to the test labels')
    ap.add_argument('--device', default='0', help="'cpu' to leave the GPU to a training run")
    ap.add_argument('--skip-foreign', action='store_true', help='local test only')
    a = ap.parse_args()
    if a.dry_run == a.team_approved:
        sys.exit('Give exactly one of --dry-run (val, nothing recorded) or --team-approved (the one test run).')
    if a.labels_corrected and not a.team_approved:
        sys.exit('--labels-corrected goes with --team-approved.')
    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
    members = [(cfg.get('run', 'model'), ROOT / cfg['weights'], int(cfg['imgsz']))] + \
              [(m.get('run', 'member'), ROOT / m['weights'], int(m['imgsz'])) for m in cfg.get('ensemble') or []]
    thr, border = float(cfg['conf_threshold']), int(cfg.get('border_px') or 0)
    if cfg.get('tta'):
        sys.exit('The deployed config uses TTA, which this script does not score.')
    title = ' + '.join(n for n, _, _ in members)
    env = {**os.environ, 'PYTHONUTF8': '1'}
    history, run_no = [], 1

    if a.dry_run:
        split, list_name = 'val', 'val_reviewed.txt'
    else:
        th = test_hash(YDIR)
        if DONE.exists():
            prev = json.loads(DONE.read_text())
            if not a.labels_corrected:
                sys.exit(f'Test was already evaluated ({json.dumps(prev)}). It is evaluated once only; the one '
                         'allowed re-run is --labels-corrected after corrections to the test labels.')
            if prev.get('script') != 'test_eval_nz.py' or 'finished' not in prev:
                sys.exit('The recorded test run is not a finished test_eval_nz.py run; no re-run.')
            if prev.get('test_hash') == th:
                sys.exit('The test labels are unchanged since the recorded run (same test hash): no re-run.')
            history = prev.pop('history', []) + [prev]
            run_no = len(history) + 1
            if REPORT.exists():
                REPORT.replace(REPORT.with_name(f'test_evaluation_run{run_no - 1}.md'))
        else:
            if a.labels_corrected:
                sys.exit('No recorded test run to repeat; run --team-approved without --labels-corrected.')
            if cfg.get('test_evaluated'):
                sys.exit('model_config.json says this model is already test-evaluated.')
        r = subprocess.run([sys.executable, str(ROOT / 'ml' / 'local' / 'check_counts.py')]
                           + (['--no-compare'] if a.labels_corrected else []), cwd=ROOT, env=env)
        if r.returncode:
            sys.exit('check_counts.py failed (dataset counts or test hash changed); nothing was evaluated.')
        split, list_name = 'test', 'test.txt'
        DONE.write_text(json.dumps({'run': title, 'weights': [str(w.relative_to(ROOT)) for _, w, _ in members],
                                    'threshold': thr, 'script': 'test_eval_nz.py', 'test_hash': th, 'run_no': run_no,
                                    'labels_corrected': a.labels_corrected, 'history': history,
                                    'started': datetime.now().isoformat(timespec='seconds')}))

    # Val (the selection set) first, then the target set (test, or val again in a dry run).
    print('Scoring the 270 reviewed val frames ...', flush=True)
    val = evaluate('val', 'val_reviewed.txt', members, border, thr, a.device)
    hc = high_conf_point(val['frames'], val['det'])
    if a.dry_run:
        tst = val
    else:
        print('Scoring the local test frames ...', flush=True)
        tst = evaluate(split, list_name, members, border, thr, a.device)
    hc_test = overall(tst['frames'], tst['det'], hc['threshold']) if hc['reached'] else None

    # Foreign test, each member alone.
    foreign_md, foreign_rows = [], []
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
            if r.returncode == 0 and f.exists():
                body = f.read_text(encoding='utf-8')
                foreign_md += [body.split('\n', 2)[2], '']
                row = next((l.replace('**', '') for l in body.splitlines() if l.replace('**', '').startswith('| all six countries |')), None)
                if row:
                    foreign_rows.append((n, sz, held_out, [c.strip() for c in row.strip().strip('|').split('|')]))
            else:
                foreign_md += ['_Foreign test evaluation failed; see the console output._', '']

    # ---- Report ----
    T = 'Test' if not a.dry_run else 'Val (dry run)'
    fus_v, fus_t = val['maps'][0][1], tst['maps'][0][1]
    ov_v, ov_t = val['overall'], tst['overall']
    ca_v, ca_t = val['cls_acc'], tst['cls_acc']
    when = datetime.now()
    md = [f'# Test evaluation of the deployed model ({title})' + (f', run {run_no}' if run_no > 1 else ', done once')
          if not a.dry_run else f'# DRY RUN of the test evaluation code ({title}): val frames in place of test', '',
          'Model as deployed (`ml/models/model_config.json`): '
          + '; '.join(f'`{w.relative_to(ROOT).as_posix()}` at {sz} px' for _, w, sz in members)
          + (', fused (weighted box fusion)' if len(members) > 1 else '')
          + f'; grey border {border} px; confidence threshold {thr:.2f}, calibrated on the 270 reviewed val frames '
          f'(results/threshold_calibration.md). Chosen on those frames (results/final_selection.md). Metrics as fixed in '
          f'results/metric_definitions.md. Evaluated {when:%Y-%m-%d %H:%M}.', '']
    if run_no > 1:
        md += [f'Re-run {run_no} after corrections to the test labels (--labels-corrected); the earlier report is kept as '
               f'results/test_evaluation_run{run_no - 1}.md.', '']
    md += [f'{T}: {tst["n_frames"]} near-zone frames ({tst["n_empty"]} with no damage), {ov_t["boxes"]} reviewed boxes. '
           f'Validation: {val["n_frames"]} reviewed frames ({val["n_empty"]} with no damage), {ov_v["boxes"]} boxes. '
           'Class counts are small (see the box counts), so per-class figures are uncertain.', '',
           '## Chapter V tables (ready to paste)', '',
           '**Table 5.A. Detection accuracy of the deployed model (AP at IoU 0.5; conf 0.001, NMS IoU 0.7).**', '',
           f'| Metric | Validation (270 reviewed frames) | {T} ({tst["n_frames"]} frames) |', '|---|---|---|',
           f'| mAP@50 | {f3(fus_v["m50"])} | {f3(fus_t["m50"])} |',
           f'| mAP@50-95 | {f3(fus_v["m5095"])} | {f3(fus_t["m5095"])} |'] + \
          [f'| AP@50, {NAMES[c]} ({c}) | {f3(fus_v["ap50"][i])} ({fus_v["per_class_boxes"][i]} boxes) | '
           f'{f3(fus_t["ap50"][i])} ({fus_t["per_class_boxes"][i]} boxes) |' for i, c in enumerate(CODES)] + \
          ['', f'**Table 5.B. Precision, recall and F1 at the deployed threshold ({thr:.2f}), all classes.**', '',
           '| Set | Boxes | Correct | False alarms | Missed | Precision (95% CI) | Recall (95% CI) | F1 |',
           '|---|---|---|---|---|---|---|---|']
    for lab, o in (('Validation', ov_v), (T, ov_t)):
        md.append(f'| {lab} | {o["boxes"]} | {o["tp"]} | {o["fp"]} | {o["fn"]} | '
                  f'{o["p"]:.2f} ({ci(wilson(o["tp"], o["tp"] + o["fp"]))}) | '
                  f'{o["r"]:.2f} ({ci(wilson(o["tp"], o["boxes"]))}) | {o["f1"]:.2f} |')
    md += ['', f'**Table 5.C. {T}: precision, recall and F1 per class at {thr:.2f}.**', ''] + cal.md_rows(tst['rows']) + \
          ['', f'**Table 5.D. Classification accuracy among detections (threshold {thr:.2f}; detections matched to a '
           'reviewed box at IoU >= 0.5, any class).**', '',
           '| Set | Matched detections | Correct class | Accuracy (95% CI) |', '|---|---|---|---|']
    for lab, c in (('Validation', ca_v), (T, ca_t)):
        md.append(f'| {lab} | {c["matched"]} | {c["correct"]} | {pct(c["accuracy"])} ({ci(c["ci"])}) |')
    md += ['', f'{T}: matched pairs by reviewed class (rows) and detected class (columns):', '',
           '| Reviewed \\ Detected | ' + ' | '.join(CODES) + ' |', '|---|' + '---|' * 4] + \
          [f'| {c} | ' + ' | '.join(str(x) for x in ca_t['table'][i]) + ' |' for i, c in enumerate(CODES)]
    md += ['', f'**Table 5.E. High-confidence operating point (lowest threshold with validation precision >= {HIGH_P:.2f}).**', '']
    if hc['reached']:
        v = hc['val']
        md += ['| Set | Threshold | Correct | False alarms | Missed | Precision | Recall |', '|---|---|---|---|---|---|---|',
               f'| Validation | {hc["threshold"]:.2f} | {v["tp"]} | {v["fp"]} | {v["fn"]} | {v["p"]:.2f} | {v["r"]:.2f} |',
               f'| {T} | {hc["threshold"]:.2f} | {hc_test["tp"]} | {hc_test["fp"]} | {hc_test["fn"]} | '
               f'{hc_test["p"]:.2f} | {hc_test["r"]:.2f} |']
        if v['tp'] + v['fp'] < 10:
            md += ['', f'Note: on validation this point rests on {v["tp"] + v["fp"]} detection(s) out of {v["boxes"]} reviewed '
                   'boxes, so it is not a usable operating point; it is reported as defined (results/metric_definitions.md, '
                   'section 4).']
    else:
        b = hc['best_val']
        md += [f'Not reached: no threshold from 0.01 to 0.99 gives validation precision >= {HIGH_P:.2f}. The highest is '
               f'{b["p"]:.2f} at {hc["best_threshold"]:.2f} (recall {b["r"]:.2f}, {b["tp"]} correct, {b["fp"]} false alarms). '
               'No test figure is reported for this point (results/metric_definitions.md, section 4).']
    if foreign_rows:
        md += ['', '**Table 5.F. Foreign test (RDD2022 test part, six countries), each model alone (secondary result).**', '',
               '| Model | Images | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 | Held out |',
               '|---|---|---|---|---|---|---|---|---|---|---|'] + \
              [f'| {n} ({sz} px) | ' + ' | '.join(cells[1:]) + f' | {"yes" if h else "**NOT HELD OUT**"} |'
               for n, sz, h, cells in foreign_rows]
    md += ['', '## Each model alone and the fusion (mAP, for information)', '',
           '| Set | Model | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |',
           '|---|---|---|---|---|---|---|---|---|---|']
    for lab, res in (('Validation', val), (T, tst)):
        for n, m in res['maps']:
            name = f'**{title} (fused, deployed)**' if n == 'fusion' else f'{n} alone'
            md.append(f'| {lab} | {name} | {f3(m["p"])} | {f3(m["r"])} | {f3(m["m50"])} | {f3(m["m5095"])} | '
                      + ' | '.join(f3(x) for x in m['ap50']) + ' |')
    md += ['', f'## Validation per class at {thr:.2f} (for comparison with Table 5.C)', ''] + cal.md_rows(val['rows'])
    if foreign_md:
        md += ['', '## Foreign test in full (RDD2022, six countries), each member alone', '',
               'The fusion is not scored on foreign images; these are the single models at their own sizes.', ''] + foreign_md
    text = '\n'.join(md) + '\n'
    if a.dry_run:
        print(text)
        return
    REPORT.write_text(text, encoding='utf-8')
    strip = lambda r: {k: v for k, v in r.items() if k not in ('frames', 'det')}  # noqa: E731
    (ROOT / 'results' / 'test_evaluation.json').write_text(json.dumps(
        {'model': title, 'threshold': thr, 'when': when.isoformat(timespec='seconds'), 'run_no': run_no,
         'val': strip(val), 'test': strip(tst), 'high_conf': hc, 'high_conf_test': hc_test,
         'foreign': [{'model': n, 'imgsz': sz, 'held_out': h, 'all_six': cells} for n, sz, h, cells in foreign_rows]},
        indent=1), encoding='utf-8')
    d = json.loads(DONE.read_text())
    d['finished'] = datetime.now().isoformat(timespec='seconds')
    DONE.write_text(json.dumps(d))
    cfg['test_evaluated'] = True
    CONFIG.write_text(json.dumps(cfg, indent=1), encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()

"""Start or resume one YOLO training run, with the logging tools/watch_training.py reads.

    python ml/train_run.py --project runs/teacher --name teacher --data data/rdd2022/teacher/data.yaml \
        --imgsz 960 --batch 6 --epochs 30 --patience 8
    python ml/train_run.py --project runs/teacher --name teacher ... --workers 4          # resume, fewer workers
    python ml/train_run.py --project runs/teacher --name teacher ... --set amp=False lr0=0.005   # NaN recovery

- If <project>/<name>/weights/last.pt exists and the run has not finished, it RESUMES from it
  (Ultralytics resume=True); a run is never restarted from scratch. --workers/--batch override on
  resume; --set key=value rewrites the saved training settings in last.pt first (for amp, lr0).
- Fixed settings for every run on this PC: device 0, amp, cache=False, seed 42, deterministic,
  workers 6 (team decision 2026-11-09; watch_training.py drops it to 4 when RAM passes 85%).
- Keeps Windows awake while it runs (SetThreadExecutionState, released automatically when the
  process ends, so nothing needs restoring afterwards).
- Writes <run>/run_info.json (settings, command, versions, every session's start/end/exit) and
  <run>/epochs.csv (per epoch: wall time, seconds, losses, P, R, mAP50, AP50 per class, GPU memory).
Console output: --log <file> shows everything live in the terminal (the Ultralytics progress bars)
AND appends it to the file (used by the VS Code tasks, tools/train_queue.py). Without --log, start
it with output redirected to <run>/train.log (tools/start_training.ps1, hidden; no longer used).
"""

import argparse
import csv
import ctypes
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODES = ['D00', 'D10', 'D20', 'D40']
# Augmentation for every run from 2026-11-10 on (team decision; Chapter III). HSV stays at the
# Ultralytics defaults, written out so the log shows the values. The teacher (2026-11-09) used the
# Ultralytics defaults, which differ only in degrees (0).
AUG = dict(fliplr=0.5, flipud=0.0, mixup=0.0, degrees=5.0, scale=0.5, mosaic=1.0, close_mosaic=10,
           hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, translate=0.1, shear=0.0, perspective=0.0, copy_paste=0.0)


class Tee:
    """Write to the console and to a log file; the console keeps its own properties (isatty etc.)."""

    def __init__(self, stream, f):
        self.stream, self.f = stream, f

    def write(self, s):
        self.stream.write(s)
        self.f.write(s)
        return len(s)

    def flush(self):
        self.stream.flush()
        self.f.flush()

    def __getattr__(self, k):
        return getattr(self.stream, k)


def tee_to(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    f = open(path, 'a', encoding='utf-8', buffering=1)
    f.write(f'\n===== {datetime.now():%Y-%m-%d %H:%M:%S} {" ".join(sys.argv)}\n')
    sys.stdout, sys.stderr = Tee(sys.stdout, f), Tee(sys.stderr, f)


def keep_awake():
    if os.name == 'nt':   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED: no sleep while this process lives
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)


def parse_set(items):
    out = {}
    for it in items or []:
        k, v = it.split('=', 1)
        out[k] = {'true': True, 'false': False}.get(v.lower(), v)
        try:
            out[k] = float(v) if '.' in v or 'e' in v.lower() else int(v)
        except ValueError:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--data', required=True)
    ap.add_argument('--model', default='yolov8m.pt', help='COCO weights by default')
    ap.add_argument('--imgsz', type=int, required=True)
    ap.add_argument('--batch', type=int, required=True)
    ap.add_argument('--epochs', type=int, required=True)
    ap.add_argument('--patience', type=int, required=True)
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--extra', nargs='*', default=[], help='more Ultralytics settings for a NEW run, key=value')
    ap.add_argument('--set', nargs='*', default=[], help='rewrite saved settings in last.pt before resuming')
    ap.add_argument('--log', help='also append all output to this file (shown live in the terminal too)')
    ap.add_argument('--stop-at', help='hard stop "YYYY-MM-DD HH:MM": not started after it; a running run ends '
                                      'after the epoch in which it passes (best.pt kept)')
    ap.add_argument('--max-mem-gib', type=float, help='abort with exit code 3 if, in the first 2 epochs, the GPU '
                    'memory reserved passes this or Ultralytics lowers the batch after an out-of-memory error')
    a = ap.parse_args()
    if a.log:
        tee_to(a.log)   # before ultralytics is imported, so its logger and progress bars use it
    stop_at = datetime.strptime(a.stop_at, '%Y-%m-%d %H:%M') if a.stop_at else None
    if stop_at and datetime.now() >= stop_at:
        print(f'[{datetime.now():%H:%M:%S}] Past the hard stop {stop_at:%Y-%m-%d %H:%M}: {a.name} not started.', flush=True)
        return 0

    import torch
    import ultralytics
    from ultralytics import YOLO

    keep_awake()
    run = (ROOT / a.project / a.name).resolve()
    run.mkdir(parents=True, exist_ok=True)
    info_p = run / 'run_info.json'
    info = json.loads(info_p.read_text()) if info_p.exists() else {}
    if info.get('finished'):
        print(f'{run} already finished at {info["finished"]}; nothing to do.')
        return 0
    last = run / 'weights' / 'last.pt'
    resume = last.exists()
    session = dict(start=datetime.now().isoformat(timespec='seconds'), mode='resume' if resume else 'new',
                   command=[sys.executable] + sys.argv, workers=a.workers, batch=a.batch, set=a.set)
    info.setdefault('sessions', []).append(session)
    info.update(name=a.name, project=a.project, data=a.data, model=a.model, imgsz=a.imgsz, batch=a.batch,
                epochs=a.epochs, patience=a.patience, workers=a.workers, seed=42,
                versions=dict(torch=torch.__version__, cuda=torch.version.cuda, ultralytics=ultralytics.__version__,
                              gpu=torch.cuda.get_device_name(0)))
    info_p.write_text(json.dumps(info, indent=1))

    if resume and a.set:
        ck = torch.load(last, map_location='cpu', weights_only=False)
        ck['train_args'].update(parse_set(a.set))
        torch.save(ck, last)
        print(f'Rewrote saved settings in {last.name}: {parse_set(a.set)}', flush=True)

    epochs_p = run / 'epochs.csv'
    t0 = time.time()

    def on_fit_epoch_end(tr):
        m = tr.metrics or {}
        row = dict(epoch=tr.epoch + 1, time=datetime.now().isoformat(timespec='seconds'),
                   session_s=round(time.time() - t0, 1),
                   box_loss=round(float(tr.tloss[0]), 5), cls_loss=round(float(tr.tloss[1]), 5),
                   dfl_loss=round(float(tr.tloss[2]), 5),
                   precision=round(m.get('metrics/precision(B)', float('nan')), 5),
                   recall=round(m.get('metrics/recall(B)', float('nan')), 5),
                   mAP50=round(m.get('metrics/mAP50(B)', float('nan')), 5),
                   mAP50_95=round(m.get('metrics/mAP50-95(B)', float('nan')), 5),
                   gpu_mem_gib=round(torch.cuda.memory_reserved(0) / 2 ** 30, 2), batch=tr.batch_size,
                   workers=tr.args.workers)
        try:
            vm = tr.validator.metrics
            ap50 = dict(zip([int(i) for i in vm.ap_class_index], [float(x) for x in vm.box.ap50]))
        except Exception:
            ap50 = {}
        for i, c in enumerate(CODES):
            row[f'AP50_{c}'] = round(ap50[i], 5) if i in ap50 else ''
        if stop_at and datetime.now() >= stop_at and not tr.stop:
            tr.stop = True   # ends after this epoch; best.pt is already saved
            print(f'[{datetime.now():%H:%M:%S}] HARD STOP {stop_at:%H:%M} reached after epoch {tr.epoch + 1}: '
                  f'training ends now, best.pt is kept as a candidate.', flush=True)
            inf = json.loads(info_p.read_text())
            inf['hard_stop'] = dict(at=datetime.now().isoformat(timespec='seconds'), after_epoch=tr.epoch + 1)
            info_p.write_text(json.dumps(inf, indent=1))
        new = not epochs_p.exists()
        with open(epochs_p, 'a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)

    def on_train_batch_end(tr):
        if a.max_mem_gib and tr.epoch < 2:
            peak = torch.cuda.max_memory_reserved(0) / 2 ** 30
            lowered = tr.batch_size < a.batch
            if peak > a.max_mem_gib or lowered:
                why = (f'GPU memory reserved {peak:.2f} GiB > {a.max_mem_gib} GiB' if peak > a.max_mem_gib else
                       f'Ultralytics lowered the batch to {tr.batch_size} after running out of memory')
                print(f'\n[{datetime.now():%H:%M:%S}] MEMORY GUARD: {why} in epoch {tr.epoch + 1}; '
                      f'aborting {run.name} (exit code 3).', flush=True)
                inf = json.loads(info_p.read_text())
                inf['aborted'] = dict(at=datetime.now().isoformat(timespec='seconds'), reason=why)
                info_p.write_text(json.dumps(inf, indent=1))
                raise SystemExit(3)

    if resume:
        print(f'[{datetime.now():%H:%M:%S}] Resuming {run.name} from {last}', flush=True)
        model = YOLO(str(last))
        model.add_callback('on_fit_epoch_end', on_fit_epoch_end)
        model.add_callback('on_train_batch_end', on_train_batch_end)
        model.train(resume=True, workers=a.workers, batch=a.batch)
    else:
        print(f'[{datetime.now():%H:%M:%S}] New run {run.name}', flush=True)
        model = YOLO(a.model)
        model.add_callback('on_fit_epoch_end', on_fit_epoch_end)
        model.add_callback('on_train_batch_end', on_train_batch_end)
        extra = parse_set(a.extra)
        aug = {k: extra.pop(k, v) for k, v in AUG.items()}
        info = json.loads(info_p.read_text())
        info.update(augmentation=aug, extra=extra)
        info_p.write_text(json.dumps(info, indent=1))
        model.train(data=str((ROOT / a.data).resolve()), imgsz=a.imgsz, batch=a.batch, epochs=a.epochs,
                    patience=a.patience, workers=a.workers, device=0, amp=True, cache=False, seed=42,
                    deterministic=True, project=str((ROOT / a.project).resolve()), name=a.name, exist_ok=True,
                    plots=True, **aug, **extra)

    info = json.loads(info_p.read_text())
    info['sessions'][-1].update(end=datetime.now().isoformat(timespec='seconds'), exit='ok',
                                seconds=round(time.time() - t0))
    info['finished'] = datetime.now().isoformat(timespec='seconds')
    info['train_seconds_total'] = sum(s.get('seconds', 0) for s in info['sessions'])
    info_p.write_text(json.dumps(info, indent=1))
    print(f'[{datetime.now():%H:%M:%S}] Finished {run.name}', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""Step 0 of TRAINING_TASK_WEDNESDAY.md: benchmark YOLOv8m on this PC, then estimate every planned run.

    python ml/benchmark_step0.py --all              # prepare sample, benchmark 640/960/1024(/1280), estimate
    python ml/benchmark_step0.py --estimate         # re-print the estimate table from saved benchmarks

Sample: 300 train + 60 val RDD2022 images (50 + 10 from each of Japan, India, Czech, Norway,
United_States, China_MotorBike; China_Drone excluded, aerial view), only images with at least one
D00/D10/D20/D40 box, fixed seed. Each image size trains YOLOv8m (COCO weights) for 1 epoch with
batch=-1 (AutoBatch), amp, cache=False, workers=4, device=0, in its own subprocess, one at a time.
Console output goes to runs/step0/<run>/train.log; measurements to runs/step0/<run>/bench.json;
the table to results/step0_benchmark.md.
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RDD = ROOT / 'RDD2022_raw' / 'RDD2022'
SAMPLE = ROOT / 'ml' / 'benchmark' / 'rdd_sample'
RUNS = ROOT / 'runs' / 'step0'
RESULTS = ROOT / 'results'
POOLS_JSON = ROOT / 'ml' / 'benchmark' / 'rdd2022_pools.json'

SEED = 42
COUNTRIES = ['Japan', 'India', 'Czech', 'Norway', 'United_States', 'China_MotorBike']  # no China_Drone
CLASSES = ['D00', 'D10', 'D20', 'D40']           # YOLO ids 0-3, same order as ml/dataset_prep.py
PER_COUNTRY_TRAIN, PER_COUNTRY_VAL = 50, 10
IMGSZ_STEP0 = [640, 960, 1024]
IMGSZ_EXTRA = [1280]                             # only to judge whether 1280 fits overnight (Step 6.1)
SKIP_BATCHES = 3                                 # warm-up batches left out of the steady-state rate
# AutoBatch on this PC over-measures (its profile spills into shared system memory under the Windows
# driver), so each size is also run at the batch the task expects to fit in 8 GB.
FIXED_BATCH = {640: 16, 960: 8, 1024: 6, 1280: 4}
FITS_GIB = 7.0                                   # torch peak reserved above this = too close to the 8 GB card

# Planned data sizes (Steps 1-2 not done yet: the local counts are the task's caps).
LOCAL_TRAIN, LOCAL_VAL = 600, 120
N_FOREIGN_CAP, INDIA_STEP4 = 2000, 3000
TRAIN_SHARE = 0.70


def yolo_lines(xml_path):
    root = ET.parse(xml_path).getroot()
    w = int(root.find('size').findtext('width')); h = int(root.find('size').findtext('height'))
    out = []
    for o in root.iter('object'):
        name = o.findtext('name', '').strip()
        if name not in CLASSES or not w or not h:
            continue
        b = o.find('bndbox')
        x1, y1, x2, y2 = (float(b.findtext(k)) for k in ('xmin', 'ymin', 'xmax', 'ymax'))
        cx, cy = min(1, max(0, (x1 + x2) / 2 / w)), min(1, max(0, (y1 + y2) / 2 / h))
        bw, bh = min(1, max(0, (x2 - x1) / w)), min(1, max(0, (y2 - y1) / h))
        out.append(f'{CLASSES.index(name)} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}')
    return out


def pools():
    """Per country: annotated train images with at least one of the four classes (cached)."""
    if POOLS_JSON.exists():
        return json.loads(POOLS_JSON.read_text())
    res = {}
    for c in COUNTRIES:
        xmls = RDD / c / 'train' / 'annotations' / 'xmls'
        res[c] = sorted(p.stem for p in xmls.glob('*.xml') if yolo_lines(p))
    POOLS_JSON.parent.mkdir(parents=True, exist_ok=True)
    POOLS_JSON.write_text(json.dumps(res))
    return res


def prepare():
    if (SAMPLE / 'data.yaml').exists():
        print(f'Sample already at {SAMPLE}')
        return
    rng = random.Random(SEED)
    pool = pools()
    for split in ('train', 'val'):
        (SAMPLE / 'images' / split).mkdir(parents=True, exist_ok=True)
        (SAMPLE / 'labels' / split).mkdir(parents=True, exist_ok=True)
    for c in COUNTRIES:
        picked = rng.sample(pool[c], PER_COUNTRY_TRAIN + PER_COUNTRY_VAL)
        for i, stem in enumerate(picked):
            split = 'train' if i < PER_COUNTRY_TRAIN else 'val'
            src = next((RDD / c / 'train' / 'images').glob(stem + '.*'))
            shutil.copy2(src, SAMPLE / 'images' / split / src.name)
            lines = yolo_lines(RDD / c / 'train' / 'annotations' / 'xmls' / f'{stem}.xml')
            (SAMPLE / 'labels' / split / f'{stem}.txt').write_text('\n'.join(lines) + '\n')
    names = '\n'.join(f'  {i}: {n}' for i, n in enumerate(CLASSES))
    (SAMPLE / 'data.yaml').write_text(
        f'# Step 0 benchmark sample, seed {SEED}\npath: {SAMPLE.as_posix()}\n'
        f'train: images/train\nval: images/val\nnc: {len(CLASSES)}\nnames:\n{names}\n')
    print(f'Sample written to {SAMPLE}: {6 * PER_COUNTRY_TRAIN} train, {6 * PER_COUNTRY_VAL} val')


class GpuSampler:
    """Peak whole-card memory (includes the Windows desktop), utilisation and temperature, every second."""

    def __init__(self):
        self.peak_mem = self.peak_temp = 0
        self.util = []
        self._halt = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while not self._halt.is_set():
            try:
                out = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu,temperature.gpu',
                                      '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10)
                mem, util, temp = (int(x) for x in out.stdout.strip().split(','))
                self.peak_mem, self.peak_temp = max(self.peak_mem, mem), max(self.peak_temp, temp)
                self.util.append(util)
            except Exception:
                pass
            self._halt.wait(1)

    def close(self):
        self._halt.set()
        self._thread.join(timeout=15)


def run_name(imgsz, batch):
    return f'bench_{imgsz}' + ('' if batch == -1 else f'_b{batch}')


def run_one(imgsz, batch=-1):
    import torch
    import ultralytics
    from ultralytics import YOLO

    name = run_name(imgsz, batch)
    t = {'batch_ends': []}
    model = YOLO('yolov8m.pt')
    model.add_callback('on_train_start', lambda tr: t.update(train_start=time.time(), batch=tr.batch_size,
                                                             n_train=len(tr.train_loader.dataset)))
    model.add_callback('on_train_epoch_start', lambda tr: t.update(epoch_start=time.time()))
    model.add_callback('on_train_batch_end', lambda tr: t['batch_ends'].append(time.time()))
    model.add_callback('on_train_epoch_end', lambda tr: t.update(epoch_train_end=time.time()))
    model.add_callback('on_fit_epoch_end', lambda tr: t.update(epoch_end=time.time()))

    gpu = GpuSampler()   # fresh process per size, so torch's peak counters start at zero
    wall0 = time.time()
    settings = dict(data=str(SAMPLE / 'data.yaml'), epochs=1, imgsz=imgsz, batch=batch, device=0, amp=True,
                    cache=False, workers=4, seed=SEED, deterministic=True, project=str(RUNS), name=name,
                    exist_ok=True, plots=True, val=True)
    model.train(**settings)
    wall = time.time() - wall0
    gpu.close()

    b, ends = t['batch'], t['batch_ends']
    n_train = t['n_train']
    full = len(ends) - (1 if n_train % b else 0)          # batches that were full
    steady_imgs = (full - SKIP_BATCHES) * b
    steady_s = ends[full - 1] - ends[SKIP_BATCHES - 1]
    res = dict(
        imgsz=imgsz, batch=b, batch_mode='AutoBatch (batch=-1)' if batch == -1 else 'fixed', n_train=n_train, n_val=6 * PER_COUNTRY_VAL, batches=len(ends),
        epoch_s=round(t['epoch_end'] - t['epoch_start'], 1),
        epoch_train_s=round(t['epoch_train_end'] - t['epoch_start'], 1),
        epoch_val_s=round(t['epoch_end'] - t['epoch_train_end'], 1),
        steady_train_img_per_s=round(steady_imgs / steady_s, 2),
        setup_s=round(t['train_start'] - wall0, 1), wall_s=round(wall, 1),
        torch_peak_reserved_gib=round(torch.cuda.max_memory_reserved(0) / 2 ** 30, 2),
        torch_peak_alloc_gib=round(torch.cuda.max_memory_allocated(0) / 2 ** 30, 2),
        card_peak_used_mib=gpu.peak_mem, card_peak_temp_c=gpu.peak_temp,
        mean_util_pct=round(sum(gpu.util) / max(1, len(gpu.util))),
        versions=dict(torch=torch.__version__, cuda=torch.version.cuda, ultralytics=ultralytics.__version__,
                      gpu=torch.cuda.get_device_name(0), python=sys.version.split()[0]),
        settings=settings, finished=datetime.now().isoformat(timespec='seconds'))
    (RUNS / name / 'bench.json').write_text(json.dumps(res, indent=1))
    print('BENCH', json.dumps(res))


def run_all(sizes):
    prepare()
    for s in sizes:
        for b in (-1, FIXED_BATCH[s]):
            out = RUNS / run_name(s, b)
            if (out / 'bench.json').exists():
                print(f'{out.name}: already benchmarked, skipping', flush=True); continue
            out.mkdir(parents=True, exist_ok=True)
            env = dict(os.environ, PYTHONUTF8='1')
            print(f'[{datetime.now():%H:%M:%S}] {out.name} started -> {out / "train.log"}', flush=True)
            with open(out / 'train.log', 'w', encoding='utf-8') as log:
                rc = subprocess.run([sys.executable, __file__, '--one', str(s), '--batch', str(b)], stdout=log,
                                    stderr=subprocess.STDOUT, cwd=ROOT, env=env).returncode
            print(f'[{datetime.now():%H:%M:%S}] {out.name} finished, exit {rc}', flush=True)
    estimate()


def estimate():
    runs = [json.loads(p.read_text()) for p in sorted(RUNS.glob('bench_*/bench.json'))]
    if not runs:
        sys.exit('No benchmarks yet.')
    # Per size, the fastest batch that stayed inside the card (no spill into shared system memory).
    bench = {}
    for r in runs:
        r['fits'] = r['torch_peak_reserved_gib'] <= FITS_GIB
        best = bench.get(r['imgsz'])
        if r['fits'] and (best is None or r['steady_train_img_per_s'] > best['steady_train_img_per_s']):
            bench[r['imgsz']] = r
    for r in runs:   # nothing fitted at this size: estimate from what ran, flagged in the table
        bench.setdefault(r['imgsz'], r)
    pool = {c: int(len(v) * TRAIN_SHARE) for c, v in pools().items()}

    def epoch_s(n_train, imgsz):
        r = bench[imgsz]
        train = n_train / r['steady_train_img_per_s']
        overhead = r['epoch_train_s'] - r['n_train'] / r['steady_train_img_per_s']   # loader start-up, warm-up
        val = r['epoch_val_s'] * LOCAL_VAL / r['n_val']
        return train + max(0, overhead) + val

    def hours(n_train, imgsz, epochs):
        return (epochs * epoch_s(n_train, imgsz) + 2 * epoch_s(0, imgsz)) / 3600   # + final val, start-up

    n_foreign = min(min(pool.values()), N_FOREIGN_CAP)
    india4 = min(INDIA_STEP4, pool['India'])
    singles = sorted(pool, key=pool.get)
    big_pair = sorted(combinations(pool, 2), key=lambda p: pool[p[0]] + pool[p[1]])[-1]

    rows = []   # (step, run, n_train, imgsz, epochs)
    rows.append(('4', f'Safety: local + India {india4}', LOCAL_TRAIN + india4, 960, 40))
    rows.append(('5', 'Local only', LOCAL_TRAIN, 640, 20))
    for c in COUNTRIES:
        rows.append(('5', f'Local + {c} {n_foreign}', LOCAL_TRAIN + n_foreign, 640, 20))
    for i in range(3):
        rows.append(('5', f'Pair {i + 1} of top 3 ({n_foreign // 2} + {n_foreign // 2})', LOCAL_TRAIN + n_foreign, 640, 20))
    final_sizes = sorted(set([960, 1024, 1280]) & set(bench))
    mixes = [(c,) for c in singles] + [big_pair]
    six = {}
    for imgsz in final_sizes:
        for mix in mixes:
            n = 3 * LOCAL_TRAIN + sum(pool[c] for c in mix)
            six[(imgsz, mix)] = (n, hours(n, imgsz, 50),
                                 LOCAL_TRAIN + int(0.2 * sum(pool[c] for c in mix)))

    lines = ['# Step 0 benchmark (YOLOv8m, RTX 4060 8 GB)', '',
             f'Generated {datetime.now():%Y-%m-%d %H:%M}. Sample: {6 * PER_COUNTRY_TRAIN} train / '
             f'{6 * PER_COUNTRY_VAL} val RDD2022 images (6 countries, no China_Drone), 1 epoch, batch=-1, '
             'amp, cache=False, workers=4, seed 42.', '',
             '| imgsz | batch | chosen by | epoch (s) | train part (s) | val part (s) | steady train img/s | '
             'peak torch reserved (GiB) | peak card used (MiB, incl. desktop) | peak temp (°C) | mean util | '
             'used for estimate |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in sorted(runs, key=lambda r: (r['imgsz'], r['batch_mode'] != 'fixed')):
        s = r['imgsz']
        lines.append(f"| {s}{' (extra)' if s in IMGSZ_EXTRA else ''} | {r['batch']} | {r['batch_mode']} | "
                     f"{r['epoch_s']} | {r['epoch_train_s']} | {r['epoch_val_s']} | {r['steady_train_img_per_s']} | "
                     f"{r['torch_peak_reserved_gib']} | {r['card_peak_used_mib']} | {r['card_peak_temp_c']} | "
                     f"{r['mean_util_pct']}% | {'yes' if bench.get(s) is r else ('no, too close to 8 GB' if not r['fits'] else 'no')} |")
    lines += ['', '## Estimated wall-clock of the planned runs (all epochs; early stopping can only shorten)', '',
              f'Assumed: local train {LOCAL_TRAIN} (pseudo-labelled cap), local val {LOCAL_VAL}; foreign train pools '
              f'= {int(TRAIN_SHARE * 100)}% of the annotated images with a target class: '
              + ', '.join(f'{c} {n}' for c, n in pool.items()) + f'. N_foreign = {n_foreign}.', '',
              '| Step | Run | train images | imgsz | epochs | est. hours |', '|---|---|---|---|---|---|']
    total45 = 0
    for step, run, n, imgsz, ep in rows:
        h = hours(n, imgsz, ep); total45 += h
        lines.append(f'| {step} | {run} | {n} | {imgsz} | {ep} | {h:.2f} |')
    lines.append(f'| | **Steps 4 + 5 total** | | | | **{total45:.1f}** |')
    lines += ['', '### Step 6 (mix decided in Step 5; local ×3 = '
              f'{3 * LOCAL_TRAIN} in 6.1)', '',
              '| imgsz | mix | 6.1 train images | 6.1 hours (50 ep) | 6.2 train images | 6.2 hours (30 ep) |',
              '|---|---|---|---|---|---|']
    for (imgsz, mix), (n, h, n2) in six.items():
        lines.append(f"| {imgsz} | {' + '.join(mix)} | {n} | {h:.1f} | {n2} | {hours(n2, imgsz, 30):.1f} |")
    text = '\n'.join(lines) + '\n'
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / 'step0_benchmark.md').write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--extra', action='store_true', help='also benchmark 1280')
    ap.add_argument('--one', type=int)
    ap.add_argument('--batch', type=int, default=-1)
    ap.add_argument('--estimate', action='store_true')
    ap.add_argument('--prepare', action='store_true')
    a = ap.parse_args()
    if a.one:
        run_one(a.one, a.batch)
    elif a.all:
        run_all(IMGSZ_STEP0 + (IMGSZ_EXTRA if a.extra else []))
    elif a.prepare:
        prepare()
    else:
        estimate()

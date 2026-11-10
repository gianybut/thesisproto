"""The training runs of the 2026-11-10 strategy, in one place.

    python ml/local/runs_v2.py --list                 # settings of every run
    python ml/local/runs_v2.py --run Bv2_noreplay     # in THIS terminal, live progress, also to train.log
                                                      # (what the VS Code tasks and tools/train_queue.py use)
    python ml/local/runs_v2.py --start Bv1            # old: hidden process (no longer used)
Both resume from last.pt if the run was started before (never from scratch).

Every run: imgsz 1280, batch 4, workers 2 (RAM), SGD (optimizer=auto would ignore lr0), seed 42,
the augmentation in ml/train_run.py (AUG), validation on the reviewed LOCAL val set.
At start, the run's data file and training list are copied into the run folder, so a later rebuild
of data/local/yolo (after the AL batch) cannot change what an earlier run trained on.
"""

import argparse
import re
import shutil
import subprocess
import sys

from common import OUT, ROOT

Y = OUT / 'yolo'
TEACHER = 'runs/teacher/teacher/weights/best.pt'
COMMON = dict(imgsz=1280, batch=4, epochs=40, patience=10, workers=2)   # deadline plan of 2026-11-10
RUNS = {
    'A': dict(data='A.yaml', model='yolov8m.pt', extra=['optimizer=SGD', 'lr0=0.01'],
              note='local only, from COCO weights'),
    'Bv1': dict(data='B.yaml', model=TEACHER, extra=['optimizer=SGD', 'lr0=0.001'],
                note="from the teacher's weights; local (D10/D20 frames x3) + 600 six-country replay images"),
    'Bv2': dict(data='B.yaml', model=TEACHER, extra=['optimizer=SGD', 'lr0=0.001'],
                note='as Bv1, on the train set enlarged by the AL batch'),
    'Bv2_freeze10': dict(data='B.yaml', model=TEACHER, extra=['optimizer=SGD', 'lr0=0.001', 'freeze=10'],
                         note='as Bv2, first 10 layers frozen', cancelled='2026-11-10 11:20, team decision'),
    'Bv2_noreplay': dict(data='B_noreplay.yaml', model=TEACHER, extra=['optimizer=SGD', 'lr0=0.001'],
                         note='as Bv2, without the RDD2022 replay', cancelled='2026-11-10 12:00, team decision (new plan)'),
}

# Step 5 of the plan of 2026-11-10 12:00: near-zone data (data/local/yolo_nz, D10/D20/D40 frames x3 +
# 600 replay), AdamW lr0 0.0005 with cosine decay, 40 epochs, patience 10 (team, 13:03; was 60/15), the AUG of train_run.py
# (close_mosaic 10, fliplr 0.5, flipud 0, mixup 0, degrees 5). Starting points = the top 2 of the
# zero-shot check (results/zero_shot_nz_val.md): B v2 (YOLOv8m) and YOLOv12s (SreekarAditya).
V12S = 'data/pretrained/SreekarAditya__yolo-rdd2022-benchmark/yolo-rdd2022-benchmark/yolo12s_seed0_best.pt'
STEP5 = dict(data='B.yaml', ydir=OUT / 'yolo_nz', project='runs/v3', stop_at='2026-11-10 22:15',
             extra=['optimizer=AdamW', 'lr0=0.0005', 'cos_lr=True'])
for _name, _model, _imgsz, _batch, _note in (
        ('S5_v8m_1280', 'runs/v2/Bv2/weights/best.pt', 1280, 4, 'YOLOv8m from B v2'),
        ('S5_v12s_1280', V12S, 1280, 2, 'YOLOv12s from SreekarAditya RDD2022 (external)'),
        ('S5_v8m_1600', 'runs/v2/Bv2/weights/best.pt', 1600, 2, 'YOLOv8m from B v2, larger input'),
        ('S5_v8m_1920', 'runs/v2/Bv2/weights/best.pt', 1920, 2, 'YOLOv8m from B v2, native width'),
        ('S5_v12s_1024', V12S, 1024, 2, 'YOLOv12s, smaller input (fallback)')):
    RUNS[_name] = dict(STEP5, model=_model, set=dict(imgsz=_imgsz, batch=_batch, epochs=40, patience=10),
                       note=f'{_note}, imgsz {_imgsz}, batch {_batch}; near zone; AdamW 0.0005 cosine; 40/10')
# 1920 is close to the 8 GiB limit (7.14 GiB in the benchmark): abort in its first 2 epochs above 7.6 GiB
# (or if Ultralytics lowers the batch after an out-of-memory error) and run 1600 instead (team, 13:03).
RUNS['S5_v8m_1920'].update(max_mem=7.6, fallback='S5_v8m_1600')


def snapshot(name, spec):
    """Copy the data file and the lists it names into <project>/<name>/data/; return the copied yaml."""
    ydir = spec.get('ydir', Y)
    dst = ROOT / spec.get('project', 'runs/v2') / name / 'data'
    dst.mkdir(parents=True, exist_ok=True)
    text = (ydir / spec['data']).read_text()
    for key in ('train', 'val'):
        lst = re.search(rf'^{key}: (\S+)$', text, flags=re.M).group(1)
        shutil.copy2(ydir / lst, dst / lst)
    text = re.sub(r'^path: .*$', f'path: {dst.as_posix()}', text, flags=re.M)
    (dst / spec['data']).write_text(text)
    return dst / spec['data']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--start')
    ap.add_argument('--run')
    a = ap.parse_args()
    name = a.run or a.start
    if a.list or not name:
        for n, s in RUNS.items():
            print(f'{n:14} data {s["data"]:16} from {s["model"]:38} {" ".join(s["extra"])}  ({s["note"]})')
        print('All:', ', '.join(f'{k} {v}' for k, v in COMMON.items()))
        return
    spec = RUNS[name]
    project = spec.get('project', 'runs/v2')
    run_dir = ROOT / project / name
    data = run_dir / 'data' / spec['data']
    if not (run_dir / 'weights' / 'last.pt').exists():   # new run: freeze its data now
        data = snapshot(name, spec)
    args = ['--data', data.relative_to(ROOT).as_posix(), '--model', spec['model']] + \
           [x for k, v in {**COMMON, **spec.get('set', {})}.items() for x in (f'--{k}', str(v))] + ['--extra'] + spec['extra']
    if a.run:   # foreground, in this terminal
        cmd = [sys.executable, '-u', str(ROOT / 'ml' / 'train_run.py'), '--project', project, '--name', name,
               '--log', str(run_dir / 'train.log')]
        if spec.get('stop_at'):
            cmd += ['--stop-at', spec['stop_at']]
        if spec.get('max_mem'):
            cmd += ['--max-mem-gib', str(spec['max_mem'])]
        code = subprocess.run(cmd + args, cwd=ROOT).returncode
        if code == 3 and spec.get('fallback'):
            print(f'\n{name} stopped by the memory guard; running the fallback {spec["fallback"]} instead.\n', flush=True)
            return subprocess.run([sys.executable, '-u', __file__, '--run', spec['fallback']], cwd=ROOT).returncode
        return code
    out = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                          str(ROOT / 'tools' / 'start_training.ps1'), '-Project', 'runs\\v2', '-Name', name] + args,
                         capture_output=True, text=True)
    print(out.stdout.strip() or out.stderr.strip())


if __name__ == '__main__':
    sys.exit(main())

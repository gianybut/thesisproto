"""Training queue, run in the VS Code terminal "Train: queue" (Terminal > Run Task > Train: queue).

    python tools/train_queue.py

Works through runs/queue.txt from the top, one job at a time, IN THIS TERMINAL (live Ultralytics
progress bars; each training also appends to its run's train.log). Lines:

    run <NAME>              training run NAME of ml/local/runs_v2.py (resumes from last.pt if started)
    py <script> [args...]   any project Python script, e.g. py ml/local/val_table.py
    wait <project/name>     until that run's run_info.json says finished (a run started elsewhere)
    # ...                   comment, skipped

A job is removed from the queue only when it has finished; if it fails (exit code not 0) the queue
stops and says so, and the job stays at the top: fix it, then press Enter to try it again. If the
terminal is closed while a training runs, starting the task again resumes that run from last.pt.
Before any training it waits while another training process holds the GPU (one at a time).
Claude Code adds jobs by editing runs/queue.txt; the file is read again before every job.
Finished jobs: runs/queue_done.txt (time, exit code, minutes).
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / 'runs' / 'queue.txt'
DONE = ROOT / 'runs' / 'queue_done.txt'
PY = sys.executable


def jobs():
    if not QUEUE.exists():
        return []
    return [l.strip() for l in QUEUE.read_text(encoding='utf-8-sig').splitlines() if l.strip() and not l.strip().startswith('#')]


def drop_first(job):
    lines = QUEUE.read_text(encoding='utf-8-sig').splitlines()
    for i, l in enumerate(lines):
        if l.strip() == job:
            del lines[i]
            break
    QUEUE.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')


def training_running():
    me = os.getpid()
    for p in psutil.process_iter(['pid', 'cmdline']):
        try:
            cl = p.info['cmdline'] or []
            if p.info['pid'] != me and any(c.endswith('train_run.py') for c in cl):
                return cl[cl.index('--name') + 1] if '--name' in cl else '?'
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, IndexError):
            pass
    return None


def finished(run):
    p = ROOT / run / 'run_info.json'
    return p.exists() and bool(json.loads(p.read_text()).get('finished'))


def banner(text):
    print('\n' + '=' * 100 + f'\n[{datetime.now():%a %H:%M:%S}] {text}\n' + '=' * 100, flush=True)


def main():
    os.environ['PYTHONUTF8'] = '1'
    print(f'Training queue: {QUEUE.relative_to(ROOT)} (Ctrl+C stops the queue AND the job running in it).', flush=True)
    idle = False
    while True:
        js = jobs()
        if not js:
            if not idle:
                banner('Queue empty; waiting for jobs (checked every 30 s)')
                idle = True
            time.sleep(30)
            continue
        idle = False
        job = js[0]
        kind, _, rest = job.partition(' ')
        start = time.time()
        if kind == 'wait':
            banner(f'Waiting for {rest} to finish (it runs elsewhere; follow it with Get-Content <log> -Wait)')
            while not finished(rest):
                time.sleep(30)
            code = 0
        elif kind in ('run', 'py'):
            if kind == 'run':
                other = training_running()
                if other:
                    banner(f'Another training ({other}) holds the GPU; {rest} starts when it ends')
                    while training_running():
                        time.sleep(30)
                cmd = [PY, '-u', str(ROOT / 'ml' / 'local' / 'runs_v2.py'), '--run', rest]
            else:
                cmd = [PY, '-u'] + rest.split()
            banner(f'START {job}')
            code = subprocess.run(cmd, cwd=ROOT).returncode
        else:
            print(f'Unknown job "{job}" (use run / py / wait); skipped.', flush=True)
            code = 0
        mins = (time.time() - start) / 60
        if code != 0:
            banner(f'FAILED {job} (exit {code}) after {mins:.0f} min. The queue is stopped; the job stays at the top.')
            input('Fix the problem, then press Enter to try it again (or close this terminal). ')
            continue
        drop_first(job)
        with open(DONE, 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}  exit {code}  {mins:6.1f} min  {job}\n')
        banner(f'DONE {job} ({mins:.0f} min)')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nQueue stopped.')

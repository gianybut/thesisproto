"""Watch training runs and keep results/training_status.md up to date (the team reads it).

    python tools/watch_training.py                 # every 5 min until stopped (start it hidden:
                                                   #   tools/start_watch.ps1)
    python tools/watch_training.py --once          # write the status file once and exit
    python tools/watch_training.py --interval 120  # other period, seconds
    python tools/watch_training.py --console --interval 60   # live view in a terminal (VS Code task
                                                   #   "Watch training"); display only: no notifications,
                                                   #   no RAM actions, no status file (the hidden watcher
                                                   #   keeps doing those)

Looks at every run folder under runs/ that has a run_info.json (written by ml/train_run.py) and
was active in the last --recent-h hours. Per run: epoch / total, time elapsed, estimated time
left, latest train losses, local/foreign val P, R, mAP@50, AP@50 per class, best epoch, and
whether the training process is alive. System: GPU use / memory / temperature (nvidia-smi), RAM,
free disk.

Alerts (marked ALERT in the file, and a Windows notification once per alert): process died,
error or out-of-memory in the log, NaN/inf loss, no mAP@50 gain for 5 epochs, GPU > 85 C, RAM > 90%,
free disk < 10 GB, no new epoch for more than twice the usual epoch time.

RAM rule (team decision 2026-11-09): when RAM stays above 85% for two samples 30 s apart while a
run uses workers=6, the watcher stops that run and resumes it from last.pt with workers=4
(--no-auto-workers turns this off). Every action is written to runs/watch_actions.log.
"""

import argparse
import csv
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / 'runs'
STATUS = ROOT / 'results' / 'training_status.md'
STATE = RUNS / '.watch_state.json'
ACTIONS = RUNS / 'watch_actions.log'
CODES = ['D00', 'D10', 'D20', 'D40']
ERR = re.compile(r'Traceback|out of memory|OutOfMemoryError|CUDA error|RuntimeError|MemoryError|DataLoader worker .* exited',
                 re.I)

SCHEDULE = """**Check schedule for the team**
- Right after each run starts: confirm the first-epoch sanity check passed (ask Claude Code to "check").
- Every 1-2 hours while awake: open this file, or ask Claude Code to "check".
- Before going to bed on Tuesday: the final run is alive, has no alerts, and its ETA is before Wednesday 6 AM.
- First thing Wednesday morning: check it finished, then continue to Step 6.3.

**What to do on an alert** (never restart a run from scratch if last.pt exists; re-running its
start line resumes it)
| Alert | Action |
|---|---|
| Crash or out-of-memory | Resume from last.pt with a smaller batch: same start line plus `--batch 4` |
| NaN loss | Resume with `--set amp=False lr0=<half the current lr0>` |
| Overheating (GPU > 85 C) | Stop the run, check the PC's airflow (side panel, dust, room), resume |
| Low RAM | Close other apps; the watcher lowers workers to 4 by itself at 85%; else resume with `--workers 2` |
| Stuck (no new epoch) | Stop the run (Task Manager: python.exe running train_run.py) and resume from last.pt |
| No improvement for 5 epochs | Normal; early stopping is near. Nothing to do |
"""


def log_action(text):
    RUNS.mkdir(exist_ok=True)
    with open(ACTIONS, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S} {text}\n')


def notify(title, body):
    """Windows toast notification (Windows PowerShell 5.1, no extra modules)."""
    ps = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
        "$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        "$x = $t.GetElementsByTagName('text');"
        "$x.Item(0).AppendChild($t.CreateTextNode($env:WT_TITLE)) | Out-Null;"
        "$x.Item(1).AppendChild($t.CreateTextNode($env:WT_BODY)) | Out-Null;"
        "$n = [Windows.UI.Notifications.ToastNotification]::new($t);"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
        "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe').Show($n)")
    try:
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], env=dict(os.environ, WT_TITLE=title, WT_BODY=body),
                       capture_output=True, timeout=30)
    except Exception:
        pass


def gpu():
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
                              '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=15).stdout
        u, m, t, c = (int(x) for x in out.strip().split(','))
        return dict(util=u, mem=m, total=t, temp=c)
    except Exception:
        return None


def processes():
    out = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cl = p.info['cmdline'] or []
            if any('train_run.py' in c for c in cl):
                out.append((p, cl))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return out


def arg(cl, key):
    return cl[cl.index(key) + 1] if key in cl and cl.index(key) + 1 < len(cl) else None


def proc_for(run, procs):
    for p, cl in procs:
        prj, name = arg(cl, '--project'), arg(cl, '--name')
        if name == run.name and prj and (ROOT / prj).resolve() == run.parent.resolve():
            return p, cl
    return None, None


def read_epochs(run):
    p = run / 'epochs.csv'
    if not p.exists():
        return []
    with open(p, newline='') as f:
        return list(csv.DictReader(f))


def log_tail(run, nbytes=65536):
    p = run / 'train.log'
    if not p.exists():
        return ''
    with open(p, 'rb') as f:
        f.seek(max(0, p.stat().st_size - nbytes))
        text = f.read().decode('utf-8', 'replace')
    return text.split('===== ')[-1]   # only the latest session


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float('nan')


def relaunch(run, info, cl, workers):
    """Stop the run's process tree and resume it from last.pt with other workers."""
    p, _ = proc_for(run, processes())
    if p:
        for c in p.children(recursive=True) + [p]:
            try:
                c.kill()
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs([p], timeout=60)
    time.sleep(10)
    rest = cl[cl.index(next(c for c in cl if c.endswith('train_run.py'))) + 1:]
    if '--workers' in rest:
        rest[rest.index('--workers') + 1] = str(workers)
    else:
        rest += ['--workers', str(workers)]
    prj, name = arg(rest, '--project'), arg(rest, '--name')
    keep = []
    skip = False
    for x in rest:   # start_training.ps1 adds --project/--name itself
        if skip:
            skip = False
            continue
        if x in ('--project', '--name'):
            skip = True
            continue
        keep.append(x)
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                    str(ROOT / 'tools' / 'start_training.ps1'), '-Project', prj, '-Name', name] + keep,
                   capture_output=True, timeout=60)
    how = 'resumed from last.pt' if (run / 'weights' / 'last.pt').exists() else 'restarted (no epoch finished yet)'
    log_action(f'{run.relative_to(ROOT)}: RAM above 85%: stopped and {how} with workers={workers}')


def run_report(run, procs, sysinfo, now):
    info = json.loads((run / 'run_info.json').read_text())
    eps = read_epochs(run)
    p, cl = proc_for(run, procs)
    alive = p is not None
    finished = bool(info.get('finished'))
    alerts = []
    total = int(info.get('epochs', 0))
    done = int(eps[-1]['epoch']) if eps else 0
    last = eps[-1] if eps else {}

    # Epoch durations within sessions (the first epoch of a session includes start-up).
    durs = []
    for a_, b_ in zip(eps, eps[1:]):
        d = (datetime.fromisoformat(b_['time']) - datetime.fromisoformat(a_['time'])).total_seconds()
        if 0 < d < 6 * 3600 and int(b_['epoch']) == int(a_['epoch']) + 1:
            durs.append(d)
    usual = statistics.median(durs) if durs else None
    sess = info.get('sessions', [])
    # Wall time of every session: a stopped session (no 'end') ran until the next one started.
    elapsed = 0.0
    for i, s in enumerate(sess):
        start = datetime.fromisoformat(s['start'])
        stop = (datetime.fromisoformat(s['end']) if 'end' in s else
                datetime.fromisoformat(sess[i + 1]['start']) if i + 1 < len(sess) else now)
        elapsed += max(0.0, (stop - start).total_seconds())
    mAPs = [num(e['mAP50']) for e in eps]
    best_i = max(range(len(mAPs)), key=lambda i: (mAPs[i] if mAPs[i] == mAPs[i] else -1)) if eps else None
    patience = int(info.get('patience', 0) or 0)
    remaining = max(0, total - done)
    earliest = remaining
    if best_i is not None and patience:   # early stopping could end it sooner, if mAP stops improving
        earliest = min(remaining, max(0, patience - (done - (best_i + 1))))
    eta = timedelta(seconds=int(usual * remaining)) if usual and not finished else None
    eta_early = timedelta(seconds=int(usual * earliest)) if usual and not finished and earliest < remaining else None

    tail = log_tail(run)
    if not finished and not alive:
        alerts.append('process has died (not finished)' + (' after an error in the log' if ERR.search(tail) else ''))
    elif ERR.search(tail) and not finished:
        alerts.append('error text in the log: ' + ERR.search(tail).group(0))
    for k in ('box_loss', 'cls_loss', 'dfl_loss'):
        v = num(last.get(k))
        if eps and (v != v or abs(v) == float('inf')):
            alerts.append(f'{k} is NaN/inf')
    if best_i is not None and done - (best_i + 1) >= 5 and not finished:
        alerts.append(f'val mAP@50 has not improved for {done - (best_i + 1)} epochs (early stopping approaching)')
    if alive and not finished:
        last_t = datetime.fromisoformat(eps[-1]['time']) if eps else datetime.fromisoformat(sess[-1]['start'])
        since = (now - last_t).total_seconds()
        if usual and since > 2 * usual:
            alerts.append(f'no new epoch for {since / 60:.0f} min (usual {usual / 60:.0f} min): stuck?')
        elif not usual and since > 3 * 3600:
            alerts.append(f'no epoch finished in {since / 3600:.1f} h: stuck?')

    lines = [f'### {run.relative_to(RUNS).as_posix()}' + ('  **ALERT**' if alerts else ''), '',
             f'- State: ' + ('finished ' + info['finished'] if finished else
                              ('running (process ' + str(p.pid) + f', workers {arg(cl, "--workers") or 6})') if alive
                              else 'NOT RUNNING'),
             f'- Epoch {done} / {total}; elapsed {timedelta(seconds=int(elapsed))}'
             + (f'; usual epoch {usual / 60:.1f} min; time left to the last epoch {eta} (finish about '
                f'{(now + eta):%a %H:%M})' if eta else '')
             + (f'; earliest possible early stop in {eta_early}' if eta_early else ''),
             f'- Settings: imgsz {info.get("imgsz")}, batch {info.get("batch")}, patience {patience}, data {info.get("data")}']
    if eps:
        lines.append(f'- Latest train losses: box {num(last["box_loss"]):.4f}, cls {num(last["cls_loss"]):.4f}, '
                     f'dfl {num(last["dfl_loss"]):.4f}')
        lines.append(f'- Latest val: P {num(last["precision"]):.3f}, R {num(last["recall"]):.3f}, '
                     f'mAP@50 {num(last["mAP50"]):.3f}; AP@50 ' + ', '.join(
                         f'{c} {num(last.get("AP50_" + c)):.3f}' for c in CODES))
        b = eps[best_i]
        lines.append(f'- Best so far: epoch {b["epoch"]}, mAP@50 {num(b["mAP50"]):.3f}; AP@50 ' + ', '.join(
            f'{c} {num(b.get("AP50_" + c)):.3f}' for c in CODES))
    for al in alerts:
        lines.append(f'- **ALERT: {al}**')
    return lines, alerts, info, cl, alive


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--interval', type=int, default=300)
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--recent-h', type=float, default=48)
    ap.add_argument('--no-auto-workers', action='store_true')
    ap.add_argument('--console', action='store_true', help='live view in this terminal, display only')
    a = ap.parse_args()
    state = json.loads(STATE.read_text()) if STATE.exists() else {'notified': []}
    ram_high = {}
    next_status = 0
    while True:
        now = datetime.now()
        procs = processes()
        vm = psutil.virtual_memory()
        runs = [p.parent for p in RUNS.glob('**/run_info.json')
                if (time.time() - max(p.stat().st_mtime, (p.parent / 'train.log').stat().st_mtime
                                      if (p.parent / 'train.log').exists() else 0)) < a.recent_h * 3600]
        # RAM rule, checked every 30 s.
        for run in runs:
            info = json.loads((run / 'run_info.json').read_text())
            p, cl = proc_for(run, procs)
            w = (arg(cl, '--workers') or '6') if p else None
            # Tier 1 (team rule): workers 6 -> 4 above 85%. Tier 2 (task's low-RAM action): 4 -> 2 above 90%.
            target = 4 if w == '6' and vm.percent > 85 else 2 if w == '4' and vm.percent > 90 else None
            if p and not a.no_auto_workers and not a.console and target:
                ram_high[run] = ram_high.get(run, 0) + 1
                if ram_high[run] >= 2:
                    relaunch(run, info, cl, target)
                    notify(f'Training: RAM {vm.percent:.0f}%', f'{run.name} resumed with workers={target}')
                    ram_high[run] = 0
            else:
                ram_high[run] = 0
        if time.time() >= next_status or a.once:
            next_status = time.time() + a.interval
            g = gpu()
            free_gb = shutil.disk_usage(ROOT).free / 2 ** 30
            sys_alerts = []
            if g and g['temp'] > 85:
                sys_alerts.append(f'GPU at {g["temp"]} C')
            if vm.percent > 90:
                sys_alerts.append(f'RAM {vm.percent:.0f}% used')
            if free_gb < 10:
                sys_alerts.append(f'only {free_gb:.1f} GB free on disk')
            body, all_alerts = [], list(sys_alerts)
            for run in sorted(runs, key=lambda r: -(r / 'run_info.json').stat().st_mtime):
                lines, alerts, *_ = run_report(run, procs, g, now)
                body += lines + ['']
                all_alerts += [f'{run.name}: {x}' for x in alerts]
            head = (f'# Training status  ({"**ALERT**" if all_alerts else "OK"})\n\nUpdated {now:%a %Y-%m-%d %H:%M} by '
                    f'tools/watch_training.py (every {a.interval // 60} min).\n\n')
            sysl = ('## This PC\n\n'
                    + (f'- GPU: {g["util"]}% busy, {g["mem"]} / {g["total"]} MiB memory, {g["temp"]} C\n' if g else
                       '- GPU: nvidia-smi did not answer\n')
                    + f'- RAM: {vm.percent:.0f}% used ({vm.used / 2 ** 30:.1f} / {vm.total / 2 ** 30:.1f} GB)\n'
                    + f'- Free disk: {free_gb:.0f} GB\n'
                    + ''.join(f'- **ALERT: {x}**\n' for x in sys_alerts))
            acts = ACTIONS.read_text(encoding='utf-8').splitlines()[-5:] if ACTIONS.exists() else []
            if a.console:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f'TRAINING LIVE VIEW  {now:%a %H:%M:%S}  (refreshes every {a.interval} s; Ctrl+C closes this view '
                      f'only)  {"ALERTS: " + "; ".join(all_alerts) if all_alerts else "no alerts"}\n')
                print(sysl.replace('## This PC', 'THIS PC').replace('**', ''))
                print('\n'.join(body).replace('**', '').replace('### ', '>>> ') if body else 'No recent runs.')
                q = RUNS / 'queue.txt'
                if q.exists():
                    nxt = [l for l in q.read_text(encoding='utf-8-sig').splitlines() if l.strip() and not l.startswith('#')]
                    print('QUEUE (runs/queue.txt): ' + (' | '.join(nxt) if nxt else 'empty'))
                sys.stdout.flush()
                time.sleep(a.interval)
                continue
            text = (head + SCHEDULE + '\n' + sysl + '\n## Runs\n\n' + ('\n'.join(body) if body else 'No recent runs.\n')
                    + ('\n## Recent watcher actions\n\n' + '\n'.join(f'- {x}' for x in acts) + '\n' if acts else ''))
            STATUS.parent.mkdir(exist_ok=True)
            tmp = STATUS.with_suffix('.tmp')
            tmp.write_text(text, encoding='utf-8')
            tmp.replace(STATUS)
            for al in all_alerts:
                if al not in state['notified']:
                    notify('Training ALERT', al)
                    state['notified'].append(al)
            RUNS.mkdir(exist_ok=True)
            STATE.write_text(json.dumps(state))
        if a.once:
            return 0
        time.sleep(30)


if __name__ == '__main__':
    sys.exit(main())

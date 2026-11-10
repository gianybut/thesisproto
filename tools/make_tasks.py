"""Write .vscode/tasks.json: one "Train: <run>" task per training run, plus the queue, the live
watcher, TensorBoard and "Follow log" tasks. Run again after adding runs.

    python tools/make_tasks.py

Start a task: Terminal > Run Task... > pick it (or Ctrl+Shift+P > "Tasks: Run Task"). Each task opens
its own terminal tab named after it (the Terminal panel's list on the right shows the tabs).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'ml' / 'local'))
from runs_v2 import RUNS  # noqa: E402

PY = '${workspaceFolder}\\.venv\\Scripts\\python.exe'
ENV = {'PYTHONUTF8': '1'}


def task(label, args, detail, command=PY, kind='process', panel='dedicated'):
    return {'label': label, 'type': kind, 'command': command, 'args': args, 'detail': detail,
            'options': {'cwd': '${workspaceFolder}', 'env': ENV},
            'presentation': {'reveal': 'always', 'panel': panel, 'focus': False, 'clear': False, 'showReuseMessage': False},
            'problemMatcher': []}


def follow(label, log, detail):
    t = task(label, ['-NoProfile', '-Command', f"Get-Content '{log}' -Wait -Tail 40"], detail,
             command='powershell.exe')
    return t


def main():
    tasks = [
        task('Train: queue', ['-u', 'tools\\train_queue.py'],
             'Runs runs/queue.txt one job at a time in this terminal (live progress bars). Claude Code adds jobs.'),
        task('Watch training', ['-u', 'tools\\watch_training.py', '--console', '--interval', '60', '--recent-h', '12'],
             'Live view, every minute: epoch, losses, val mAP@50 per class, GPU memory/temperature, RAM, ETA, alerts.'),
        task('TensorBoard', ['-m', 'tensorboard.main', '--logdir', 'runs', '--port', '6006'],
             'Then Ctrl+Shift+P > "Simple Browser: Show" > http://localhost:6006'),
        follow('Follow log: Bv2 (background run)', 'runs\\v2\\Bv2\\train.log',
               'B v2 was started hidden before the tasks existed; this follows its log live.'),
    ]
    for name, spec in RUNS.items():
        if spec.get('cancelled'):
            continue
        tasks.append(task(f'Train: {name}', ['-u', 'ml\\local\\runs_v2.py', '--run', name],
                          f'{spec["note"]}. Starts or resumes (from last.pt) in this terminal; also writes runs/v2/{name}/train.log.'))
    out = ROOT / '.vscode' / 'tasks.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({'version': '2.0.0', 'tasks': tasks}, indent=2) + '\n', encoding='utf-8')
    print(f'{out.relative_to(ROOT)}: ' + ', '.join(t['label'] for t in tasks))


if __name__ == '__main__':
    main()

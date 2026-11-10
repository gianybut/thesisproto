"""Run the training plan of 2026-11-10 unattended (start hidden with tools/start_pipeline.ps1).

    python tools/pipeline_v2.py [--freeze-cutoff "2026-11-10 20:00"] [--hard-stop "2026-11-10 21:30"]

Stages (state kept in runs/v2/pipeline_state.json, so a restart continues where it was):
  wait_reviews  until every batch-2 VAL frame and every "train" batch frame is reviewed (the test
                review and the self-check are not waited for) -> build dataset -> start B v1
  Bv1           when B v1 finishes -> Chapter V table -> AL selection (notification) -> start A
  A_and_AL      when A has finished AND every AL frame is reviewed -> rebuild dataset -> start B v2
  Bv2           -> table -> start B v2 no replay
  noreplay      -> table -> start B v2 freeze 10 only if now <= --freeze-cutoff, else done
  freeze10      -> table -> done
A run whose process dies before finishing is resumed from last.pt (at most twice). At --hard-stop
any run still training is stopped (its best.pt stays as a candidate), no run is started after it,
and the table is made one last time. The final choice, calibration, test and deployment are done
by hand afterwards. Log: runs/v2/pipeline.log; status: results/pipeline_status.md.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'ml' / 'local'))
from watch_training import notify  # noqa: E402

PY = sys.executable
STATE = ROOT / 'runs' / 'v2' / 'pipeline_state.json'
LOG = ROOT / 'runs' / 'v2' / 'pipeline.log'
STATUS = ROOT / 'results' / 'pipeline_status.md'
DATA = ROOT / 'data' / 'local'


def log(msg, alert=False):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f'{datetime.now():%Y-%m-%d %H:%M:%S} {msg}'
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    print(line, flush=True)
    if alert:
        notify('Training pipeline', msg)


def save(st):
    STATE.write_text(json.dumps(st, indent=1))
    lines = ['# Training pipeline status', '', f'Updated {datetime.now():%a %H:%M}. Stage: **{st["stage"]}**', '',
             '| Time | Event |', '|---|---|'] + [f'| {t} | {e} |' for t, e in st['events'][-30:]]
    STATUS.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def event(st, msg, alert=False):
    st['events'].append((datetime.now().strftime('%a %H:%M'), msg))
    save(st)
    log(msg, alert)


def run(cmd, timeout=3600):
    r = subprocess.run([PY, '-u'] + cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                       env={**__import__('os').environ, 'PYTHONUTF8': '1'})
    tail = (r.stdout + r.stderr).strip().splitlines()[-6:]
    log(f'{" ".join(cmd)} -> exit {r.returncode}: ' + ' | '.join(tail))
    return r.returncode == 0


def review_counts():
    import csv
    with open(DATA / 'review_frames.csv', newline='', encoding='utf-8') as f:
        frames = list(csv.DictReader(f))
    with open(DATA / 'review_log.csv', newline='', encoding='utf-8') as f:
        rev = {r['frame']: r['reviewed'] == 'yes' for r in csv.DictReader(f)}

    def done(pred):
        x = [r for r in frames if pred(r)]
        return sum(rev.get(r['frame'], False) for r in x), len(x)
    return dict(val2=done(lambda r: r.get('batch') == '2' and r['split'] == 'val'),
                train=done(lambda r: r.get('batch') == 'train'), al=done(lambda r: r.get('batch') == 'AL'))


def proc(name):
    for p in psutil.process_iter(['cmdline']):
        try:
            cl = p.info['cmdline'] or []
            if any('train_run.py' in c for c in cl) and '--name' in cl and cl[cl.index('--name') + 1] == name:
                return p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None


def finished(name):
    p = ROOT / 'runs' / 'v2' / name / 'run_info.json'
    return p.exists() and bool(json.loads(p.read_text()).get('finished'))


def start(st, name):
    if run(['ml/local/runs_v2.py', '--start', name], timeout=120):
        st.setdefault('starts', {})[name] = st.get('starts', {}).get(name, 0) + 1
        event(st, f'started {name}' + (' (resumed)' if st['starts'][name] > 1 else ''), alert=True)
        time.sleep(60)
        return True
    event(st, f'could not start {name}', alert=True)
    return False


def kill(name):
    p = proc(name)
    if p:
        for c in p.children(recursive=True) + [p]:
            try:
                c.kill()
            except psutil.NoSuchProcess:
                pass


def wait_run(st, name, hard_stop):
    """'done' when finished, 'stopped' at the hard stop, 'failed' if it cannot be resumed."""
    while True:
        if finished(name):
            event(st, f'{name} finished')
            return 'done'
        if datetime.now() >= hard_stop:
            kill(name)
            time.sleep(15)
            event(st, f'hard stop: {name} stopped; its best.pt is kept as a candidate', alert=True)
            return 'stopped'
        if proc(name) is None:
            time.sleep(30)
            if finished(name):
                continue
            if proc(name) is None:
                if st.get('starts', {}).get(name, 0) >= 3:
                    event(st, f'{name} died again; not resumed (needs a look)', alert=True)
                    return 'failed'
                event(st, f'{name} died; resuming from last.pt', alert=True)
                start(st, name)
        time.sleep(60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--freeze-cutoff', default='2026-11-10 20:00')
    ap.add_argument('--hard-stop', default='2026-11-10 21:30')
    a = ap.parse_args()
    cutoff = datetime.strptime(a.freeze_cutoff, '%Y-%m-%d %H:%M')
    hard = datetime.strptime(a.hard_stop, '%Y-%m-%d %H:%M')
    st = json.loads(STATE.read_text()) if STATE.exists() else {'stage': 'wait_reviews', 'events': []}
    if not st['events']:
        event(st, f'pipeline started; freeze-10 cutoff {cutoff:%H:%M}, hard stop {hard:%H:%M}')

    def table():
        run(['ml/local/val_table.py'], timeout=1800)

    while st['stage'] != 'done':
        now = datetime.now()
        if now >= hard and st['stage'] in ('wait_reviews', 'A_and_AL'):
            if proc('A'):
                kill('A')
                time.sleep(15)
                event(st, 'hard stop: A stopped; its best.pt is kept as a candidate')
            event(st, f'hard stop reached in stage {st["stage"]}; no further runs', alert=True)
            table()
            st['stage'] = 'done'
            break
        stage = st['stage']
        if stage == 'wait_reviews':
            c = review_counts()
            if c['val2'][0] == c['val2'][1] and c['train'][0] == c['train'][1] and c['train'][1] > 0:
                event(st, f'reviews done (batch-2 val {c["val2"][1]}, train batch {c["train"][1]}); building dataset')
                if run(['ml/local/build_local_yolo.py']) and start(st, 'Bv1'):
                    st['stage'] = 'Bv1'
                    save(st)
                else:
                    event(st, 'dataset build or B v1 start failed; retrying in 10 min', alert=True)
                    time.sleep(600)
            else:
                time.sleep(60)
        elif stage == 'Bv1':
            r = wait_run(st, 'Bv1', hard)
            table()
            if r == 'stopped':
                st['stage'] = 'done'
                break
            if run(['ml/local/select_review_al.py'], timeout=1800):
                c = review_counts()
                event(st, f'AL batch ready: {c["al"][1]} train frames to review (view "To review")', alert=True)
            else:
                event(st, 'AL selection failed', alert=True)
            start(st, 'A')
            st['stage'] = 'A_and_AL'
            save(st)
        elif stage == 'A_and_AL':
            a_done = finished('A') or proc('A') is None
            if a_done and not st.get('A_tabled'):
                if not finished('A'):
                    event(st, 'A is not running and did not finish; going on without resuming it', alert=True)
                table()
                st['A_tabled'] = True
                save(st)
            c = review_counts()
            if a_done and c['al'][1] and c['al'][0] == c['al'][1]:
                event(st, f'AL review done ({c["al"][1]} frames); rebuilding dataset')
                if run(['ml/local/build_local_yolo.py']) and start(st, 'Bv2'):
                    st['stage'] = 'Bv2'
                    save(st)
                else:
                    event(st, 'rebuild or B v2 start failed; retrying in 10 min', alert=True)
                    time.sleep(600)
            else:
                if datetime.now() >= hard:
                    continue
                time.sleep(60)
        elif stage in ('Bv2', 'noreplay', 'freeze10'):
            name = {'Bv2': 'Bv2', 'noreplay': 'Bv2_noreplay', 'freeze10': 'Bv2_freeze10'}[stage]
            r = wait_run(st, name, hard)
            table()
            if r == 'stopped' or stage == 'freeze10':
                st['stage'] = 'done'
            elif stage == 'Bv2':
                st['stage'] = 'noreplay' if start(st, 'Bv2_noreplay') else 'done'
            elif datetime.now() <= cutoff:
                st['stage'] = 'freeze10' if start(st, 'Bv2_freeze10') else 'done'
            else:
                event(st, f'freeze 10 skipped: it could not start by {cutoff:%H:%M}', alert=True)
                st['stage'] = 'done'
            save(st)
    event(st, 'pipeline done: all training finished or stopped; ready for the final choice', alert=True)


if __name__ == '__main__':
    main()

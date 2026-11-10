"""Queue step before runs 2 and 3 (team decision 2026-11-10 13:03): if every AL2 frame is reviewed,
rebuild the near-zone dataset so the next run includes AL2; otherwise leave it as it is (built at
12:20, without AL2). Always exits 0. Which runs had AL2 is read from each run's own copy of its
training list (val_table_nz.py), and every decision is appended to results/al2_inclusion.md.

    python ml/local/al2_gate.py --before S5_v8m_1920
"""

import argparse
import subprocess
import sys
from datetime import datetime

from common import OUT, ROOT, read_csv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--before', default='next run')
    a = ap.parse_args()
    al2 = [r['frame'] for r in read_csv(OUT / 'review_frames.csv') if r.get('batch') == 'AL2']
    log = {r['frame']: r for r in read_csv(OUT / 'review_log.csv')}
    done = sum(log.get(f, {}).get('reviewed') == 'yes' for f in al2)
    note = ROOT / 'results' / 'al2_inclusion.md'
    if not note.exists():
        note.write_text('# AL2 in the step-5 runs\n\nRun 1 (S5_v8m_1280) started before any AL2 frame was reviewed.\n\n',
                        encoding='utf-8')
    if al2 and done == len(al2):
        print(f'AL2 fully reviewed ({done}/{len(al2)}): rebuilding the near-zone dataset before {a.before}.', flush=True)
        code = subprocess.run([sys.executable, '-u', str(ROOT / 'ml' / 'local' / 'build_local_yolo.py'), '--near-zone'],
                              cwd=ROOT).returncode
        msg = f'rebuilt with AL2 ({done} frames) before {a.before}' + ('' if code == 0 else f' - REBUILD FAILED (exit {code})')
    else:
        msg = f'AL2 {done}/{len(al2)} reviewed: not complete, {a.before} uses the dataset without AL2'
        print(msg, flush=True)
    with open(note, 'a', encoding='utf-8') as f:
        f.write(f'- {datetime.now():%H:%M}: {msg}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

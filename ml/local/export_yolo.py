"""Export the annotation site's labels into the near-zone YOLO dataset (deploy_annotation_site.md §3.9).

    python ml/local/export_yolo.py              # any time, also while people are labelling

1. Snapshot labels.db with the SQLite backup API to backups/labels_<timestamp>_export.db (this file is
   the data snapshot a training run is tied to; logged in results/export_log.md).
2. Rebuild data/local/yolo_nz from the 1,066 reviewed frames with the unchanged
   build_local_yolo.py --near-zone (near-zone filter, test set exactly as before).
3. Add every frame with status 'labeled' in the snapshot: image from data/local/frames_nz, boxes as
   stored (already normalised to the near-zone crop; clipped to it, a box whose centre falls outside
   is dropped). Zero boxes = confirmed negative (empty label file). Skipped frames are left out.
   Frames come only from the train/val pool, which already excludes test groups and val frames
   within 50 m of a train frame (splits.csv dropped_by_location); both are re-checked here.
   A frame that is also reviewed in the old tool keeps the reviewed label.
4. Rewrite the lists: local_train.txt (A), local_train_x3.txt (B_noreplay: frames with D10/D20/D40 x3),
   val.txt; test.txt is not touched. B_train.txt / B.yaml (RDD2022 replay) are deleted: no replay.
5. Write the new counts to results/local_datasets_nz_export.md and run check_counts.py.
   results/local_datasets_nz.md is protected (§0.5): build_local_yolo.py rewrites it, so it is restored
   byte for byte afterwards.
"""

import csv
import os
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'local'
Y = DATA / 'yolo_nz'
DB = Path(os.environ.get('LABELS_DB') or DATA / 'annotate' / 'labels.db')
CODES = ['D00', 'D10', 'D20', 'D40']
TEST_GROUPS = {'G05', 'G13', 'G15'}
REPEAT = 3
PY = sys.executable


def read_csv(p):
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def link(src, dst):
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main():
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    (ROOT / 'backups').mkdir(exist_ok=True)
    snap = ROOT / 'backups' / f'labels_{stamp}_export.db'
    src = sqlite3.connect(DB)
    dst = sqlite3.connect(snap)
    with dst:
        src.backup(dst)
    src.close()
    print('snapshot', snap)

    protected = ROOT / 'results' / 'local_datasets_nz.md'
    keep = protected.read_bytes()
    r = subprocess.run([PY, str(ROOT / 'ml/local/build_local_yolo.py'), '--near-zone'], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode:
        protected.write_bytes(keep)
        sys.exit('build_local_yolo.py failed:\n' + r.stdout + r.stderr)
    base_md = protected.read_text(encoding='utf-8')
    protected.write_bytes(keep)

    splits = {x['frame']: x for x in read_csv(DATA / 'splits.csv')}
    reviewed = {x['frame'] for x in read_csv(DATA / 'review_log.csv') if x['reviewed'] == 'yes'}
    db = dst
    db.row_factory = sqlite3.Row
    added = {'train': [], 'val': []}
    counts = {s: Counter() for s in added}
    refused = Counter()
    for f in db.execute("SELECT * FROM frames WHERE status='labeled' ORDER BY frame_id"):
        fid, sp = f['frame_id'], splits.get(f['frame_id'])
        if fid in reviewed:
            refused['already reviewed'] += 1
            continue
        if not sp or sp['split'] not in added or sp['route_group'] in TEST_GROUPS or sp['dropped_by_location'] != '0':
            refused['not train/val pool'] += 1
            continue
        split = sp['split']
        lines = []
        for b in db.execute('SELECT * FROM boxes WHERE frame_id=? AND source=?', (fid, 'human')):
            if not (0 <= b['cx'] <= 1 and 0 <= b['cy'] <= 1):
                refused['box centre outside crop'] += 1
                continue
            x1, x2 = max(0.0, b['cx'] - b['w'] / 2), min(1.0, b['cx'] + b['w'] / 2)
            y1, y2 = max(0.0, b['cy'] - b['h'] / 2), min(1.0, b['cy'] + b['h'] / 2)
            lines.append(f'{b["class_id"]} {(x1 + x2) / 2:.6f} {(y1 + y2) / 2:.6f} {x2 - x1:.6f} {y2 - y1:.6f}')
            counts[split][CODES[b['class_id']]] += 1
        link(DATA / 'frames_nz' / fid, Y / 'images' / split / fid)
        (Y / 'labels' / split / f'{fid[:-4]}.txt').write_text(''.join(l + '\n' for l in lines))
        counts[split]['frames'] += 1
        counts[split]['no damage'] += not lines
        added[split].append(fid)
    db.close()

    def p(split, fid):
        return (Y / 'images' / split / fid).as_posix()

    def rare(split, fid):
        return any(l.split()[0] in ('1', '2', '3') for l in (Y / 'labels' / split / f'{fid[:-4]}.txt').read_text().splitlines())

    a_list = [l for l in (Y / 'local_train.txt').read_text().splitlines() if l.strip()] + [p('train', f) for f in added['train']]
    x3 = a_list + [x for x in a_list for _ in range(REPEAT - 1) if rare('train', Path(x).name)]
    val = [l for l in (Y / 'val.txt').read_text().splitlines() if l.strip()] + [p('val', f) for f in added['val']]
    (Y / 'local_train.txt').write_text('\n'.join(a_list) + '\n')
    (Y / 'local_train_x3.txt').write_text('\n'.join(x3) + '\n')
    (Y / 'val.txt').write_text('\n'.join(val) + '\n')
    for name in ('B_train.txt', 'B.yaml', 'replay.txt'):
        (Y / name).unlink(missing_ok=True)
    for c in ('train.cache', 'val.cache'):
        (Y / 'labels' / c).unlink(missing_ok=True)

    # counts table: old reviewed + new
    old = {}
    for line in base_md.splitlines():
        q = [x.strip() for x in line.strip('|').split('|')]
        if len(q) == 7 and q[0] in ('train', 'val', 'test') and q[0] not in old and q[1].isdigit():
            old[q[0]] = list(map(int, q[1:]))
    md = ['# Local YOLO datasets (human labels only), near zone', '',
          f'Export {stamp}: 1,066 reviewed frames + annotation-site frames from `{snap.relative_to(ROOT).as_posix()}`.', '',
          '| Split | Frames | No damage | D00 | D10 | D20 | D40 |', '|---|---|---|---|---|---|---|']
    for s in ('train', 'val', 'test'):
        o = old[s]
        n = counts.get(s, Counter())
        tot = [o[0] + n['frames'], o[1] + n['no damage']] + [o[2 + i] + n[c] for i, c in enumerate(CODES)]
        md.append(f'| {s} | ' + ' | '.join(map(str, tot)) + ' |')
    md += ['', '| Of which new from the annotation site | Frames | No damage | D00 | D10 | D20 | D40 |', '|---|---|---|---|---|---|---|']
    for s in ('train', 'val'):
        n = counts[s]
        md.append(f'| {s} | {n["frames"]} | {n["no damage"]} | ' + ' | '.join(str(n[c]) for c in CODES) + ' |')
    md += ['', '| Training list | Images per epoch |', '|---|---|',
           f'| local_train.txt (A) | {len(a_list)} |', f'| local_train_x3.txt (B_noreplay, D10/D20/D40 x{REPEAT}) | {len(x3)} |',
           '', 'No RDD2022 replay (decision 2026-11-10): B.yaml / B_train.txt are not written. Test set unchanged.']
    if refused:
        md.append('Not exported: ' + ', '.join(f'{k} {v}' for k, v in refused.items()) + '.')
    md.append('')
    md.append('Reviewed-only base (build_local_yolo.py) before the export:')
    md += ['> ' + l for l in base_md.splitlines() if l.strip()]
    (ROOT / 'results' / 'local_datasets_nz_export.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    log = ROOT / 'results' / 'export_log.md'
    if not log.exists():
        log.write_text('# Exports (data snapshots for training runs)\n\n| Time | Snapshot | New train | New val |\n|---|---|---|---|\n')
    with open(log, 'a', encoding='utf-8') as fh:
        fh.write(f'| {stamp} | {snap.name} | {counts["train"]["frames"]} | {counts["val"]["frames"]} |\n')
    print('\n'.join(md[:12]))
    subprocess.run([PY, str(ROOT / 'ml/local/check_counts.py'), '--no-compare'], cwd=ROOT)


if __name__ == '__main__':
    main()

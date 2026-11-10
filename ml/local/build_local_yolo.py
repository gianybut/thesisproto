"""Build the YOLO datasets for the training runs from the REVIEWED local labels (strategy of
2026-11-10, replacing Steps 4-6).

    python ml/local/build_local_yolo.py            # for training: every val frame must be reviewed
    python ml/local/build_local_yolo.py --final    # for the test evaluation: every test frame too
    python ml/local/build_local_yolo.py --near-zone [--final]   # near-zone crops -> data/local/yolo_nz

--near-zone (team decision 2026-11-10 12:05): images from data/local/frames_nz (near_zone.py --apply)
and the reviewed boxes moved into those crops (y + old crop top - new crop top, clipped; a box whose
centre falls outside the new crop is dropped and counted). Frames with D10, D20 or D40 are repeated
x3 (new plan of 12:00). Writes data/local/yolo_nz (same lists and yamls) and results/local_datasets_nz.md.

Only human-reviewed frames are used (no pseudo-labels): val frames must all be accepted in the review
tool (review_log.csv reviewed = yes); train frames are the reviewed "train" and "AL" batch frames;
test frames are those reviewed so far, and with --final all of them must be (training never reads
test, so training can start before the test review and the self-check are finished).

data/local/yolo/images/<split>/<frame>.jpg (hard links to data/local/frames) and
labels/<split>/<frame>.txt (from the reviewed boxes). Lists and data files in data/local/yolo/:
  A.yaml          local train                          -> local val
  B.yaml          local train, D10/D20 frames x3, + 600 random six-country RDD2022 train images (replay)
  B_noreplay.yaml local train, D10/D20 frames x3
  val.yaml        local val only (scoring every run, including the teacher)
  test.yaml       local test (Wednesday, once)
The replay sample is fixed (seed 42) so B v1 and B v2 see the same foreign images.
"""

import argparse
import json
import os
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

from common import OUT, ROOT, read_csv

CODES = ['D00', 'D10', 'D20', 'D40']
Y = OUT / 'yolo'
RDD_LISTS = ROOT / 'data' / 'rdd2022' / 'lists'
COUNTRIES = ['Japan', 'India', 'Czech', 'Norway', 'United_States', 'China_MotorBike']


def link(src, dst):
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--final', action='store_true', help='require every test frame to be reviewed')
    ap.add_argument('--replay-n', type=int, default=600)
    ap.add_argument('--repeat', type=int, default=3)
    ap.add_argument('--near-zone', action='store_true')
    a = ap.parse_args()
    global Y
    rare_cls = ('1', '2', '3') if a.near_zone else ('1', '2')
    if a.near_zone:
        Y = OUT / 'yolo_nz'
        nzb = {r['recording']: r for r in read_csv(OUT / 'near_zone_bands.csv')}
        man = {r['frame']: r for r in read_csv(OUT / 'manifest.csv')}
        dropped = Counter()
    sel = read_csv(OUT / 'review_frames.csv')
    log = {r['frame']: r for r in read_csv(OUT / 'review_log.csv')}
    problems = []
    use = {'train': [], 'val': [], 'test': []}
    for r in sel:
        lg = log.get(r['frame'], {})
        ok = lg.get('reviewed') == 'yes'
        if not ok and (r['split'] == 'val' or (r['split'] == 'test' and a.final)):
            problems.append(f'{r["frame"]} ({r["split"]}, batch {r.get("batch", "1")}) not reviewed')
        if ok:
            use[r['split']].append(r['frame'])
    if problems:
        sys.exit(f'{len(problems)} frames not ready, e.g.:\n  ' + '\n  '.join(problems[:8]))

    shutil.rmtree(Y, ignore_errors=True)
    counts = {}
    for split, frames in use.items():
        (Y / 'images' / split).mkdir(parents=True)
        (Y / 'labels' / split).mkdir(parents=True)
        c = Counter()
        for f in frames:
            s = json.loads((OUT / 'reviewed' / 'state' / f'{f[:-4]}.json').read_text(encoding='utf-8'))
            w, h = s['width'], s['height']
            if a.near_zone:
                link(OUT / 'frames_nz' / f, Y / 'images' / split / f)
                b = nzb[man[f]['recording']]
                shift = int(man[f]['band_top_px']) - int(b['nz_top_px'])
                h = int(b['nz_bottom_px']) - int(b['nz_top_px'])
                kept = []
                for bx in s['boxes']:
                    y1, y2 = bx['y1'] + shift, bx['y2'] + shift
                    if not 0 <= (y1 + y2) / 2 <= h:
                        dropped[(split, bx['cls'])] += 1
                        continue
                    kept.append(dict(bx, y1=max(0.0, y1), y2=min(float(h), y2)))
                s = dict(s, boxes=kept, height=h)
            else:
                link(OUT / 'frames' / f, Y / 'images' / split / f)
            lines = [f'{CODES.index(b["cls"])} {(b["x1"] + b["x2"]) / 2 / w:.6f} {(b["y1"] + b["y2"]) / 2 / h:.6f} '
                     f'{(b["x2"] - b["x1"]) / w:.6f} {(b["y2"] - b["y1"]) / h:.6f}' for b in s['boxes']]
            (Y / 'labels' / split / f'{f[:-4]}.txt').write_text(''.join(l + '\n' for l in lines))
            c.update(b['cls'] for b in s['boxes'])
            c['frames'] += 1
            c['no damage'] += not s['boxes']
        counts[split] = c

    def paths(split, frames):
        return [(Y / 'images' / split / f).as_posix() for f in frames]

    rare = [f for f in use['train'] if any(l.split()[0] in rare_cls for l in
                                          (Y / 'labels' / 'train' / f'{f[:-4]}.txt').read_text().splitlines())]
    local = paths('train', use['train'])
    local_x3 = local + paths('train', rare) * (a.repeat - 1)
    rng = random.Random(42)
    rdd_train = [l for c in COUNTRIES for l in (RDD_LISTS / f'{c}_train.txt').read_text().splitlines() if l.strip()]
    replay = rng.sample(sorted(rdd_train), a.replay_n)
    lists = {'local_train.txt': local, 'local_train_x3.txt': local_x3, 'replay.txt': replay,
             'B_train.txt': local_x3 + replay,
             'val.txt': paths('val', use['val']), 'test.txt': paths('test', use['test'])}
    for name, items in lists.items():
        (Y / name).write_text('\n'.join(items) + '\n')
    names = ''.join(f'  {i}: {c}\n' for i, c in enumerate(CODES))
    for yname, train, val in (('A', 'local_train.txt', 'val.txt'), ('B', 'B_train.txt', 'val.txt'),
                              ('B_noreplay', 'local_train_x3.txt', 'val.txt'),
                              ('val', 'val.txt', 'val.txt'), ('test', 'test.txt', 'test.txt')):
        (Y / f'{yname}.yaml').write_text(f'path: {Y.as_posix()}\ntrain: {train}\nval: {val}\nnc: 4\nnames:\n{names}')

    md = ['# Local YOLO datasets (human-reviewed labels only)' + (', near zone' if a.near_zone else ''), '',
          '| Split | Frames | No damage | D00 | D10 | D20 | D40 |', '|---|---|---|---|---|---|---|']
    for split in ('train', 'val', 'test'):
        c = counts[split]
        md.append(f'| {split} | {c["frames"]} | {c["no damage"]} | ' + ' | '.join(str(c[k]) for k in CODES) + ' |')
    md += ['', '| Training list | Images per epoch | of which local |', '|---|---|---|']
    for name in ('local_train.txt', 'local_train_x3.txt', 'B_train.txt'):
        n_local = sum(1 for p in lists[name] if '/data/local/' in p)
        md.append(f'| {name} | {len(lists[name])} | {n_local} |')
    if a.near_zone:
        md.append('\nBoxes dropped (centre outside the near zone): ' + (', '.join(
            f'{sp} {c} {n}' for (sp, c), n in sorted(dropped.items())) or 'none') + '.')
    md.append(f'\n{"D10/D20/D40" if a.near_zone else "D10/D20"} train frames repeated x{a.repeat}: {len(rare)}. Replay: {len(replay)} images '
              f'(random of {len(rdd_train)} six-country RDD2022 train, seed 42). Test frames reviewed so far: '
              f'{len(use["test"])} of {sum(1 for r in sel if r["split"] == "test")}'
              + ('' if a.final else ' (rebuild with --final before the test evaluation)') + '.')
    (ROOT / 'results' / ('local_datasets_nz.md' if a.near_zone else 'local_datasets.md')).write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

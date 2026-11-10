"""Quality check of the annotation-site labels (final freeze, 2026-11-11).

    python ml/local/label_quality_site.py            # reads the snapshot named in results/FINAL_SNAPSHOT.txt

- Unchanged = a final (human) box with a model pre-label box (data/local/annotate/prelabels/*.txt,
  conf >= 0.15) of the same class at IoU >= 0.9. Reported per class and per labeller.
- Pace = seconds since the same labeller's previous save (gaps over 10 min are breaks, left out),
  median on damage frames vs no-damage frames.
- Spot-check list: 50 random new damage frames + 50 random new no-damage frames (seed 0).
Writes results/label_quality.md and results/spotcheck_list.csv.
"""

import csv
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
CODES = ['D00', 'D10', 'D20', 'D40']
PRE = ROOT / 'data/local/annotate/prelabels'


def iou(a, b):
    ax1, ay1, ax2, ay2 = a[0] - a[2] / 2, a[1] - a[3] / 2, a[0] + a[2] / 2, a[1] + a[3] / 2
    bx1, by1, bx2, by2 = b[0] - b[2] / 2, b[1] - b[3] / 2, b[0] + b[2] / 2, b[1] + b[3] / 2
    iw, ih = max(0, min(ax2, bx2) - max(ax1, bx1)), max(0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    u = a[2] * a[3] + b[2] * b[3] - inter
    return inter / u if u > 0 else 0


def pct(a, b):
    return f'{a / b:.0%}' if b else '–'


def main():
    snap = (ROOT / 'results/FINAL_SNAPSHOT.txt').read_text().split()[0]
    c = sqlite3.connect(f'file:{(ROOT / "backups" / snap).as_posix()}?mode=ro', uri=True)
    frames = {r[0]: dict(zip(('split', 'group', 'user', 'status', 'tier'), r[1:])) for r in c.execute(
        'SELECT frame_id, split, route_group, labeled_by, status, tier FROM frames')}
    human = defaultdict(list)
    for f, k, *xywh in c.execute("SELECT frame_id, class_id, cx, cy, w, h FROM boxes WHERE source='human'"):
        human[f].append((k, xywh))
    users = sorted({v['user'] for v in frames.values() if v['user']})

    # unchanged boxes
    tot, same = Counter(), Counter()
    drafts_total, drafts_kept = Counter(), Counter()
    for f, v in frames.items():
        if v['status'] != 'labeled':
            continue
        p = PRE / f'{f[:-4]}.txt'
        d = [(int(l.split()[0]), list(map(float, l.split()[1:5]))) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
        for k, b in human[f]:
            hit = any(dk == k and iou(b, db) >= 0.9 for dk, db in d)
            for key in ((v['user'], k), (v['user'], 'all'), ('all', k), ('all', 'all')):
                tot[key] += 1
                same[key] += hit
        for dk, db in d:
            kept = any(k == dk and iou(b, db) >= 0.9 for k, b in human[f])
            for key in (v['user'], 'all'):
                drafts_total[key] += 1
                drafts_kept[key] += kept

    # pace
    pace = defaultdict(lambda: {'damage': [], 'none': []})
    for u in users:
        ev = list(c.execute("SELECT frame_id, timestamp FROM events WHERE user=? AND action IN ('labeled','skipped') "
                            'ORDER BY timestamp', (u,)))
        for (_, t0), (f, t1) in zip(ev, ev[1:]):
            if t1 - t0 <= 600 and frames[f]['status'] == 'labeled' and frames[f]['user'] == u:
                pace[u]['damage' if human[f] else 'none'].append(t1 - t0)
    hours = {u: c.execute("SELECT MIN(timestamp), MAX(timestamp) FROM events WHERE user=? AND action='labeled'", (u,)).fetchone()
             for u in users}

    # spot-check list
    lab = sorted(f for f, v in frames.items() if v['status'] == 'labeled')
    dmg = [f for f in lab if human[f]]
    neg = [f for f in lab if not human[f]]
    rng = random.Random(0)
    pick = [('damage', f) for f in rng.sample(dmg, 50)] + [('no damage', f) for f in rng.sample(neg, 50)]
    with open(ROOT / 'results/spotcheck_list.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['kind', 'frame', 'split', 'route_group', 'labeled_by', 'tier', 'boxes', 'classes', 'had_draft',
                    'correct (yes/no)', 'note'])
        for kind, f in pick:
            v = frames[f]
            w.writerow([kind, f, v['split'], v['group'], v['user'], v['tier'], len(human[f]),
                        ' '.join(CODES[k] for k, _ in human[f]), int((PRE / f'{f[:-4]}.txt').stat().st_size > 0), '', ''])

    # report
    by_user = Counter((v['user'], v['split'], bool(human[f])) for f, v in frames.items() if v['status'] == 'labeled')
    md = ['# Annotation-site label quality (final freeze)', '',
          f'Snapshot `backups/{snap}`. Labelled {len(lab)} frames ({len(dmg)} with damage, {len(neg)} no damage), '
          f'skipped {sum(v["status"] == "skipped" for v in frames.values())}. Pre-labels: S5_v8m_1280, conf 0.15.', '',
          '## Final boxes kept unchanged from the model pre-labels (same class, IoU >= 0.9)', '',
          '| Labeller | ' + ' | '.join(CODES) + ' | All boxes | Drafts kept / drafts shown |', '|---|' + '---|' * 6]
    for u in users + ['all']:
        md.append(f'| {u} | ' + ' | '.join(f'{pct(same[(u, k)], tot[(u, k)])} ({same[(u, k)]}/{tot[(u, k)]})' for k in range(4))
                  + f' | {pct(same[(u, "all")], tot[(u, "all")])} ({same[(u, "all")]}/{tot[(u, "all")]})'
                  + f' | {pct(drafts_kept[u], drafts_total[u])} ({drafts_kept[u]}/{drafts_total[u]}) |')
    md += ['', '"Unchanged" share = of the final boxes, how many are a draft accepted as is. Last column = of the drafts '
           'the labeller saw, how many survived unchanged (the rest were deleted, re-classed or redrawn).', '',
           '## Pace (seconds since the same labeller\'s previous save; breaks over 10 min left out)', '',
           '| Labeller | Frames | Damage frames: n, median s | No-damage frames: n, median s | No-damage share | Saves under 2 s | Span |',
           '|---|---|---|---|---|---|---|']
    for u in users:
        d, n = pace[u]['damage'], pace[u]['none']
        allg = d + n
        span = (hours[u][1] - hours[u][0]) / 3600 if hours[u][0] else 0
        nd = sum(by_user[(u, s, False)] for s in ('train', 'val'))
        nn = nd + sum(by_user[(u, s, True)] for s in ('train', 'val'))
        md.append(f'| {u} | {nn} | {len(d)}, {median(d):.1f} | {len(n)}, {median(n):.1f} | {pct(nd, nn)} | '
                  f'{sum(g < 2 for g in allg)} ({pct(sum(g < 2 for g in allg), len(allg))}) | {span:.1f} h |')
    md += ['', '## Per labeller and split', '', '| Labeller | Train damage | Train no damage | Val damage | Val no damage |',
           '|---|---|---|---|---|']
    for u in users:
        md.append(f'| {u} | {by_user[(u, "train", True)]} | {by_user[(u, "train", False)]} | {by_user[(u, "val", True)]} | '
                  f'{by_user[(u, "val", False)]} |')
    md += ['', '## Spot check', '', '`results/spotcheck_list.csv`: 50 damage + 50 no-damage frames, random, seed 0. '
           'Fill in "correct (yes/no)".', '']
    (ROOT / 'results/label_quality.md').write_text('\n'.join(md), encoding='utf-8')
    print('\n'.join(md))
    print(Counter((frames[f]['user'], k) for k, f in pick))


if __name__ == '__main__':
    main()

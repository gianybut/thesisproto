"""Compare the automatic labels with the reviewed val/test labels (Steps 2 and 7.1).

    python ml/local/label_quality.py [--iou 0.5]

Uses only frames whose review is accepted (review_log.csv reviewed = yes); refuses otherwise.
The detector's boxes (autolabel_log.csv: every stand-in box of the four classes, with its CLIP
score and whether the AI check kept it) are matched one-to-one, greedily by IoU, to the reviewed
boxes of the same frame (both in band-crop pixels).

1. AI check per class (val only, used to choose the per-class rule): for each detector class,
   how many boxes the check KEPT / DROPPED that match a reviewed box of any class ("real damage")
   or match none ("false"). Candidate rules are scored the same way.
2. Pseudo-label quality (val + test, for Chapter V): precision and recall per class at IoU >= --iou,
   class-aware, for (a) the drafts the reviewers saw (detector + AI check) and (b) the detector
   alone; plus how many boxes the AI check removed and how many of those the reviewers confirmed
   were not damage (matched no reviewed box).
Caveat written into the report: reviewers saw (a) as drafts, which can anchor them toward it.

Writes results/step2_clip_check.md and results/step7_pseudo_label_quality.md.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict

from common import OUT, ROOT, read_csv

CODES = ['D00', 'D10', 'D20', 'D40']


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def match(preds, gts, thr, same_class):
    """Greedy one-to-one matching, highest IoU first. Returns {pred index: gt index}."""
    pairs = sorted(((iou(p['box'], g['box']), i, j) for i, p in enumerate(preds) for j, g in enumerate(gts)
                    if (not same_class or p['cls'] == g['cls'])), reverse=True)
    used_p, used_g, out = set(), set(), {}
    for v, i, j in pairs:
        if v < thr:
            break
        if i not in used_p and j not in used_g:
            out[i] = j
            used_p.add(i)
            used_g.add(j)
    return out


def load(thr):
    sel = read_csv(OUT / 'review_frames.csv')
    log = {r['frame']: r for r in read_csv(OUT / 'review_log.csv')}
    bad = [f['frame'] for f in sel if log.get(f['frame'], {}).get('reviewed') != 'yes']
    if bad:
        sys.exit(f'{len(bad)} val/test frames are not reviewed (e.g. {bad[:3]}): refusing to use unreviewed labels.')
    det = defaultdict(list)
    for r in read_csv(OUT / 'autolabel_log.csv'):
        if r['code'] in CODES:
            det[r['frame']].append(dict(box=tuple(float(r[k]) for k in ('x1', 'y1', 'x2', 'y2')), cls=r['code'],
                                        conf=float(r['det_conf']), clip=float(r['clip_score']), kept=r['kept'] == '1'))
    frames = []
    for f in sel:
        s = json.loads((OUT / 'reviewed' / 'state' / f'{f["frame"][:-4]}.json').read_text(encoding='utf-8'))
        gts = [dict(box=(b['x1'], b['y1'], b['x2'], b['y2']), cls=b['cls']) for b in s['boxes']]
        frames.append(dict(frame=f['frame'], split=f['split'], gts=gts, det=det.get(f['frame'], [])))
    return frames


def pr(frames, pick, thr):
    """Class-aware precision/recall of the boxes chosen by pick(box) against reviewed boxes."""
    tp, fp, fn = Counter(), Counter(), Counter()
    for fr in frames:
        preds = [d for d in fr['det'] if pick(d)]
        m = match(preds, fr['gts'], thr, same_class=True)
        for i, p in enumerate(preds):
            (tp if i in m else fp)[p['cls']] += 1
        matched_g = set(m.values())
        for j, g in enumerate(fr['gts']):
            if j not in matched_g:
                fn[g['cls']] += 1
    return tp, fp, fn


def fmt(n, d):
    return f'{n / d:.2f}' if d else '-'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iou', type=float, default=0.5)
    a = ap.parse_args()
    frames = load(a.iou)
    val = [f for f in frames if f['split'] == 'val']

    # 1. AI check vs reviewed val labels, class-agnostic "is it real damage".
    rows = defaultdict(Counter)
    for fr in val:
        m = match(fr['det'], fr['gts'], a.iou, same_class=False)
        for i, d in enumerate(fr['det']):
            real = i in m
            rows[d['cls']][('kept' if d['kept'] else 'dropped', 'real' if real else 'false')] += 1
            if real and fr['gts'][m[i]]['cls'] != d['cls']:
                rows[d['cls']]['wrong_class'] += 1
    md = ['# AI check (CLIP) per class against the reviewed val labels', '',
          f'Every stand-in detector box (confidence >= 0.25) in the 120 reviewed val frames, matched one-to-one to the '
          f'reviewed boxes at IoU >= {a.iou} (any class). "Real" = it matches a reviewed box; "false" = it matches none. '
          'The AI check keeps a box when its CLIP score is >= 0.60.', '',
          '| Detector class | Boxes | Kept, real | **Kept, false** | **Dropped, real** | Dropped, false | Real but other class |',
          '|---|---|---|---|---|---|---|']
    for c in CODES:
        r = rows[c]
        n = sum(v for k, v in r.items() if k != 'wrong_class')
        md.append(f'| {c} | {n} | {r[("kept", "real")]} | {r[("kept", "false")]} | {r[("dropped", "real")]} | '
                  f'{r[("dropped", "false")]} | {r["wrong_class"]} |')
    tot = Counter()
    for c in CODES:
        tot.update({k: v for k, v in rows[c].items()})
    md.append(f'| **all** | {sum(v for k, v in tot.items() if k != "wrong_class")} | {tot[("kept", "real")]} | '
              f'{tot[("kept", "false")]} | {tot[("dropped", "real")]} | {tot[("dropped", "false")]} | {tot["wrong_class"]} |')

    # Candidate rules, class-aware P/R on val.
    rules = {
        'detector only (no AI check)': lambda d: True,
        'AI check on all classes (current)': lambda d: d['kept'],
        'AI check for D20/D40; D00/D10 at conf >= 0.40': lambda d: d['kept'] if d['cls'] in ('D20', 'D40') else d['conf'] >= 0.40,
        'AI check for D20/D40; D00/D10 without it': lambda d: d['kept'] if d['cls'] in ('D20', 'D40') else True,
        'AI check for D40 only': lambda d: d['kept'] if d['cls'] == 'D40' else True,
    }
    md += ['', f'## Candidate rules on val (class-aware, IoU >= {a.iou})', '',
           '| Rule | ' + ' | '.join(f'{c} P | {c} R' for c in CODES) + ' | All P | All R |',
           '|---|' + '---|' * (2 * len(CODES) + 2)]
    for name, rule in rules.items():
        tp, fp, fn = pr(val, rule, a.iou)
        cells = []
        for c in CODES:
            cells += [f'{fmt(tp[c], tp[c] + fp[c])} ({tp[c]}/{tp[c] + fp[c]})', f'{fmt(tp[c], tp[c] + fn[c])} ({tp[c]}/{tp[c] + fn[c]})']
        T, F, N = sum(tp.values()), sum(fp.values()), sum(fn.values())
        md.append(f'| {name} | ' + ' | '.join(cells) + f' | {fmt(T, T + F)} | {fmt(T, T + N)} |')
    (ROOT / 'results' / 'step2_clip_check.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))

    # 2. Pseudo-label quality, val + test.
    out = ['# Pseudo-label quality (stand-in RDD2022 detector) against the reviewed labels', '',
           f'Reviewed val + test frames (240; 120 each). Class-aware matching at IoU >= {a.iou}. "Drafts" are the '
           'detector boxes the AI check kept (what the reviewers were shown); "detector alone" is every box of the '
           'four classes at confidence >= 0.25. Reviewers saw the drafts, which may anchor them toward accepting '
           'them; the boxes the AI check removed were not shown.', '',
           '| Split | Labels | ' + ' | '.join(f'{c} P | {c} R' for c in CODES) + ' | All P | All R | Reviewed boxes |',
           '|---|---|' + '---|' * (2 * len(CODES) + 3)]
    for split in ('val', 'test', 'val+test'):
        fs = [f for f in frames if split == 'val+test' or f['split'] == split]
        ngt = Counter(g['cls'] for f in fs for g in f['gts'])
        for name, rule in (('drafts (detector + AI check)', lambda d: d['kept']), ('detector alone', lambda d: True)):
            tp, fp, fn = pr(fs, rule, a.iou)
            cells = []
            for c in CODES:
                cells += [fmt(tp[c], tp[c] + fp[c]), fmt(tp[c], tp[c] + fn[c])]
            T, F, N = sum(tp.values()), sum(fp.values()), sum(fn.values())
            out.append(f'| {split} | {name} | ' + ' | '.join(cells) + f' | {fmt(T, T + F)} | {fmt(T, T + N)} | '
                       + ', '.join(f'{c} {ngt[c]}' for c in CODES) + ' |')
    removed = confirmed = 0
    by_cls = Counter()
    for fr in frames:
        m = match(fr['det'], fr['gts'], a.iou, same_class=False)
        for i, d in enumerate(fr['det']):
            if not d['kept']:
                removed += 1
                if i not in m:
                    confirmed += 1
                    by_cls[d['cls']] += 1
    out += ['', f'AI check: removed {removed} detector boxes in these frames; {confirmed} of them match no reviewed box '
            f'(confirmed not damage at IoU >= {a.iou}): ' + ', '.join(f'{c} {by_cls[c]}' for c in CODES) + '.']
    (ROOT / 'results' / 'step7_pseudo_label_quality.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('\n' + '\n'.join(out))


if __name__ == '__main__':
    main()

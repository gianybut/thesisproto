"""Fit the per-class pseudo-label rule for the teacher on the REVIEWED val frames (team decision
2026-11-09), and report the train yield. Writes no labels.

    python ml/local/fit_label_rule.py [--imgsz 960 1280] [--target-precision 0.60]

1. Image size: the teacher's class-aware AP@50 against the reviewed val labels at each --imgsz;
   the higher mean wins (val only; test is not looked at).
2. Per class: the LOWEST confidence threshold whose val precision is >= --target-precision
   (most recall at that precision); if no threshold reaches it, the threshold with the best F1.
3. CLIP: used for a class only if, at that class's threshold, keeping just the boxes with
   CLIP >= 0.60 (the backend's VERIFY_THRESHOLD) raises val precision.
4. Train yield: the teacher on every train frame at the chosen size, the rule applied; boxes and
   frames per class.
Matching: class-aware, IoU >= 0.50, one-to-one, highest confidence first (VOC style).
Writes data/local/teacher/label_rule.json and results/step2_pseudo_label_rule.md.
"""

import argparse
import json
import sys

from common import OUT, ROOT, read_csv
from label_quality import iou
import teacher_detect as td

CODES = ['D00', 'D10', 'D20', 'D40']
VERIFY = 0.60


def reviewed_val():
    log = {r['frame']: r for r in read_csv(OUT / 'review_log.csv')}
    sel = [f for f in read_csv(OUT / 'review_frames.csv') if f['split'] == 'val']
    bad = [f['frame'] for f in sel if log.get(f['frame'], {}).get('reviewed') != 'yes']
    if bad:
        sys.exit(f'{len(bad)} val frames not reviewed: refusing.')
    gts = {}
    for f in sel:
        s = json.loads((OUT / 'reviewed' / 'state' / f'{f["frame"][:-4]}.json').read_text(encoding='utf-8'))
        gts[f['frame']] = [dict(box=(b['x1'], b['y1'], b['x2'], b['y2']), cls=b['cls']) for b in s['boxes']]
    return gts


def score_class(dets, gts, c, keep=lambda d: True):
    """Detections of class c (kept by `keep`) sorted by confidence, each marked TP/FP; and n GT."""
    items = sorted(((d['conf'], f, d) for f in gts for d in dets.get(f, []) if d['cls'] == c and keep(d)),
                   key=lambda x: -x[0])
    used = set()
    marks = []
    for conf, f, d in items:
        best, bj = 0.5, None
        for j, g in enumerate(gts[f]):
            if g['cls'] == c and (f, j) not in used:
                v = iou(d['box'], g['box'])
                if v >= best:
                    best, bj = v, j
        if bj is not None:
            used.add((f, bj))
        marks.append((conf, bj is not None, d))
    return marks, sum(1 for f in gts for g in gts[f] if g['cls'] == c)


def ap(marks, n):
    if not n:
        return None
    tp = fp = 0
    pts = []
    for _, ok, _ in marks:
        tp += ok
        fp += not ok
        pts.append((tp / n, tp / (tp + fp)))
    # all-point interpolation
    s, prev_r = 0.0, 0.0
    for i, (r, _) in enumerate(pts):
        p = max(q for _, q in pts[i:])
        s += (r - prev_r) * p
        prev_r = r
    return s


def at(marks, n, t):
    sel = [m for m in marks if m[0] >= t]
    tp = sum(m[1] for m in sel)
    fp = len(sel) - tp
    p = tp / len(sel) if sel else 0.0
    r = tp / n if n else 0.0
    return tp, fp, n - tp, p, r, (2 * p * r / (p + r) if p + r else 0.0)


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument('--imgsz', nargs='+', type=int, default=[960, 1280])
    ap_.add_argument('--target-precision', type=float, default=0.60)
    a = ap_.parse_args()
    gts = reviewed_val()
    frames = list(gts)

    md = ['# Pseudo-label rule for the teacher, fitted on the reviewed val frames', '',
          f'{len(frames)} reviewed val frames; class-aware matching at IoU >= 0.50, one-to-one, highest confidence first. '
          'Test frames were not used.', '', '## Image size (teacher AP@50 on reviewed val)', '',
          '| imgsz | D00 | D10 | D20 | D40 | mean |', '|---|---|---|---|---|---|']
    best = None
    for s in a.imgsz:
        dets = td.detect(frames, s)
        aps = [ap(*score_class(dets, gts, c)) for c in CODES]
        m = sum(x for x in aps if x is not None) / len([x for x in aps if x is not None])
        md.append(f'| {s} | ' + ' | '.join('-' if x is None else f'{x:.3f}' for x in aps) + f' | {m:.3f} |')
        if best is None or m > best[1]:
            best = (s, m)
    imgsz = best[0]
    md += ['', f'Chosen: **{imgsz}**.', '']

    dets = td.add_clip(imgsz, frames, lambda d: True)
    rule = {'imgsz': imgsz, 'target_precision': a.target_precision, 'verify_threshold': VERIFY, 'classes': {}}
    md += [f'## Per-class rule (target precision {a.target_precision:.2f})', '',
           '| Class | Val instances | Threshold | How chosen | TP | FP | FN | Precision | Recall | '
           'With CLIP: P | With CLIP: R | CLIP used |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for c in CODES:
        marks, n = score_class(dets, gts, c)
        cands = sorted({m[0] for m in marks})
        ok = [t for t in cands if at(marks, n, t)[3] >= a.target_precision]
        if ok:
            t, how = min(ok), f'lowest with P >= {a.target_precision:.2f}'
        elif cands and max(at(marks, n, t)[5] for t in cands) > 0:
            t, how = max(cands, key=lambda t: (at(marks, n, t)[5], -t)), 'best F1 (target not reached)'
        else:   # not one correct box on val at any threshold: write no labels of this class
            t, how = 1.01, 'none: no correct box on val at any threshold'
        tp, fp, fn, p, r, _ = at(marks, n, t)
        cm, _ = score_class(dets, gts, c, keep=lambda d: d['clip'] is not None and d['clip'] >= VERIFY)
        ctp, cfp, _, cp, cr, _ = at(cm, n, t)
        use_clip = (ctp + cfp) > 0 and cp > p
        rule['classes'][c] = dict(threshold=round(t, 4), clip=use_clip, how=how, val=dict(tp=tp, fp=fp, fn=fn, p=p, r=r),
                                  val_with_clip=dict(tp=ctp, fp=cfp, p=cp, r=cr))
        md.append(f'| {c} | {n} | {"-" if t > 1 else f"{t:.3f}"} | {how} | {tp} | {fp} | {fn} | {p:.2f} | {r:.2f} | '
                  f'{cp:.2f} | {cr:.2f} | {"yes" if use_clip else "no"} |')

    # Train yield.
    train = [r['frame'] for r in read_csv(OUT / 'splits.csv') if r['split'] == 'train']
    print(f'Teacher on {len(train)} train frames at {imgsz} ...', flush=True)
    tdets = td.detect(train, imgsz)
    clip_cls = {c for c, v in rule['classes'].items() if v['clip']}
    if clip_cls:
        tdets = td.add_clip(imgsz, train, lambda d: d['cls'] in clip_cls and d['conf'] >= rule['classes'][d['cls']]['threshold'])

    def kept(d):
        v = rule['classes'][d['cls']]
        return d['conf'] >= v['threshold'] and (not v['clip'] or (d['clip'] is not None and d['clip'] >= VERIFY))

    boxes = {c: 0 for c in CODES}
    frames_c = {c: 0 for c in CODES}
    any_box = 0
    for f in train:
        k = [d for d in tdets.get(f, []) if kept(d)]
        any_box += bool(k)
        for c in CODES:
            n = sum(d['cls'] == c for d in k)
            boxes[c] += n
            frames_c[c] += bool(n)
    rule['train_yield'] = dict(frames=len(train), frames_with_box=any_box, boxes=boxes, frames_per_class=frames_c)
    md += ['', f'## Train yield ({len(train)} train frames, teacher at {imgsz}, rule above)', '',
           '| | D00 | D10 | D20 | D40 | Frames with any box |', '|---|---|---|---|---|---|',
           '| Boxes | ' + ' | '.join(str(boxes[c]) for c in CODES) + ' | |',
           '| Frames containing the class | ' + ' | '.join(str(frames_c[c]) for c in CODES) + f' | {any_box} |']
    md += ['', 'Small val counts (D10 13, D20 12 instances) make those thresholds uncertain; the expanded, '
           'second-pass-reviewed val set will be used to re-fit before labels are written.']
    (OUT / 'teacher').mkdir(exist_ok=True)
    (OUT / 'teacher' / 'label_rule.json').write_text(json.dumps(rule, indent=1))
    (ROOT / 'results' / 'step2_pseudo_label_rule.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

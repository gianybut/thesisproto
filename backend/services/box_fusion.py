"""Weighted box fusion: one list of boxes from the boxes of several models on the same picture.

Used by the video pipeline when ml/models/model_config.json lists more than one model ("ensemble"),
and by ml/local (ensemble_eval.py, calibrate_threshold.py) so the offline figures are computed with
exactly the code the app runs.

Per class, boxes of all models are taken from the most to the least confident. A box joins the cluster
whose fused box it overlaps most (IoU >= FUSE_IOU), else it starts a cluster. A cluster's box is the
confidence-weighted mean of its members and its score is the sum of their confidences divided by the
number of models: a damage both models found keeps about its confidence, one only a single model
found is halved (with two models). Run `python services/box_fusion.py` for its self-checks.
"""

FUSE_IOU = 0.55


def _iou(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    inter = w * h
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-9)


def fuse(per_model, iou=FUSE_IOU):
    """per_model: one list per model of (cls, x1, y1, x2, y2, conf). Returns fused [cls, x1, y1, x2, y2, conf]."""
    n = max(1, len(per_model))
    out = []
    for c in sorted({p[0] for preds in per_model for p in preds}):
        boxes = sorted((p for preds in per_model for p in preds if p[0] == c), key=lambda p: -p[5])
        clusters = []   # [fused box, members]
        for p in boxes:
            best, bi = iou, None
            for i, (fb, _) in enumerate(clusters):
                v = _iou(fb, p[1:5])
                if v >= best:
                    best, bi = v, i
            if bi is None:
                clusters.append([list(p[1:5]), [p]])
            else:
                members = clusters[bi][1]
                members.append(p)
                total = sum(m[5] for m in members)
                clusters[bi][0] = [sum(m[k] * m[5] for m in members) / total for k in (1, 2, 3, 4)]
        for fb, members in clusters:
            out.append([c, *fb, min(1.0, sum(m[5] for m in members) / n)])
    return out


if __name__ == '__main__':
    a = [(0, 10, 10, 50, 50, 0.8), (1, 100, 100, 140, 140, 0.6)]
    b = [(0, 12, 12, 52, 52, 0.4), (0, 300, 300, 340, 340, 0.5)]
    f = sorted(fuse([a, b]), key=lambda x: -x[5])
    assert len(f) == 3, f
    both = [x for x in f if x[0] == 0 and x[1] < 100][0]
    assert abs(both[5] - 0.6) < 1e-9 and 10 < both[1] < 12, both           # found by both: (0.8 + 0.4) / 2
    assert abs([x for x in f if x[0] == 1][0][5] - 0.3) < 1e-9             # found by one of two: halved
    assert fuse([a]) == [[0, 10, 10, 50, 50, 0.8], [1, 100, 100, 140, 140, 0.6]]   # one model: unchanged
    assert fuse([[], []]) == []
    print('box_fusion self-checks passed')

"""Would combining models help? Weighted box fusion of cached val predictions (no training, no test).

    python ml/local/ensemble_eval.py runs/eval/valsets/v1_val.json runs/eval/valsets/S5_v8m_1280_val.json [--set reviewed]

Each file is a prediction cache written by eval_val_sets.py or infer_sweep.py ({frame: {'wh', 'pred'}}).
Per frame and class, boxes of all models are clustered (IoU >= 0.55 with the cluster's fused box, highest
confidence first); a cluster's box is the confidence-weighted mean and its score the sum of confidences
divided by the number of models (a box only one model found is down-weighted). Prints mAP@50 / mAP@50-95
of every single model and of the fusion (eval_val_sets.metrics).
"""

import argparse
import json
import sys
from pathlib import Path

from common import ROOT
from eval_val_sets import CODES, SETS, frames, metrics

sys.path.insert(0, str(ROOT / 'backend' / 'services'))
from box_fusion import fuse  # noqa: E402  (the code the app runs)


def fused(dets, stems):
    """{frame: {'wh', 'pred'}} of the fusion of several caches, for the given frames."""
    return {s: {'wh': dets[0][s]['wh'], 'pred': fuse([d[s]['pred'] for d in dets])} for s in stems}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('caches', nargs='+')
    ap.add_argument('--set', choices=tuple(SETS), default='reviewed')
    a = ap.parse_args()
    stems = frames(SETS[a.set])
    dets = [json.loads((ROOT / c).read_text()) for c in a.caches]
    for c, d in zip(a.caches, dets):
        m = metrics(d, stems)
        print(f'{Path(c).parent.name}/{Path(c).stem:28} mAP50 {m["m50"]:.3f} mAP50-95 {m["m5095"]:.3f}  '
              + ' '.join(f'{k} {x:.3f}' for k, x in zip(CODES, m['ap50'])))
    m = metrics(fused(dets, stems), stems)
    print(f'{"FUSION of " + str(len(dets)):36} mAP50 {m["m50"]:.3f} mAP50-95 {m["m5095"]:.3f}  '
          + ' '.join(f'{k} {x:.3f}' for k, x in zip(CODES, m['ap50'])))


if __name__ == '__main__':
    main()

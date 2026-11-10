"""Score a model on the FULL foreign (RDD2022) val or test split, overall and per country.

    python ml/eval_foreign.py --weights runs/teacher/teacher/weights/best.pt --imgsz 960 --name teacher
    python ml/eval_foreign.py --weights ... --imgsz 1280 --name final --split test   # once, at the end

Val / test split = the 15% val / 15% test part of each of the six countries (ml/prepare_rdd2022.py,
seed 42), 3,277 images each. Standard Ultralytics validation (conf 0.001, IoU 0.7 NMS, AP@50 per class).
Writes results/<name>_foreign_<split>.md.
"""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTS = ROOT / 'data' / 'rdd2022' / 'lists'
TMP = ROOT / 'data' / 'rdd2022' / 'eval'
COUNTRIES = ['Japan', 'India', 'Czech', 'Norway', 'United_States', 'China_MotorBike']
CODES = ['D00', 'D10', 'D20', 'D40']


def yaml_for(name, lists):
    TMP.mkdir(parents=True, exist_ok=True)
    lst = TMP / f'{name}.txt'
    lst.write_text(''.join(Path(l).read_text() for l in lists))
    y = TMP / f'{name}.yaml'
    y.write_text(f'path: {TMP.as_posix()}\ntrain: {lst.name}\nval: {lst.name}\nnc: 4\nnames:\n'
                 + ''.join(f'  {i}: {c}\n' for i, c in enumerate(CODES)))
    return y, sum(1 for _ in lst.read_text().splitlines() if _.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--weights', required=True)
    ap.add_argument('--imgsz', type=int, required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--batch', type=int, default=12)
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--split', choices=['val', 'test'], default='val')
    a = ap.parse_args()
    from ultralytics import YOLO
    model = YOLO(str(ROOT / a.weights))
    sets = [('all six countries', [LISTS / f'{c}_{a.split}.txt' for c in COUNTRIES])] + \
           [(c, [LISTS / f'{c}_{a.split}.txt']) for c in COUNTRIES]
    rows = []
    for label, lists in sets:
        y, n = yaml_for(f"{a.split}_{label.replace(' ', '_')}", lists)
        m = model.val(data=str(y), imgsz=a.imgsz, batch=a.batch, workers=a.workers, device=0, split='val',
                      plots=label == 'all six countries', project=str(ROOT / 'runs' / 'eval'),
                      name=f'{a.name}_foreign_{a.split}_{label.replace(" ", "_")}', exist_ok=True, verbose=False)
        ap50 = dict(zip([int(i) for i in m.box.ap_class_index], [float(x) for x in m.box.ap50]))
        rows.append((label, n, float(m.box.mp), float(m.box.mr), float(m.box.map50), float(m.box.map),
                     [ap50.get(i) for i in range(4)]))
        print(label, n, f'mAP50 {m.box.map50:.3f}', flush=True)
    md = [f'# {a.name}: foreign (RDD2022) {a.split}, full split', '',
          f'Weights `{a.weights}`, imgsz {a.imgsz}. {a.split.capitalize()} = 15% of each country (seed 42), never used for training.'
          f' '
          'Standard Ultralytics validation (conf 0.001, NMS IoU 0.7).', '',
          f'| {a.split.capitalize()} set | Images | P | R | mAP@50 | mAP@50-95 | D00 AP@50 | D10 AP@50 | D20 AP@50 | D40 AP@50 |',
          '|---|---|---|---|---|---|---|---|---|---|']
    for label, n, p, r, m50, m, ap in rows:
        md.append(f'| {"**" + label + "**" if label.startswith("all") else label} | {n} | {p:.3f} | {r:.3f} | '
                  f'{m50:.3f} | {m:.3f} | ' + ' | '.join('-' if v is None else f'{v:.3f}' for v in ap) + ' |')
    out = ROOT / 'results' / f'{a.name}_foreign_{a.split}.md'
    out.write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

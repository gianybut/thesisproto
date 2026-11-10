"""Step 3: RDD2022 for six countries in YOLO format, split 70/15/15 by image, pre-resized.

    python ml/prepare_rdd2022.py [--src RDD2022_raw/RDD2022] [--max-side 1280]

- Countries: Japan, India, Czech, Norway, United_States, China_MotorBike. China_Drone is excluded:
  its pictures are taken from above (aerial), not from a vehicle like the team's.
- Only the annotated part of each release is used (train/annotations/xmls; the release's test
  images have no labels). Classes D00, D10, D20, D40 are kept (ids 0-3, ml/dataset_prep.py
  order); images with none of them are dropped.
- Split 70/15/15 by image within each country, fixed seed 42.
- Pre-resized copy (team decision 2026-11-09): every image is written with its longest side at most
  --max-side (smaller images are copied unchanged). YOLO labels are normalised, so they do not
  change. Norway's 3,650 x 2,044 originals otherwise slow the data loader.

Writes data/rdd2022/images/<country>/*.jpg, labels/<country>/*.txt, lists/<country>_<split>.txt
(absolute image paths) and results/step3_rdd2022_counts.md. Re-running skips images already done.
"""

import argparse
import random
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'rdd2022'
COUNTRIES = ['Japan', 'India', 'Czech', 'Norway', 'United_States', 'China_MotorBike']
CODES = ['D00', 'D10', 'D20', 'D40']
SEED = 42
SPLITS = (('train', 0.70), ('val', 0.15), ('test', 0.15))


def parse(xml_path):
    root = ET.parse(xml_path).getroot()
    w = int(root.find('size').findtext('width')); h = int(root.find('size').findtext('height'))
    lines = []
    for o in root.iter('object'):
        name = o.findtext('name', '').strip()
        if name not in CODES or not w or not h:
            continue
        b = o.find('bndbox')
        x1, y1, x2, y2 = (float(b.findtext(k)) for k in ('xmin', 'ymin', 'xmax', 'ymax'))
        x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
        y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))
        if x2 - x1 < 1 or y2 - y1 < 1:
            continue
        lines.append(f'{CODES.index(name)} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} {(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}')
    return lines


def convert(job):
    src_img, dst_img, max_side = job
    if dst_img.exists():
        return 0
    im = cv2.imread(str(src_img))
    if im is None:
        return -1
    h, w = im.shape[:2]
    if max(h, w) <= max_side:
        shutil.copy2(src_img, dst_img)
    else:
        k = max_side / max(h, w)
        im = cv2.resize(im, (round(w * k), round(h * k)), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(dst_img), im, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=str(ROOT / 'RDD2022_raw' / 'RDD2022'))
    ap.add_argument('--max-side', type=int, default=1280)
    ap.add_argument('--workers', type=int, default=6)
    a = ap.parse_args()
    src = Path(a.src)
    (OUT / 'lists').mkdir(parents=True, exist_ok=True)
    jobs, table = [], []
    for c in COUNTRIES:
        xmls = sorted((src / c / 'train' / 'annotations' / 'xmls').glob('*.xml'))
        imgs = {p.stem: p for p in (src / c / 'train' / 'images').iterdir()}
        keep = []
        for x in xmls:
            lines = parse(x)
            if lines and x.stem in imgs:
                keep.append((x.stem, lines))
        rng = random.Random(f'{SEED}-{c}')
        rng.shuffle(keep)
        n = len(keep)
        cut1, cut2 = round(n * SPLITS[0][1]), round(n * (SPLITS[0][1] + SPLITS[1][1]))
        parts = {'train': keep[:cut1], 'val': keep[cut1:cut2], 'test': keep[cut2:]}
        (OUT / 'images' / c).mkdir(parents=True, exist_ok=True)
        (OUT / 'labels' / c).mkdir(parents=True, exist_ok=True)
        for split, items in parts.items():
            paths = []
            counts = Counter()
            for stem, lines in items:
                s = imgs[stem]
                dst = OUT / 'images' / c / (stem + '.jpg')
                (OUT / 'labels' / c / (stem + '.txt')).write_text('\n'.join(lines) + '\n')
                jobs.append((s, dst, a.max_side))
                paths.append(dst.as_posix())
                counts.update(CODES[int(l.split()[0])] for l in lines)
            (OUT / 'lists' / f'{c}_{split}.txt').write_text('\n'.join(sorted(paths)) + '\n')
            table.append((c, split, len(items), counts))
        print(f'{c}: {len(xmls)} annotated, {n} with a target class -> '
              + ', '.join(f'{k} {len(v)}' for k, v in parts.items()), flush=True)

    print(f'Writing {len(jobs)} images (longest side <= {a.max_side}) ...', flush=True)
    with Pool(a.workers) as pool:
        res = pool.map(convert, jobs, chunksize=64)
    print(f'  resized/copied {sum(1 for r in res if r == 1)}, already there {res.count(0)}, unreadable {res.count(-1)}')

    md = ['# Step 3: RDD2022, six countries, four classes', '',
          'Annotated part of each country\'s release only; images without D00/D10/D20/D40 dropped; split 70/15/15 by '
          'image within each country, seed 42; pre-resized to longest side <= ' f'{a.max_side} px. China_Drone is '
          'excluded (aerial viewpoint, unlike the team\'s vehicle-mounted phone).', '',
          '| Country | Split | Images | D00 | D10 | D20 | D40 |', '|---|---|---|---|---|---|---|']
    for c, split, n, cnt in table:
        md.append(f'| {c} | {split} | {n} | ' + ' | '.join(str(cnt[k]) for k in CODES) + ' |')
    for split in ('train', 'val', 'test'):
        rows = [t for t in table if t[1] == split]
        tot = Counter()
        for t in rows:
            tot.update(t[3])
        md.append(f'| **all** | **{split}** | **{sum(t[2] for t in rows)}** | '
                  + ' | '.join(f'**{tot[k]}**' for k in CODES) + ' |')
    (ROOT / 'results').mkdir(exist_ok=True)
    (ROOT / 'results' / 'step3_rdd2022_counts.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

"""Step 7.3: images for the expert check of the reviewed labels (Sir Neri's form).

    python ml/local/annotation_sample.py [--per-class 25]

From the REVIEWED val/test labels only (refuses if any val/test frame is not reviewed): up to
--per-class random boxes per class (all of a class with fewer), fixed seed, shuffled together.
One image per box: the road-band frame with the box in one neutral colour (the same for every
class) and only its ID, and below it a zoomed close-up of the box. Nothing on the image tells the
class.

Writes data/local/annotation_form/images/<ID>.jpg, form_items.csv (ID, image file; what the form
script needs) and answer_key.csv (ID -> frame, split, box, reviewed class; KEEP PRIVATE: do not
upload it with the images or share it with the validator).
"""

import argparse
import json
import random
import shutil
import sys

import cv2
import numpy as np

from common import OUT, SEED, read_csv, write_csv

CODES = ['D00', 'D10', 'D20', 'D40']
FORM = OUT / 'annotation_form'
BOX = (255, 0, 255)   # magenta for every class; not one of the app's class colours


def render(frame_path, b, item_id):
    im = cv2.imread(str(frame_path))
    h, w = im.shape[:2]
    x1, y1, x2, y2 = (int(round(v)) for v in (b['x1'], b['y1'], b['x2'], b['y2']))
    top = im.copy()
    t = max(3, w // 400)
    cv2.rectangle(top, (x1 - t, y1 - t), (x2 + t, y2 + t), (0, 0, 0), t + 2)
    cv2.rectangle(top, (x1 - t, y1 - t), (x2 + t, y2 + t), BOX, t)
    top = cv2.resize(top, (1600, int(h * 1600 / w)))
    # Close-up: the box with as much road again around it, at least 160 px, enlarged to 800 px high.
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    side = max(160, 2 * max(x2 - x1, y2 - y1))
    l, r = int(max(0, cx - side)), int(min(w, cx + side))
    tt, bb = int(max(0, cy - side / 2)), int(min(h, cy + side / 2))
    crop = im[tt:bb, l:r].copy()
    cv2.rectangle(crop, (x1 - l, y1 - tt), (x2 - l, y2 - tt), BOX, max(2, t // 2))
    k = min(800 / crop.shape[0], 1600 / crop.shape[1])
    crop = cv2.resize(crop, (int(crop.shape[1] * k), int(crop.shape[0] * k)), interpolation=cv2.INTER_CUBIC)
    pad = np.full((crop.shape[0], 1600, 3), 255, np.uint8)
    pad[:, (1600 - crop.shape[1]) // 2:(1600 - crop.shape[1]) // 2 + crop.shape[1]] = crop
    head = np.full((70, 1600, 3), 255, np.uint8)
    cv2.putText(head, item_id, (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 0), 3)
    cv2.putText(head, 'whole picture (above) and close-up (below)', (330, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                (90, 90, 90), 2)
    sep = np.full((16, 1600, 3), 255, np.uint8)
    return np.vstack([head, top, sep, pad])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-class', type=int, default=25)
    a = ap.parse_args()
    sel = read_csv(OUT / 'review_frames.csv')
    log = {r['frame']: r for r in read_csv(OUT / 'review_log.csv')}
    bad = [f['frame'] for f in sel if log.get(f['frame'], {}).get('reviewed') != 'yes']
    if bad:
        sys.exit(f'{len(bad)} val/test frames are not reviewed: refusing.')
    boxes = {c: [] for c in CODES}
    for f in sel:
        s = json.loads((OUT / 'reviewed' / 'state' / f'{f["frame"][:-4]}.json').read_text(encoding='utf-8'))
        for b in s['boxes']:
            boxes[b['cls']].append((f, b))
    rng = random.Random(SEED)
    picked = []
    for c in CODES:
        pool = sorted(boxes[c], key=lambda x: (x[0]['frame'], x[1]['x1'], x[1]['y1']))
        picked += rng.sample(pool, min(a.per_class, len(pool)))
    rng.shuffle(picked)
    shutil.rmtree(FORM, ignore_errors=True)
    (FORM / 'images').mkdir(parents=True)
    key, items = [], []
    for i, (f, b) in enumerate(picked, 1):
        item_id = f'B{i:03d}'
        cv2.imwrite(str(FORM / 'images' / f'{item_id}.jpg'), render(OUT / 'frames' / f['frame'], b, item_id),
                    [cv2.IMWRITE_JPEG_QUALITY, 88])
        items.append(dict(id=item_id, image=f'{item_id}.jpg'))
        key.append(dict(id=item_id, frame=f['frame'], split=f['split'], route_group=f['route_group'],
                        x1=b['x1'], y1=b['y1'], x2=b['x2'], y2=b['y2'], reviewed_class=b['cls'],
                        origin=b.get('origin', '')))
    write_csv(FORM / 'form_items.csv', items)
    write_csv(FORM / 'answer_key.csv', key)
    n = {c: sum(1 for k in key if k['reviewed_class'] == c) for c in CODES}
    print(f'{len(key)} boxes: ' + ', '.join(f'{c} {n[c]} of {len(boxes[c])}' for c in CODES))
    print(f'-> {FORM / "images"} ({len(items)} images), form_items.csv, answer_key.csv (private)')


if __name__ == '__main__':
    main()

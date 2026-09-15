"""
Convert RDD2022 in dataset-ninja (Supervisely JSON) format to YOLO format.
Keeps the four CRDDC 2022 classes using RDD2022's own codes — there is no D30 in RDD2022:
    D00 longitudinal crack, D10 transverse crack, D20 alligator crack, D40 pothole

The class titles dataset-ninja uses can differ from the raw codes. CLASS_ALIASES lists every
spelling seen so far; anything unrecognised is collected and printed at the end so you can add it.
Check meta.json in the dataset root if a class comes out empty.
"""
import json
import os
import glob
import shutil
import random
from pathlib import Path

# YOLO index order — must match backend/services/video_processor.py's fallback map.
CLASS_NAMES = ['longitudinal_crack', 'transverse_crack', 'alligator_crack', 'pothole']

# Normalised classTitle -> YOLO index. Titles are lower-cased with '_' and '-' turned into spaces.
CLASS_ALIASES = {
    'd00': 0, 'longitudinal crack': 0, 'longitudinal': 0, 'longitudinal cracks': 0,
    'd10': 1, 'transverse crack': 1, 'transverse': 1, 'lateral crack': 1, 'transverse cracks': 1,
    'd20': 2, 'alligator crack': 2, 'alligator': 2, 'crocodile crack': 2, 'alligator cracks': 2,
    'd40': 3, 'pothole': 3, 'potholes': 3,
}

MAX_PER_CLASS = 2500          # C3 cap; set to None to keep everything
TRAIN_RATIO, VAL_RATIO = 0.80, 0.15
RANDOM_SEED = 42


def _normalise(title):
    return (title or '').strip().lower().replace('_', ' ').replace('-', ' ')


def cap_per_class(pairs, max_per_class):
    if not max_per_class:
        return pairs
    pairs = list(pairs)
    random.Random(RANDOM_SEED).shuffle(pairs)
    per_class = {i: 0 for i in range(len(CLASS_NAMES))}
    kept = []
    for img, labels in pairs:
        classes = {int(l.split()[0]) for l in labels}
        if any(per_class[c] < max_per_class for c in classes):
            kept.append((img, labels))
            for c in classes:
                per_class[c] += 1
    return kept


def convert_rdd2022_ninja_to_yolo(src_dir, output_dir, max_per_class=MAX_PER_CLASS):
    src_dir = os.path.expanduser(src_dir)
    output_dir = os.path.expanduser(output_dir)

    print("=" * 60)
    print("🔄 RDD2022 (dataset-ninja) → YOLO, four CRDDC 2022 classes")
    print("=" * 60)

    all_pairs = []
    unknown_titles = {}
    box_counts = {n: 0 for n in CLASS_NAMES}

    for split in ['train', 'test']:
        ann_dir = os.path.join(src_dir, split, 'ann')
        img_dir = os.path.join(src_dir, split, 'img')
        if not os.path.exists(ann_dir):
            print(f"⚠️  Skipping {split}: {ann_dir} not found")
            continue

        ann_files = glob.glob(os.path.join(ann_dir, '*.json'))
        print(f"📁 Processing {split}: {len(ann_files)} annotation files...")

        for ann_file in ann_files:
            with open(ann_file) as f:
                data = json.load(f)
            img_h = data['size']['height']
            img_w = data['size']['width']
            if img_w == 0 or img_h == 0:
                continue

            labels = []
            for obj in data.get('objects', []):
                if obj.get('geometryType') != 'rectangle':
                    continue
                title = _normalise(obj.get('classTitle'))
                if title not in CLASS_ALIASES:
                    unknown_titles[title] = unknown_titles.get(title, 0) + 1
                    continue
                cls = CLASS_ALIASES[title]

                points = obj.get('points', {}).get('exterior', [])
                if len(points) != 2:
                    continue
                (x1, y1), (x2, y2) = points
                cx = max(0, min(1, ((x1 + x2) / 2.0) / img_w))
                cy = max(0, min(1, ((y1 + y2) / 2.0) / img_h))
                w = max(0.001, min(1, abs(x2 - x1) / img_w))
                h = max(0.001, min(1, abs(y2 - y1) / img_h))
                labels.append(f"{cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
                box_counts[CLASS_NAMES[cls]] += 1

            if labels:
                img_name = os.path.basename(ann_file).replace('.json', '')
                img_path = os.path.join(img_dir, img_name)
                if os.path.exists(img_path):
                    all_pairs.append((img_path, labels))

    print(f"\n📊 Images with target-class boxes: {len(all_pairs)}")
    print(f"📊 Boxes per class: {box_counts}")
    if unknown_titles:
        print(f"⚠️  Unrecognised classTitles (skipped): {unknown_titles}")
        print("   Add them to CLASS_ALIASES if they are one of the four target classes.")

    if not all_pairs:
        print("❌ No target-class data found!")
        return

    if max_per_class:
        all_pairs = cap_per_class(all_pairs, max_per_class)
        print(f"📉 Capped to ≤{max_per_class} images per class → {len(all_pairs)} images")

    random.seed(RANDOM_SEED)
    random.shuffle(all_pairs)
    n = len(all_pairs)
    train_end = int(TRAIN_RATIO * n)
    val_end = int((TRAIN_RATIO + VAL_RATIO) * n)
    splits = {
        'train': all_pairs[:train_end],
        'val': all_pairs[train_end:val_end],
        'test': all_pairs[val_end:],
    }

    for split_name, pairs in splits.items():
        img_out = os.path.join(output_dir, split_name, 'images')
        lbl_out = os.path.join(output_dir, split_name, 'labels')
        os.makedirs(img_out, exist_ok=True)
        os.makedirs(lbl_out, exist_ok=True)
        for idx, (img_path, labels) in enumerate(pairs):
            ext = os.path.splitext(img_path)[1]
            new_name = f"rdd_{idx:05d}"
            shutil.copy2(img_path, os.path.join(img_out, new_name + ext))
            with open(os.path.join(lbl_out, new_name + '.txt'), 'w') as f:
                f.write('\n'.join(labels))
        print(f"   {split_name}: {len(pairs)} images")

    names_block = "\n".join(f"  {i}: {name}" for i, name in enumerate(CLASS_NAMES))
    yaml_content = f"""# Road Damage Detection Dataset — RDD2022 four-class subset (CRDDC 2022 codes)
# {n} images from dataset-ninja export{f', capped at {max_per_class}/class' if max_per_class else ''}

path: {os.path.abspath(output_dir)}
train: train/images
val: val/images
test: test/images

nc: {len(CLASS_NAMES)}

names:
{names_block}
"""
    yaml_path = os.path.join(output_dir, 'data.yaml')
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.yaml'), 'w') as f:
        f.write(yaml_content)

    print(f"\n✅ Dataset ready at: {output_dir}")
    print(f"📝 data.yaml saved to: {yaml_path}")
    print(f"\n🚀 Next: python train_model.py --data {yaml_path} --model yolov8m --epochs 100")


if __name__ == '__main__':
    convert_rdd2022_ninja_to_yolo(
        src_dir='~/dataset-ninja/rdd2022',
        output_dir='./datasets/rdd2022_4class',
    )

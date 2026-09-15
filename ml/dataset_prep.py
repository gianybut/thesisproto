"""
RDD2022 Dataset Preparation Script
Filters RDD2022 (Pascal-VOC XML) to the four CRDDC 2022 classes and converts to YOLO format.

Classes follow RDD2022's own codes (Arya et al., 2022) — there is no D30 in RDD2022:
    D00 longitudinal crack, D10 transverse crack, D20 alligator crack, D40 pothole

Usage:
    python dataset_prep.py --local <extracted RDD2022 path>            # full four-class set
    python dataset_prep.py --local <path> --max-per-class 2500         # capped, balanced subset
    python dataset_prep.py --download                                  # instructions + synthetic smoke set
"""

import os
import sys
import shutil
import random
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


# RDD2022 code -> human name (for reference / yaml comments)
RDD2022_CLASSES = {
    'D00': 'longitudinal_crack',
    'D10': 'transverse_crack',
    'D20': 'alligator_crack',
    'D40': 'pothole',
}

# RDD2022 code -> YOLO class index. This order is what backend/services/video_processor.py
# falls back to when a model's class names cannot be matched, so keep it stable.
TARGET_CLASSES = {'D00': 0, 'D10': 1, 'D20': 2, 'D40': 3}
CLASS_NAMES = [RDD2022_CLASSES[c] for c in TARGET_CLASSES]  # index order

# Split ratios (thesis Sec 3.2.1). The local Philippine set uses 70/15/15 — see convert notes.
TRAIN_RATIO, VAL_RATIO = 0.80, 0.15   # remaining 0.05 -> test

RANDOM_SEED = 42


def download_rdd2022(output_dir):
    """Explain the manual download and build a synthetic smoke-test set."""
    print("📥 RDD2022 dataset")
    print("   Official source: https://data.mendeley.com/datasets/5ty2wb6gvg/1  (~3.5 GB)")
    print("   Or the figshare mirror used by download_rdd2022.py (~13 GB, all countries).")
    print()
    print("   1. Download and extract to a local directory")
    print("   2. Run: python dataset_prep.py --local <extracted_path> [--max-per-class N]")
    print()
    create_sample_dataset(output_dir)


def create_sample_dataset(output_dir):
    """Small synthetic dataset so the training pipeline can be smoke-tested without RDD2022.

    Only potholes are synthesised (class index 3); the other three classes stay empty.
    """
    print("📁 Creating synthetic smoke-test dataset...")

    base = os.path.join(output_dir, 'pothole_dataset')
    for split in ['train', 'val', 'test']:
        os.makedirs(os.path.join(base, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(base, split, 'labels'), exist_ok=True)

    pothole_idx = TARGET_CLASSES['D40']

    import numpy as np
    try:
        import cv2

        for split, count in [('train', 100), ('val', 20), ('test', 10)]:
            for i in range(count):
                img = np.zeros((640, 640, 3), dtype=np.uint8)
                base_gray = random.randint(80, 140)
                img[:] = [base_gray, base_gray, base_gray]
                noise = np.random.randint(-20, 20, img.shape, dtype=np.int16)
                img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

                labels = []
                for _ in range(random.randint(1, 3)):
                    cx = random.randint(100, 540)
                    cy = random.randint(100, 540)
                    w = random.randint(40, 150)
                    h = random.randint(30, 120)
                    dark = random.randint(20, 60)
                    cv2.ellipse(img, (cx, cy), (w // 2, h // 2), 0, 0, 360, (dark, dark + 5, dark), -1)
                    for _ in range(5):
                        dx = random.randint(-w // 4, w // 4)
                        dy = random.randint(-h // 4, h // 4)
                        cv2.circle(img, (cx + dx, cy + dy), random.randint(5, 15),
                                   (dark + 10, dark + 10, dark + 10), -1)
                    labels.append(f"{pothole_idx} {cx / 640:.6f} {cy / 640:.6f} {w / 640:.6f} {h / 640:.6f}")

                cv2.imwrite(os.path.join(base, split, 'images', f'synthetic_{i:04d}.jpg'), img)
                with open(os.path.join(base, split, 'labels', f'synthetic_{i:04d}.txt'), 'w') as f:
                    f.write('\n'.join(labels))

        print("✅ Generated synthetic dataset: 100 train, 20 val, 10 test images (potholes only)")

    except ImportError:
        print("⚠️  OpenCV not available. Creating placeholder labels only.")
        for split, count in [('train', 10), ('val', 3), ('test', 2)]:
            for i in range(count):
                with open(os.path.join(base, split, 'labels', f'synthetic_{i:04d}.txt'), 'w') as f:
                    f.write(f"{pothole_idx} 0.5 0.5 0.2 0.15\n")

    create_data_yaml(base, note="synthetic smoke-test set")
    print(f"📁 Dataset ready at: {base}")
    return base


def cap_per_class(pairs, max_per_class, seed=RANDOM_SEED):
    """Keep at most `max_per_class` images per class (C3: a stated, defensible sampling rule).

    An image counts toward every class it contains. Images are visited in a seeded random order
    and kept while at least one of their classes is still under the cap, which keeps rare classes
    fully represented and trims only the abundant ones.
    """
    if not max_per_class:
        return pairs
    pairs = list(pairs)
    random.Random(seed).shuffle(pairs)
    per_class = {i: 0 for i in TARGET_CLASSES.values()}
    kept = []
    for img, labels in pairs:
        classes = {int(l.split()[0]) for l in labels}
        if any(per_class[c] < max_per_class for c in classes):
            kept.append((img, labels))
            for c in classes:
                per_class[c] += 1
    return kept


def class_box_counts(pairs):
    counts = {name: 0 for name in CLASS_NAMES}
    for _, labels in pairs:
        for l in labels:
            counts[CLASS_NAMES[int(l.split()[0])]] += 1
    return counts


def convert_rdd2022_to_yolo(rdd_path, output_dir, max_per_class=None):
    """Convert RDD2022 VOC annotations to YOLO format, keeping the four CRDDC 2022 classes."""
    print(f"🔄 Converting RDD2022 dataset from: {rdd_path}")

    base = os.path.join(output_dir, 'pothole_dataset')
    all_pairs = []

    # RDD2022 has country subdirectories (China_Drone, India, Japan, ...) each with train/test
    for country_dir in Path(rdd_path).iterdir():
        if not country_dir.is_dir():
            continue
        for split_dir in country_dir.iterdir():
            if not split_dir.is_dir():
                continue
            images_dir = split_dir / 'images'
            annotations_dir = split_dir / 'annotations' / 'xmls'
            if not annotations_dir.exists():
                annotations_dir = split_dir / 'annotations'
            if not images_dir.exists():
                continue
            for img_file in images_dir.glob('*.jpg'):
                xml_file = annotations_dir / f"{img_file.stem}.xml"
                if xml_file.exists():
                    labels = _parse_voc_annotation(xml_file)
                    if labels:
                        all_pairs.append((str(img_file), labels))

    if not all_pairs:
        print("⚠️  No annotations for the four target classes found in the provided path.")
        print("   Falling back to synthetic dataset generation.")
        return create_sample_dataset(output_dir)

    print(f"📊 Found {len(all_pairs)} annotated images before capping")
    print(f"   boxes per class: {class_box_counts(all_pairs)}")

    if max_per_class:
        all_pairs = cap_per_class(all_pairs, max_per_class)
        print(f"📉 Capped to ≤{max_per_class} images per class → {len(all_pairs)} images")
        print(f"   boxes per class: {class_box_counts(all_pairs)}")

    random.Random(RANDOM_SEED).shuffle(all_pairs)
    n = len(all_pairs)
    train_end = int(TRAIN_RATIO * n)
    val_end = int((TRAIN_RATIO + VAL_RATIO) * n)
    splits = {
        'train': all_pairs[:train_end],
        'val': all_pairs[train_end:val_end],
        'test': all_pairs[val_end:],
    }

    for split_name, pairs in splits.items():
        img_dir = os.path.join(base, split_name, 'images')
        lbl_dir = os.path.join(base, split_name, 'labels')
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(lbl_dir, exist_ok=True)
        for idx, (img_path, labels) in enumerate(pairs):
            ext = os.path.splitext(img_path)[1]
            shutil.copy2(img_path, os.path.join(img_dir, f"rdd_{idx:05d}{ext}"))
            with open(os.path.join(lbl_dir, f"rdd_{idx:05d}.txt"), 'w') as f:
                f.write('\n'.join(labels))
        print(f"   {split_name}: {len(pairs)} images")

    note = f"RDD2022 four-class subset, {n} images" + (f", ≤{max_per_class}/class" if max_per_class else "")
    create_data_yaml(base, note=note)
    print(f"✅ Dataset conversion complete: {base}")
    return base


def _parse_voc_annotation(xml_path):
    """Parse VOC XML and emit YOLO lines for every object in TARGET_CLASSES."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        size = root.find('size')
        if size is None:
            return []
        img_w = int(size.find('width').text)
        img_h = int(size.find('height').text)
        if img_w == 0 or img_h == 0:
            return []

        labels = []
        for obj in root.findall('object'):
            name = obj.find('name').text.strip()
            if name not in TARGET_CLASSES:
                continue
            cls_id = TARGET_CLASSES[name]
            bbox = obj.find('bndbox')
            xmin = float(bbox.find('xmin').text)
            ymin = float(bbox.find('ymin').text)
            xmax = float(bbox.find('xmax').text)
            ymax = float(bbox.find('ymax').text)

            cx = max(0, min(1, (xmin + xmax) / 2.0 / img_w))
            cy = max(0, min(1, (ymin + ymax) / 2.0 / img_h))
            w = max(0, min(1, (xmax - xmin) / img_w))
            h = max(0, min(1, (ymax - ymin) / img_h))
            labels.append(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        return labels

    except Exception as e:
        print(f"   Warning: Could not parse {xml_path}: {e}")
        return []


def create_data_yaml(dataset_path, note=""):
    """Write the YOLO data.yaml for the four-class set (here and in ml/)."""
    names_block = "\n".join(f"  {i}: {name}" for i, name in enumerate(CLASS_NAMES))
    yaml_content = f"""# Road Damage Detection Dataset — RDD2022 codes (CRDDC 2022 classes)
# {note}

path: {os.path.abspath(dataset_path)}
train: train/images
val: val/images
test: test/images

nc: {len(CLASS_NAMES)}

names:
{names_block}
"""
    yaml_path = os.path.join(dataset_path, 'data.yaml')
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    ml_yaml = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.yaml')
    with open(ml_yaml, 'w') as f:
        f.write(yaml_content)

    print(f"📝 Created data.yaml at: {yaml_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare RDD2022 (four-class) for YOLO training')
    parser.add_argument('--download', action='store_true', help='Show download instructions and build a synthetic smoke set')
    parser.add_argument('--local', type=str, help='Path to locally extracted RDD2022 dataset')
    parser.add_argument('--output', type=str, default='./datasets', help='Output directory')
    parser.add_argument('--max-per-class', type=int, default=None,
                        help='Cap images per class (e.g. 2500 → roughly ≤10k images total)')
    args = parser.parse_args()

    if args.local:
        convert_rdd2022_to_yolo(args.local, args.output, max_per_class=args.max_per_class)
    else:
        download_rdd2022(args.output)

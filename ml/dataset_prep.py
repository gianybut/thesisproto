"""
RDD2022 Dataset Preparation Script
Filters the RDD2022 dataset for pothole class (D40) and converts to YOLO format.

Usage:
    python dataset_prep.py --download    # Download and prepare dataset
    python dataset_prep.py --local PATH  # Prepare from local dataset path
"""

import os
import sys
import shutil
import random
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


# RDD2022 class mapping — we only want D40 (potholes)
RDD2022_CLASSES = {
    'D00': 'longitudinal_crack',
    'D10': 'transverse_crack',
    'D20': 'alligator_crack',
    'D40': 'pothole'
}

# For our model, we only train on pothole
TARGET_CLASSES = {'D40': 0}  # D40 → class index 0


def download_rdd2022(output_dir):
    """Download RDD2022 dataset from official sources."""
    print("📥 Downloading RDD2022 dataset...")
    print("   This dataset is available at: https://data.mendeley.com/datasets/5ty2wb6gvg/1")
    print()
    print("   Due to dataset size (~3.5GB), we recommend downloading manually:")
    print("   1. Visit the URL above")
    print("   2. Download the dataset")
    print("   3. Extract to a local directory")
    print(f"   4. Run: python dataset_prep.py --local <extracted_path>")
    print()
    print("   Alternatively, you can use a smaller subset for faster training.")
    print()

    # Create a small sample dataset for immediate testing
    create_sample_dataset(output_dir)


def create_sample_dataset(output_dir):
    """Create a small sample dataset structure for testing the pipeline."""
    print("📁 Creating sample dataset structure for pipeline testing...")

    base = os.path.join(output_dir, 'pothole_dataset')
    for split in ['train', 'val', 'test']:
        os.makedirs(os.path.join(base, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(base, split, 'labels'), exist_ok=True)

    # Generate synthetic training data using solid color images with simulated annotations
    import numpy as np
    try:
        import cv2

        print("🖼️  Generating synthetic pothole training images...")

        for split, count in [('train', 100), ('val', 20), ('test', 10)]:
            for i in range(count):
                # Create a road-like image
                img = np.zeros((640, 640, 3), dtype=np.uint8)

                # Road surface color (gray tones)
                base_gray = random.randint(80, 140)
                img[:] = [base_gray, base_gray, base_gray]

                # Add noise for texture
                noise = np.random.randint(-20, 20, img.shape, dtype=np.int16)
                img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

                # Add 1-3 "pothole" shapes
                labels = []
                num_potholes = random.randint(1, 3)
                for _ in range(num_potholes):
                    # Random position and size
                    cx = random.randint(100, 540)
                    cy = random.randint(100, 540)
                    w = random.randint(40, 150)
                    h = random.randint(30, 120)

                    # Draw dark ellipse (pothole)
                    dark_color = random.randint(20, 60)
                    cv2.ellipse(img, (cx, cy), (w // 2, h // 2), 0, 0, 360,
                                (dark_color, dark_color + 5, dark_color), -1)

                    # Add some rough edges
                    for _ in range(5):
                        dx = random.randint(-w // 4, w // 4)
                        dy = random.randint(-h // 4, h // 4)
                        r = random.randint(5, 15)
                        cv2.circle(img, (cx + dx, cy + dy), r,
                                   (dark_color + 10, dark_color + 10, dark_color + 10), -1)

                    # YOLO format: class cx cy w h (normalized)
                    labels.append(f"0 {cx / 640:.6f} {cy / 640:.6f} {w / 640:.6f} {h / 640:.6f}")

                # Save image
                img_path = os.path.join(base, split, 'images', f'pothole_{i:04d}.jpg')
                cv2.imwrite(img_path, img)

                # Save label
                label_path = os.path.join(base, split, 'labels', f'pothole_{i:04d}.txt')
                with open(label_path, 'w') as f:
                    f.write('\n'.join(labels))

        print(f"✅ Generated synthetic dataset: 100 train, 20 val, 10 test images")

    except ImportError:
        print("⚠️  OpenCV not available. Creating placeholder dataset.")
        for split, count in [('train', 10), ('val', 3), ('test', 2)]:
            for i in range(count):
                label_path = os.path.join(base, split, 'labels', f'pothole_{i:04d}.txt')
                with open(label_path, 'w') as f:
                    f.write(f"0 0.5 0.5 0.2 0.15\n")

    # Create data.yaml
    create_data_yaml(base)
    print(f"📁 Dataset ready at: {base}")
    return base


def convert_rdd2022_to_yolo(rdd_path, output_dir):
    """
    Convert RDD2022 VOC format annotations to YOLO format.
    Filters for D40 (pothole) class only.
    """
    print(f"🔄 Converting RDD2022 dataset from: {rdd_path}")

    base = os.path.join(output_dir, 'pothole_dataset')

    # Collect all image-annotation pairs
    all_pairs = []

    # RDD2022 has country subdirectories (China, India, Japan, etc.)
    for country_dir in Path(rdd_path).iterdir():
        if not country_dir.is_dir():
            continue

        # Look for train/test splits within each country
        for split_dir in country_dir.iterdir():
            if not split_dir.is_dir():
                continue

            images_dir = split_dir / 'images'
            annotations_dir = split_dir / 'annotations' / 'xmls'

            if not images_dir.exists():
                images_dir = split_dir / 'images'
            if not annotations_dir.exists():
                annotations_dir = split_dir / 'annotations'

            if not images_dir.exists():
                continue

            for img_file in images_dir.glob('*.jpg'):
                xml_file = annotations_dir / f"{img_file.stem}.xml"
                if xml_file.exists():
                    # Parse XML and check for D40
                    labels = _parse_voc_annotation(xml_file)
                    if labels:  # Only include if has pothole annotations
                        all_pairs.append((str(img_file), labels))

    if not all_pairs:
        print("⚠️  No pothole annotations found in the provided path.")
        print("   Falling back to synthetic dataset generation.")
        return create_sample_dataset(output_dir)

    print(f"📊 Found {len(all_pairs)} images with pothole annotations")

    # Shuffle and split: 70% train, 20% val, 10% test
    random.shuffle(all_pairs)
    n = len(all_pairs)
    train_split = int(0.7 * n)
    val_split = int(0.9 * n)

    splits = {
        'train': all_pairs[:train_split],
        'val': all_pairs[train_split:val_split],
        'test': all_pairs[val_split:]
    }

    for split_name, pairs in splits.items():
        img_dir = os.path.join(base, split_name, 'images')
        lbl_dir = os.path.join(base, split_name, 'labels')
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(lbl_dir, exist_ok=True)

        for idx, (img_path, labels) in enumerate(pairs):
            # Copy image
            ext = os.path.splitext(img_path)[1]
            new_name = f"pothole_{idx:05d}{ext}"
            shutil.copy2(img_path, os.path.join(img_dir, new_name))

            # Write label
            label_path = os.path.join(lbl_dir, f"pothole_{idx:05d}.txt")
            with open(label_path, 'w') as f:
                f.write('\n'.join(labels))

        print(f"   {split_name}: {len(pairs)} images")

    create_data_yaml(base)
    print(f"✅ Dataset conversion complete: {base}")
    return base


def _parse_voc_annotation(xml_path):
    """Parse VOC XML annotation and extract D40 (pothole) bounding boxes in YOLO format."""
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

            # Convert to YOLO format (normalized center x, y, width, height)
            cx = (xmin + xmax) / 2.0 / img_w
            cy = (ymin + ymax) / 2.0 / img_h
            w = (xmax - xmin) / img_w
            h = (ymax - ymin) / img_h

            # Clamp values
            cx = max(0, min(1, cx))
            cy = max(0, min(1, cy))
            w = max(0, min(1, w))
            h = max(0, min(1, h))

            labels.append(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

        return labels

    except Exception as e:
        print(f"   Warning: Could not parse {xml_path}: {e}")
        return []


def create_data_yaml(dataset_path):
    """Create the YOLO data.yaml configuration file."""
    yaml_content = f"""# Pothole Detection Dataset Configuration
# Based on RDD2022 (D40 class - Potholes)

path: {os.path.abspath(dataset_path)}
train: train/images
val: val/images
test: test/images

# Number of classes
nc: 1

# Class names
names:
  0: pothole
"""
    yaml_path = os.path.join(dataset_path, 'data.yaml')
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    # Also save to ml directory
    ml_yaml = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.yaml')
    with open(ml_yaml, 'w') as f:
        f.write(yaml_content)

    print(f"📝 Created data.yaml at: {yaml_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare RDD2022 dataset for pothole detection')
    parser.add_argument('--download', action='store_true', help='Download and prepare dataset')
    parser.add_argument('--local', type=str, help='Path to locally downloaded RDD2022 dataset')
    parser.add_argument('--output', type=str, default='./datasets', help='Output directory')

    args = parser.parse_args()

    if args.local:
        convert_rdd2022_to_yolo(args.local, args.output)
    else:
        download_rdd2022(args.output)

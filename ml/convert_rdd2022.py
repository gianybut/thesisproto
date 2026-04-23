"""
Convert RDD2022 (dataset-ninja format) to YOLO format.
Filters for pothole class ONLY.
"""
import json
import os
import glob
import shutil
import random
from pathlib import Path


def convert_rdd2022_ninja_to_yolo(src_dir, output_dir):
    """Convert dataset-ninja Supervisely JSON annotations to YOLO format, pothole only."""
    
    src_dir = os.path.expanduser(src_dir)
    output_dir = os.path.expanduser(output_dir)
    
    print("=" * 60)
    print("🔄 RDD2022 → YOLO Conversion (Pothole Only)")
    print("=" * 60)
    
    # Collect all images with pothole annotations
    all_pairs = []  # (image_path, [(cx, cy, w, h), ...])
    
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
            
            # Filter for pothole objects only
            pothole_labels = []
            for obj in data.get('objects', []):
                if obj.get('classTitle') != 'pothole':
                    continue
                
                if obj.get('geometryType') != 'rectangle':
                    continue
                
                points = obj.get('points', {}).get('exterior', [])
                if len(points) != 2:
                    continue
                
                x1, y1 = points[0]
                x2, y2 = points[1]
                
                # Convert to YOLO format (normalized center x, y, width, height)
                cx = ((x1 + x2) / 2.0) / img_w
                cy = ((y1 + y2) / 2.0) / img_h
                w = abs(x2 - x1) / img_w
                h = abs(y2 - y1) / img_h
                
                # Clamp to [0, 1]
                cx = max(0, min(1, cx))
                cy = max(0, min(1, cy))
                w = max(0.001, min(1, w))
                h = max(0.001, min(1, h))
                
                pothole_labels.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
            
            if pothole_labels:
                # Get corresponding image filename
                img_name = os.path.basename(ann_file).replace('.json', '')
                img_path = os.path.join(img_dir, img_name)
                
                if os.path.exists(img_path):
                    all_pairs.append((img_path, pothole_labels))
    
    print(f"\n📊 Total images with potholes: {len(all_pairs)}")
    total_bboxes = sum(len(labels) for _, labels in all_pairs)
    print(f"📊 Total pothole bounding boxes: {total_bboxes}")
    
    if not all_pairs:
        print("❌ No pothole data found!")
        return
    
    # Shuffle and split: 80% train, 15% val, 5% test
    random.seed(42)
    random.shuffle(all_pairs)
    
    n = len(all_pairs)
    train_end = int(0.80 * n)
    val_end = int(0.95 * n)
    
    splits = {
        'train': all_pairs[:train_end],
        'val': all_pairs[train_end:val_end],
        'test': all_pairs[val_end:]
    }
    
    # Create output directories and copy files
    for split_name, pairs in splits.items():
        img_out = os.path.join(output_dir, split_name, 'images')
        lbl_out = os.path.join(output_dir, split_name, 'labels')
        os.makedirs(img_out, exist_ok=True)
        os.makedirs(lbl_out, exist_ok=True)
        
        for idx, (img_path, labels) in enumerate(pairs):
            ext = os.path.splitext(img_path)[1]
            new_name = f"pothole_{idx:05d}"
            
            # Copy image
            shutil.copy2(img_path, os.path.join(img_out, new_name + ext))
            
            # Write YOLO label
            with open(os.path.join(lbl_out, new_name + '.txt'), 'w') as f:
                f.write('\n'.join(labels))
        
        print(f"   {split_name}: {len(pairs)} images")
    
    # Create data.yaml
    yaml_content = f"""# Pothole Detection Dataset (RDD2022 - D40 class only)
# Filtered from {len(all_pairs)} images with {total_bboxes} pothole annotations

path: {os.path.abspath(output_dir)}
train: train/images
val: val/images
test: test/images

nc: 1

names:
  0: pothole
"""
    yaml_path = os.path.join(output_dir, 'data.yaml')
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    # Also copy to ml directory
    ml_yaml = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.yaml')
    with open(ml_yaml, 'w') as f:
        f.write(yaml_content)
    
    print(f"\n✅ Dataset ready at: {output_dir}")
    print(f"📝 data.yaml saved to: {yaml_path}")
    print(f"\n🚀 Next: Run training with:")
    print(f"   python3 train_model.py --data {yaml_path} --epochs 50")


if __name__ == '__main__':
    convert_rdd2022_ninja_to_yolo(
        src_dir='~/dataset-ninja/rdd2022',
        output_dir='./datasets/pothole_rdd2022'
    )

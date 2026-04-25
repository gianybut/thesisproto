import sys
import codecs
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
import os
import requests
import zipfile
import shutil
import glob
import xml.etree.ElementTree as ET
import random
from tqdm import tqdm

DOWNLOAD_URL = "https://ndownloader.figshare.com/files/38030910"
ZIP_PATH = "RDD2022.zip"
EXTRACT_DIR = "RDD2022_raw"
OUTPUT_DIR = "pothole_dataset"
TARGET_CLASS = "D40"
RANDOM_SEED = 42

TRAIN_RATIO = 0.80
VAL_RATIO = 0.15
COUNTRIES = ["China_Drone", "China_MotorBike", "Czech", "India", "Japan", "Norway", "United_States"]

def download_file(url, output_path):
    if os.path.exists(output_path):
        print(f"✅ {output_path} already exists. Skipping download.")
        return
    print(f"⬇️ Downloading {output_path} (~13GB). This will take a while...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as file, tqdm(
        desc=output_path,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024*1024):
            size = file.write(data)
            bar.update(size)
    print("✅ Download complete!")

def extract_zip(zip_path, extract_to):
    print(f"📦 Extracting {zip_path} to {extract_to}...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Avoid nested progress bars spamming logs
        for member in tqdm(zf.infolist(), desc='Extracting'):
            try:
                zf.extract(member, extract_to)
            except zipfile.error as e:
                pass
    print(f"✅ Extraction of {zip_path} complete!")

def extract_nested_zips(directory):
    nested_zips = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.zip'):
                nested_zips.append(os.path.join(root, f))
    
    if nested_zips:
        print(f"📦 Found {len(nested_zips)} nested zip files to extract.")
        for zf in nested_zips:
            zf_dir = os.path.dirname(zf)
            extract_zip(zf, zf_dir)
            os.remove(zf)
            
def parse_voc_xml(xml_path, target_class="D40"):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        size = root.find('size')
        if size is None: return []

        img_w = int(size.find('width').text)
        img_h = int(size.find('height').text)

        if img_w == 0 or img_h == 0: return []

        labels = []
        for obj in root.findall('object'):
            name = obj.find('name').text.strip()
            if name != target_class: continue

            bbox = obj.find('bndbox')
            xmin = float(bbox.find('xmin').text)
            ymin = float(bbox.find('ymin').text)
            xmax = float(bbox.find('xmax').text)
            ymax = float(bbox.find('ymax').text)

            cx = ((xmin + xmax) / 2.0) / img_w
            cy = ((ymin + ymax) / 2.0) / img_h
            w = (xmax - xmin) / img_w
            h = (ymax - ymin) / img_h

            cx = max(0.0, min(1.0, cx))
            cy = max(0.0, min(1.0, cy))
            w = max(0.001, min(1.0, w))
            h = max(0.001, min(1.0, h))

            labels.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        return labels
    except Exception:
        return []

def prepare_yolo_dataset():
    rdd_root = None
    for root_dir, dirs, files in os.walk(EXTRACT_DIR):
        matching = [d for d in dirs if d in COUNTRIES]
        if matching:
            rdd_root = root_dir
            break
            
    if rdd_root is None:
        raise RuntimeError("Could not locate country directories. Did extraction fail?")

    print("🔍 Filtering for D40 (pothole)...")
    all_pairs = []
    for country in COUNTRIES:
        country_dir = os.path.join(rdd_root, country)
        if not os.path.exists(country_dir):
            print(f"   ⚠️ {country} not found, skipping")
            continue

        for split in ['train']:
            img_dir = os.path.join(country_dir, split, 'images')
            xml_dir = os.path.join(country_dir, split, 'annotations', 'xmls')
            
            # fallback
            if not os.path.exists(xml_dir): xml_dir = os.path.join(country_dir, split, 'annotations')

            if not os.path.exists(xml_dir) or not os.path.exists(img_dir):
                continue
                
            xml_files = glob.glob(os.path.join(xml_dir, '*.xml'))
            for xml_file in xml_files:
                labels = parse_voc_xml(xml_file, TARGET_CLASS)
                if labels:
                    img_stem = os.path.splitext(os.path.basename(xml_file))[0]
                    img_path = None
                    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                        candidate = os.path.join(img_dir, img_stem + ext)
                        if os.path.exists(candidate):
                            img_path = candidate
                            break

                    if img_path:
                        all_pairs.append((img_path, labels))
                        
    total_images = len(all_pairs)
    total_bboxes = sum(len(labels) for _, labels in all_pairs)
    print(f"📊 Found {total_images} images with {total_bboxes} pothole bounding boxes")

    if total_images == 0:
        raise RuntimeError("No pothole annotations found!")

    random.seed(RANDOM_SEED)
    random.shuffle(all_pairs)
    
    n = len(all_pairs)
    splits = {
        'train': all_pairs[:int(TRAIN_RATIO * n)],
        'val': all_pairs[int(TRAIN_RATIO * n):int((TRAIN_RATIO + VAL_RATIO) * n)],
        'test': all_pairs[int((TRAIN_RATIO + VAL_RATIO) * n):],
    }

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    for split_name, pairs in splits.items():
        img_out = os.path.join(OUTPUT_DIR, split_name, 'images')
        lbl_out = os.path.join(OUTPUT_DIR, split_name, 'labels')
        os.makedirs(img_out, exist_ok=True)
        os.makedirs(lbl_out, exist_ok=True)

        print(f"   Writing {split_name} split...")
        for idx, (img_path, labels) in enumerate(tqdm(pairs, desc=split_name)):
            ext = os.path.splitext(img_path)[1]
            new_name = f"pothole_{idx:05d}"
            
            shutil.copy2(img_path, os.path.join(img_out, new_name + ext))
            with open(os.path.join(lbl_out, new_name + '.txt'), 'w') as f:
                f.write('\n'.join(labels))

    abs_out_path = os.path.abspath(OUTPUT_DIR).replace('\\', '/')
    yaml_content = f"""# Pothole Detection Dataset
path: {abs_out_path}
train: train/images
val: val/images
test: test/images

nc: 1

names:
  0: pothole
"""
    yaml_path = os.path.join(OUTPUT_DIR, 'data.yaml')
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    print(f"\\n✅ Dataset ready at: {OUTPUT_DIR}")
    print(f"📝 data.yaml at: {yaml_path}")


if __name__ == "__main__":
    if not os.path.exists(EXTRACT_DIR) or len(os.listdir(EXTRACT_DIR)) == 0:
        download_file(DOWNLOAD_URL, ZIP_PATH)
        os.makedirs(EXTRACT_DIR, exist_ok=True)
        extract_zip(ZIP_PATH, EXTRACT_DIR)
        print("🗑️ Removing main zip to free up space...")
        os.remove(ZIP_PATH)
        
    extract_nested_zips(EXTRACT_DIR)
    prepare_yolo_dataset()

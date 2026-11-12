"""Build a YOLO classification dataset from reviewed YOLO detection labels.

Each reviewed bounding box becomes one crop. The source lists are kept explicit so train,
validation, and test frames retain the team's existing split and no frame is silently moved
between evaluation sets.
"""

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

import cv2


CLASSES = ('D00', 'D10', 'D20', 'D40')


def label_path(image_path):
    parts = list(image_path.parts)
    parts[parts.index('images')] = 'labels'
    return Path(*parts).with_suffix('.txt')


def read_list(path):
    return [Path(line.strip()) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def build(source_root, output_root, lists, padding):
    if output_root.exists():
        shutil.rmtree(output_root)

    counts = {split: Counter() for split in lists}
    for split, list_path in lists.items():
        for image_path in read_list(list_path):
            image = cv2.imread(str(image_path))
            if image is None:
                raise RuntimeError(f'Could not read source image: {image_path}')
            height, width = image.shape[:2]
            labels = label_path(image_path)
            if not labels.exists():
                raise RuntimeError(f'Missing label file: {labels}')

            for index, line in enumerate(labels.read_text(encoding='utf-8').splitlines()):
                values = line.split()
                if len(values) != 5:
                    raise RuntimeError(f'Invalid YOLO label in {labels}: {line}')
                class_id, cx, cy, box_w, box_h = map(float, values)
                class_id = int(class_id)
                if class_id < 0 or class_id >= len(CLASSES):
                    raise RuntimeError(f'Unknown class id {class_id} in {labels}')

                x1 = max(0, int((cx - box_w / 2 - padding * box_w) * width))
                y1 = max(0, int((cy - box_h / 2 - padding * box_h) * height))
                x2 = min(width, int((cx + box_w / 2 + padding * box_w) * width))
                y2 = min(height, int((cy + box_h / 2 + padding * box_h) * height))
                crop = image[y1:y2, x1:x2]
                if crop.size == 0:
                    raise RuntimeError(f'Empty crop for {labels}: {line}')

                destination_dir = output_root / split / CLASSES[class_id]
                destination_dir.mkdir(parents=True, exist_ok=True)
                destination = destination_dir / f'{image_path.stem}__b{index}.jpg'
                if not cv2.imwrite(str(destination), crop):
                    raise RuntimeError(f'Could not write crop: {destination}')
                counts[split][CLASSES[class_id]] += 1

    metadata = {
        'source_root': str(source_root),
        'padding': padding,
        'lists': {key: str(value) for key, value in lists.items()},
        'counts': {split: dict(counter) for split, counter in counts.items()},
    }
    (output_root / 'dataset_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    for split, counter in counts.items():
        print(split, dict(counter), 'total', sum(counter.values()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build reviewed classification crops')
    parser.add_argument('--source-root', type=Path, default=Path('data/local/yolo_nz'))
    parser.add_argument('--output', type=Path, default=Path('data/local/classification'))
    parser.add_argument('--padding', type=float, default=0.25,
                        help='Extra fraction of the box width/height kept as context')
    args = parser.parse_args()
    root = args.source_root
    build(
        root,
        args.output,
        {
            'train': root / 'local_train.txt',
            'val': root / 'val_reviewed.txt',
            'test': root / 'test.txt',
        },
        args.padding,
    )

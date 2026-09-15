"""
YOLOv8 Training Script for Road Damage Detection (four CRDDC 2022 classes)

Defaults match the thesis (Sec 3.2.1): YOLOv8m, 100 epochs, batch 16, imgsz 640, early stopping
with patience 20. Reports per-class AP@50 so the Chapter IV table can be filled directly.

Usage:
    python train_model.py --data ./datasets/pothole_dataset/data.yaml
    python train_model.py --model yolov8s --epochs 100          # smaller/faster ablation (C5)
    python train_model.py --resume                              # continue from last.pt

On Google Colab / Kaggle (free T4 — training on CPU is not realistic, see review C2):
    !pip install ultralytics
    !python train_model.py --data /content/pothole_dataset/data.yaml --model yolov8m --epochs 100
    then download ml/models/best.pt and drop it into the repo.
"""

import os
import sys
import argparse
from pathlib import Path
from ultralytics import YOLO


def train_model(
    data_yaml='./datasets/pothole_dataset/data.yaml',
    model_size='yolov8m',
    epochs=100,
    batch_size=16,
    img_size=640,
    patience=20,
    target_map50=0.50,
    resume=False,
    project_name='pothole_detection',
    experiment_name='train'
):
    """
    Train YOLOv8 for four-class road damage detection.

    Args:
        data_yaml: Path to dataset configuration file
        model_size: YOLOv8 model variant (yolov8n, yolov8s, yolov8m, yolov8l, yolov8x)
        epochs: Maximum training epochs (early stopping usually ends sooner)
        batch_size: Training batch size
        img_size: Input image size
        patience: Stop when val mAP has not improved for this many epochs (review C4)
        target_map50: A-priori acceptance bar for mAP@50 (review C19; thesis: ≥ 0.50 local)
        resume: Resume from last checkpoint
        project_name: Project directory name for saving results
        experiment_name: Experiment name within project
    """

    print("=" * 60)
    print("🚀 Road Damage Detection - YOLOv8 Training")
    print("=" * 60)

    # Validate data.yaml exists
    if not os.path.exists(data_yaml):
        print(f"❌ Dataset config not found: {data_yaml}")
        print("   Run dataset_prep.py first to prepare the dataset.")
        sys.exit(1)

    # Load model
    if resume:
        # Resume from last checkpoint
        last_pt = Path(project_name) / experiment_name / 'weights' / 'last.pt'
        if last_pt.exists():
            print(f"📦 Resuming training from: {last_pt}")
            model = YOLO(str(last_pt))
        else:
            print(f"⚠️  No checkpoint found at {last_pt}. Starting fresh.")
            model = YOLO(f'{model_size}.pt')
    else:
        print(f"📦 Loading pretrained {model_size} model...")
        model = YOLO(f'{model_size}.pt')

    print(f"📊 Dataset config: {data_yaml}")
    print(f"🔧 Epochs: {epochs} (patience {patience}), Batch: {batch_size}, Image size: {img_size}")
    print()

    # Train the model
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        project=project_name,
        name=experiment_name,
        exist_ok=True,

        # Optimization
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,

        # Data augmentation (key for good accuracy)
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        perspective=0.0001,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.15,

        # Other settings
        patience=patience,
        save=True,
        save_period=10,
        val=True,
        plots=True,
        verbose=True,
    )

    print()
    print("=" * 60)
    print("📊 Training Results")
    print("=" * 60)

    # Copy best model to our models directory
    dest_path = Path(__file__).parent / 'models' / 'best.pt'
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Search multiple possible locations for best.pt
    import shutil
    possible_paths = [
        Path(project_name) / experiment_name / 'weights' / 'best.pt',
        Path('runs') / 'detect' / project_name / experiment_name / 'weights' / 'best.pt',
        Path('runs') / 'detect' / experiment_name / 'weights' / 'best.pt',
    ]
    best_found = False
    for best_pt in possible_paths:
        if best_pt.exists():
            shutil.copy2(best_pt, dest_path)
            print(f"✅ Best model saved to: {dest_path}")
            best_found = True
            break
    if not best_found:
        print(f"⚠️  Best model not found. Searched: {[str(p) for p in possible_paths]}")

    # Run validation
    print()
    print("🔍 Running validation...")
    val_results = model.val(data=data_yaml)

    p, r = float(val_results.box.mp), float(val_results.box.mr)
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0

    print()
    print("=" * 60)
    print("📊 Validation Metrics (overall)")
    print("=" * 60)
    print(f"   mAP@50:      {val_results.box.map50:.4f}")
    print(f"   mAP@50-95:   {val_results.box.map:.4f}")
    print(f"   Precision:   {p:.4f}")
    print(f"   Recall:      {r:.4f}")
    print(f"   F1 (from P/R above, not hand-edited): {f1:.4f}")

    # Per-class AP@50 — the rows of the Chapter IV per-class table
    try:
        names = model.names
        ap50 = val_results.box.ap50
        print("-" * 60)
        print("   Per-class AP@50:")
        for i, ap in enumerate(ap50):
            print(f"     {names.get(i, i):<20} {ap:.4f}")
    except Exception:
        pass
    print("=" * 60)

    if val_results.box.map50 >= target_map50:
        print(f"🎉 Acceptance bar met: mAP@50 {val_results.box.map50:.3f} ≥ {target_map50}")
    else:
        print(f"⚠️  mAP@50 {val_results.box.map50:.3f} is below the {target_map50} acceptance bar.")
        print("   Consider more real data per class, more epochs, or the yolov8s/m ablation.")

    return model, val_results


def export_model(model_path, format='onnx'):
    """Export trained model to different formats."""
    print(f"📦 Exporting model to {format} format...")
    model = YOLO(model_path)
    model.export(format=format)
    print(f"✅ Model exported successfully")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train YOLOv8 for four-class road damage detection')
    parser.add_argument('--data', type=str, default='./datasets/pothole_dataset/data.yaml',
                        help='Path to data.yaml')
    parser.add_argument('--model', type=str, default='yolov8m',
                        help='YOLOv8 model size (yolov8n/s/m/l/x); thesis uses yolov8m')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Maximum epochs (early stopping applies)')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size')
    parser.add_argument('--img-size', type=int, default=640,
                        help='Input image size')
    parser.add_argument('--patience', type=int, default=20,
                        help='Early-stopping patience in epochs')
    parser.add_argument('--target-map', type=float, default=0.50,
                        help='Acceptance bar for mAP@50 (thesis: 0.50 on the local test subset)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume training from last checkpoint')
    parser.add_argument('--export', type=str, default=None,
                        help='Export ml/models/best.pt to this format (onnx, tflite, ...)')

    args = parser.parse_args()

    if args.export:
        export_model(str(Path(__file__).parent / 'models' / 'best.pt'), args.export)
    else:
        train_model(
            data_yaml=args.data,
            model_size=args.model,
            epochs=args.epochs,
            batch_size=args.batch,
            img_size=args.img_size,
            patience=args.patience,
            target_map50=args.target_map,
            resume=args.resume
        )

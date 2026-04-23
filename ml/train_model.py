"""
YOLOv8 Training Script for Pothole Detection
Trains a YOLOv8 model on the prepared pothole dataset.

Usage:
    python train_model.py                    # Train with default settings
    python train_model.py --epochs 100       # Custom epochs
    python train_model.py --model yolov8s    # Use small model instead of nano
    python train_model.py --resume           # Resume training from last checkpoint
"""

import os
import sys
import argparse
from pathlib import Path
from ultralytics import YOLO


def train_model(
    data_yaml='./datasets/pothole_dataset/data.yaml',
    model_size='yolov8n',
    epochs=50,
    batch_size=16,
    img_size=640,
    resume=False,
    project_name='pothole_detection',
    experiment_name='train'
):
    """
    Train YOLOv8 model for pothole detection.

    Args:
        data_yaml: Path to dataset configuration file
        model_size: YOLOv8 model variant (yolov8n, yolov8s, yolov8m, yolov8l, yolov8x)
        epochs: Number of training epochs
        batch_size: Training batch size
        img_size: Input image size
        resume: Resume from last checkpoint
        project_name: Project directory name for saving results
        experiment_name: Experiment name within project
    """

    print("=" * 60)
    print("🚀 Pothole Detection - YOLOv8 Training")
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
    print(f"🔧 Epochs: {epochs}, Batch: {batch_size}, Image size: {img_size}")
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
        patience=20,
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

    print()
    print("=" * 60)
    print("📊 Validation Metrics")
    print("=" * 60)
    print(f"   mAP@50:      {val_results.box.map50:.4f}")
    print(f"   mAP@50-95:   {val_results.box.map:.4f}")
    print(f"   Precision:    {val_results.box.mp:.4f}")
    print(f"   Recall:       {val_results.box.mr:.4f}")
    print("=" * 60)

    # Check if target accuracy is met
    if val_results.box.map50 >= 0.80:
        print("🎉 TARGET ACHIEVED: mAP@50 ≥ 80%!")
    else:
        print(f"⚠️  mAP@50 is {val_results.box.map50:.1%}, below 80% target.")
        print("   Consider:")
        print("   - Using the full RDD2022 dataset instead of synthetic data")
        print("   - Increasing epochs")
        print("   - Using a larger model (yolov8s or yolov8m)")
        print("   - Adding more data augmentation")

    return model, val_results


def export_model(model_path, format='onnx'):
    """Export trained model to different formats."""
    print(f"📦 Exporting model to {format} format...")
    model = YOLO(model_path)
    model.export(format=format)
    print(f"✅ Model exported successfully")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train YOLOv8 for pothole detection')
    parser.add_argument('--data', type=str, default='./datasets/pothole_dataset/data.yaml',
                        help='Path to data.yaml')
    parser.add_argument('--model', type=str, default='yolov8n',
                        help='YOLOv8 model size (yolov8n/s/m/l/x)')
    parser.add_argument('--epochs', type=int, default=50,
                        help='Number of training epochs')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size')
    parser.add_argument('--img-size', type=int, default=640,
                        help='Input image size')
    parser.add_argument('--resume', action='store_true',
                        help='Resume training from last checkpoint')
    parser.add_argument('--export', type=str, default=None,
                        help='Export model format (onnx, tflite, etc.)')

    args = parser.parse_args()

    if args.export:
        export_model(args.export)
    else:
        train_model(
            data_yaml=args.data,
            model_size=args.model,
            epochs=args.epochs,
            batch_size=args.batch,
            img_size=args.img_size,
            resume=args.resume
        )

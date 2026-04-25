from ultralytics import YOLO
import time
import os

if __name__ == '__main__':
    # Verify dataset exists before starting
    if not os.path.exists('pothole_dataset/data.yaml'):
        print("❌ Dataset not found! Please run 'python download_rdd2022.py' first.")
        exit(1)

    print("=" * 60)
    print("🏋️ STARTING LOCAL TRAINING — YOLOv8m POTHOLE DETECTION (RTX 4060)")
    print("=" * 60)
    
    # Load pretrained YOLOv8m
    model = YOLO('yolov8m.pt')
    
    start_time = time.time()
    
    results = model.train(
        data='pothole_dataset/data.yaml',
        
        # --- Core settings ---
        epochs=150,
        batch=4,                  # ⭐ Reduced from 8 to 4 to fit in RTX 4060's 8GB VRAM
        imgsz=1024,               # 1024x1024 resolution
        project='pothole_training',
        name='yolov8m_1024_local',
        exist_ok=True,
        workers=4,                # Number of dataloader workers (Windows handles 4 well via multiprocessing)
        
        # --- Optimizer ---
        optimizer='auto',
        lr0=0.01,
        lrf=0.1,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=5,
        warmup_momentum=0.8,
        cos_lr=True,
        
        # --- Data augmentation ---
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=15.0,
        translate=0.2,
        scale=0.5,
        shear=2.0,
        perspective=0.0001,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.15,
        copy_paste=0.1,
        close_mosaic=20,
        
        # --- Regularization ---
        label_smoothing=0.1,
        
        # --- Training control ---
        patience=30,
        save=True,
        save_period=25,
        val=True,
        plots=True,
        verbose=True,
    )
    
    elapsed = time.time() - start_time
    print(f"\\n⏱️ Training completed in {elapsed/3600:.1f} hours")
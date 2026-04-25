"""Evaluate the trained YOLOv8 model."""
from ultralytics import YOLO
import os

def evaluate_model(model_path='models/best.pt', data_path='../pothole_dataset/data.yaml'):
    """
    Evaluates a trained YOLO model on the validation dataset.
    
    Args:
        model_path (str): Path to the trained .pt file.
        data_path (str): Path to the dataset data.yaml file.
    """
    print("=" * 60)
    print(f"📊 EVALUATING MODEL: {model_path}")
    print("=" * 60)
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found at {model_path}")
        return
        
    if not os.path.exists(data_path):
        print(f"❌ Dataset YAML not found at {data_path}")
        return

    # Load the trained model
    print("📦 Loading model...")
    model = YOLO(model_path)
    
    # Run validation
    print("\n⏳ Running validation... This may take a few minutes depending on your hardware.")
    # You can adjust batch size if you run out of memory
    metrics = model.val(data=data_path, split='val', batch=4, plots=True)
    
    print("\n" + "=" * 60)
    print("🏆 EVALUATION RESULTS")
    print("=" * 60)
    
    # Extract metrics
    map50 = metrics.box.map50
    map50_95 = metrics.box.map
    precision = metrics.box.mp
    recall = metrics.box.mr
    
    # Calculate F1 Score safely
    f1_score = 0
    if precision + recall > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
        
    print(f"📌 mAP@50:    {map50:.4f} ({map50*100:.1f}%)")
    print(f"📌 mAP@50-95: {map50_95:.4f} ({map50_95*100:.1f}%)")
    print(f"📌 Precision: {precision:.4f} ({precision*100:.1f}%)")
    print(f"📌 Recall:    {recall:.4f} ({recall*100:.1f}%)")
    print(f"📌 F1-Score:  {f1_score:.4f} ({f1_score*100:.1f}%)")
    
    print("\n📂 Detailed evaluation graphs (Confusion Matrix, PR Curve, F1 Curve)")
    print(f"   are automatically saved by YOLO in the 'runs/detect/val' directory.")
    print("=" * 60)

if __name__ == '__main__':
    # Adjust paths dynamically based on where the script is executed
    current_dir = os.getcwd()
    
    # If run from root directory (thesisproto)
    if 'thesisproto' in os.path.basename(current_dir) or os.path.exists('ml/models/best.pt'):
        model_p = 'ml/models/best.pt'
        data_p = 'pothole_dataset/data.yaml'
    # If run from ml directory
    elif 'ml' in os.path.basename(current_dir):
        model_p = 'models/best.pt'
        data_p = '../pothole_dataset/data.yaml'
    else:
        # Fallback defaults
        model_p = 'models/best.pt'
        data_p = 'pothole_dataset/data.yaml'
        
    evaluate_model(model_path=model_p, data_path=data_p)

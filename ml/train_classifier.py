"""Train the optional YOLO classification stage on reviewed damage crops.

The dataset must use Ultralytics' classification layout:

    data/local/classification/
      train/D00/*.jpg
      train/D10/*.jpg
      val/D00/*.jpg
      val/D10/*.jpg
      test/D00/*.jpg
      test/D10/*.jpg

Only reviewed detector crops should be placed in these folders. Classification accuracy is
reported separately from detection mAP@50.
"""

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO


def train(data, model_name, epochs, batch, imgsz, project, name, workers, deploy):
    data = Path(data)
    project = Path(project).resolve()
    if not (data / 'train').is_dir() or not (data / 'val').is_dir():
        raise SystemExit(f'Classification dataset must contain train/ and val/ folders: {data}')

    model = YOLO(model_name)
    model.train(
        data=str(data),
        task='classify',
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        project=project,
        name=name,
        exist_ok=True,
        workers=workers,
        patience=20,
        plots=True,
        verbose=True,
    )

    best = project / name / 'weights' / 'best.pt'
    if not best.exists():
        raise RuntimeError(f'Training completed but no classifier checkpoint was found at {best}')

    validation = model.val(data=str(data), split='val')
    top1 = float(getattr(validation, 'top1', 0.0))
    top5 = float(getattr(validation, 'top5', 0.0))
    print(f'Validation top-1 accuracy: {top1:.4f} ({top1:.1%})')
    print(f'Validation top-5 accuracy: {top5:.4f} ({top5:.1%})')
    if (data / 'test').is_dir():
        test_results = model.val(data=str(data), split='test', workers=workers)
        test_top1 = float(getattr(test_results, 'top1', 0.0))
        test_top5 = float(getattr(test_results, 'top5', 0.0))
        print(f'Test top-1 accuracy: {test_top1:.4f} ({test_top1:.1%})')
        print(f'Test top-5 accuracy: {test_top5:.4f} ({test_top5:.1%})')

    if deploy:
        destination = Path(__file__).parent / 'models' / 'classifier.pt'
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best, destination)
        print(f'Deployed classifier weights to {destination}')
        print('Set classifier.enabled=true in ml/models/model_config.json, then restart the backend.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train the optional YOLO road-damage classifier')
    parser.add_argument('--data', default='data/local/classification',
                        help='Classification dataset with train/val[/test] class folders')
    parser.add_argument('--model', default='yolov8n-cls.pt',
                        help='Ultralytics classification checkpoint')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch', type=int, default=32)
    parser.add_argument('--imgsz', type=int, default=224)
    parser.add_argument('--project', default='runs/classify')
    parser.add_argument('--name', default='road_damage')
    parser.add_argument('--workers', type=int, default=0,
                        help='Data-loader workers; 0 avoids intermittent OpenCV worker failures on Windows')
    parser.add_argument('--deploy', action='store_true',
                        help='Copy best.pt to ml/models/classifier.pt after validation')
    args = parser.parse_args()
    train(args.data, args.model, args.epochs, args.batch, args.imgsz,
          args.project, args.name, args.workers, args.deploy)

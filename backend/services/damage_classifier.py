"""Optional second-stage YOLO classifier for detected road-damage crops."""

import os

from services.video_processor import DAMAGE_CLASS_MAP


class ClassifierUnavailable(Exception):
    """The configured classifier cannot be loaded."""


def load_classifier(config):
    """Load the configured classifier, or return None when the feature is disabled."""
    settings = config.get('classifier') or {}
    if not settings.get('enabled'):
        return None

    from ultralytics import YOLO

    weights = settings.get('weights')
    if not weights:
        raise ClassifierUnavailable('The classifier is enabled but no weights are configured.')
    if not os.path.isabs(weights):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        weights = os.path.normpath(os.path.join(root, weights))
    if not os.path.exists(weights):
        raise ClassifierUnavailable(f'The configured classifier weights are missing: {weights}')

    print(f'📦 Loading damage classifier from: {weights}')
    return YOLO(weights)


def _classify_name(name, class_id, names):
    lowered = str(name).lower().strip()
    for key, (code, label) in DAMAGE_CLASS_MAP.items():
        if key in lowered:
            return code, label

    order = {
        0: ('D00', 'Longitudinal Crack'),
        1: ('D10', 'Transverse Crack'),
        2: ('D20', 'Alligator Crack'),
        3: ('D40', 'Pothole'),
    }
    if len(names) <= 4 and class_id in order:
        return order[class_id]
    return None


def classify_crop(model, frame, box, settings):
    """Return (code, label, confidence) for one detector box, or None if unusable."""
    x1, y1, x2, y2 = (int(round(v)) for v in box)
    height, width = frame.shape[:2]
    x1, x2 = max(0, min(x1, width - 1)), max(0, min(x2, width))
    y1, y2 = max(0, min(y1, height - 1)), max(0, min(y2, height))
    if x2 <= x1 or y2 <= y1:
        return None

    results = model(frame[y1:y2, x1:x2], verbose=False, imgsz=int(settings.get('imgsz', 224)))
    if not results or results[0].probs is None:
        return None

    result = results[0]
    class_id = int(result.probs.top1)
    confidence = float(result.probs.top1conf)
    names = result.names or model.names
    if isinstance(names, dict):
        class_name = names.get(class_id, '')
    else:
        class_name = names[class_id] if 0 <= class_id < len(names) else ''
    mapped = _classify_name(class_name, class_id, names)
    if not mapped or confidence < float(settings.get('conf_threshold', 0.0)):
        return None
    return mapped[0], mapped[1], confidence

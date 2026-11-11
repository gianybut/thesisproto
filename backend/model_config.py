"""Which detection model the system runs, and with which settings: ml/models/model_config.json.

    {"weights": "ml/models/<file>.pt", "conf_threshold": 0.15, "iou_threshold": 0.45, "imgsz": 1280,
     "class_names": ["D00", "D10", "D20", "D40"] | null, "run": "...", "data_snapshot": "...", ...}

Read once when the backend starts (restart it after a change). ml/local/deploy_model.py writes it and
keeps the version it replaced in model_config.previous.json for rollback. If the file is missing or
broken the defaults below apply (the demo placeholder at the settings the thesis cites).
"""

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(ROOT, 'ml', 'models', 'model_config.json')
DEFAULTS = {
    'weights': 'ml/models/rdd2022_pretrained.pt',
    'conf_threshold': 0.15,
    'iou_threshold': 0.45,
    'imgsz': 1280,
    'class_names': None,
    'run': 'placeholder',
    'data_snapshot': None,
    'deployed_at': None,
}


def load():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            cfg.update({k: v for k, v in json.load(f).items() if v is not None or k in ('class_names', 'data_snapshot')})
    except FileNotFoundError:
        print(f'⚠️  {CONFIG_PATH} not found: using the default model settings.')
    except (OSError, ValueError) as e:
        print(f'⚠️  {CONFIG_PATH} could not be read ({e}): using the default model settings.')
    return cfg


def weights_path(cfg=None):
    w = (cfg or load())['weights']
    return w if os.path.isabs(w) else os.path.normpath(os.path.join(ROOT, w))


def public_info(cfg=None):
    """What the About page may show about the deployed model."""
    cfg = cfg or load()
    weights = os.path.basename(cfg['weights'])
    return {k: cfg.get(k) for k in ('run', 'data_snapshot', 'deployed_at', 'conf_threshold', 'imgsz', 'class_names',
                                    'test_evaluated')} | \
           {'weights': weights, 'stand_in': weights in STAND_IN_WEIGHTS,
            'ensemble': [os.path.basename(m['weights']) for m in cfg.get('ensemble') or []]}


# Models that are not the team's own (the demo placeholder): the About page says so.
STAND_IN_WEIGHTS = {'rdd2022_pretrained.pt'}

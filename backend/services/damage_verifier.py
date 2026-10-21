"""AI check: a second, independent look at each damage the detector found.

The detector (YOLO) is trained to find road damage and nothing else, so anything that resembles
damage in its eyes becomes a "pothole": worn lane markings, a car door, the bus beside the lane,
the bonnet, a manhole cover. This check asks a general image model, CLIP (Radford et al., 2021),
whether the close-up looks more like road damage or like one of those other things. It needs no
training data of our own: it compares the picture with short descriptions (zero-shot).

It only advises. Each record stores the share of CLIP's answer that went to the road-damage
descriptions (Detection.ai_check_score, 0-1); below VERIFY_THRESHOLD the web app flags the record
"likely not road damage" for the system administrator, who decides. Nothing is deleted or hidden
by it, so human validation stays where Chapter 3 puts it.

Measured on 38 hand-labelled records of one 3.5-minute windshield survey (15 real damages, 23 false
detections; 11 unclear ones left out), with the settings below: real damage scored above false
detections in 94% of pairs (AUC 0.94); at the 0.6 threshold 14 of 15 real damages passed and 18
of 23 false detections were flagged. The crop size and threshold were chosen on that same survey,
so expect lower figures on others; check on a second survey before citing them. The larger CLIP
(ViT-L/14) did worse (AUC 0.83), as did tighter crops (AUC 0.84-0.85).

Runs offline once the model is on disk (ml/models/hf/, ~600 MB; fetched on first use or with
`python backend/services/damage_verifier.py --download`). Without it, or without the
`transformers` package, analysis carries on and records are left "not checked".
"""

import os
import sys
import threading

VERIFIER_MODEL = 'openai/clip-vit-base-patch16'
VERIFY_CROP = 3.0          # the crop is the damage box's larger side times this, square, around it
VERIFY_MIN_PX = 112        # but never smaller than this, so a hairline crack has road around it
VERIFY_THRESHOLD = 0.6     # ai_check_score below this = flagged "likely not road damage"

# What road damage looks like, and what the detector mistakes for it (seen on real surveys).
DAMAGE_PROMPTS = [
    'a pothole in an asphalt road', 'a crack in asphalt pavement', 'a damaged, broken road surface',
    'alligator cracking on a road', 'a patched pothole on a road',
]
OTHER_PROMPTS = [
    'white lane markings painted on a road', 'a pedestrian crossing painted on a road', 'a car',
    'a bus', 'a wall', 'a manhole cover', 'the white bonnet of a car', 'smooth asphalt road',
    'a concrete road barrier', 'a car tyre', 'a shadow on a road',
]

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'models', 'hf'))

_lock = threading.Lock()
_state = {'loaded': False, 'model': None, 'processor': None, 'text': None, 'problem': None}


def _load(allow_download=True):
    """Load CLIP once per server process. Returns None when the check cannot run (reason in problem())."""
    with _lock:
        if _state['loaded']:
            return _state['model']
        _state['loaded'] = True
        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor
        except ImportError:
            _state['problem'] = 'The AI check needs the "transformers" package: pip install -r requirements.txt'
            return None
        model = processor = None
        # The copy on disk first, so the server works without internet; download only if missing.
        # use_safetensors=False: this model's main revision ships pytorch_model.bin only, and asking
        # for safetensors fetches a second 570 MB copy from a conversion branch.
        for local_only in ((True, False) if allow_download else (True,)):
            try:
                model = CLIPModel.from_pretrained(VERIFIER_MODEL, cache_dir=CACHE_DIR, local_files_only=local_only,
                                                  use_safetensors=False).eval()
                processor = CLIPProcessor.from_pretrained(VERIFIER_MODEL, cache_dir=CACHE_DIR, local_files_only=local_only)
                break
            except Exception as e:  # not on disk, or no internet to fetch it
                _state['problem'] = (f'The AI check model ({VERIFIER_MODEL}) is not on this computer and could not be '
                                     f'downloaded ({type(e).__name__}). Run "python backend/services/damage_verifier.py '
                                     f'--download" once with internet.')
        if model is None:
            return None
        with torch.no_grad():
            prompts = [f'a photo of {p}' for p in DAMAGE_PROMPTS + OTHER_PROMPTS]
            text = model.get_text_features(**processor(text=prompts, return_tensors='pt', padding=True))
            _state['text'] = text / text.norm(dim=-1, keepdim=True)
        _state.update(model=model, processor=processor, problem=None)
        return model


def problem():
    """Why the check is not running, or None."""
    return _state['problem']


def _crop(frame_bgr, box):
    h, w = frame_bgr.shape[:2]
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    side = max(max(x2 - x1, y2 - y1) * VERIFY_CROP, VERIFY_MIN_PX)
    left, top = int(max(0, cx - side / 2)), int(max(0, cy - side / 2))
    right, bottom = int(min(w, cx + side / 2)), int(min(h, cy + side / 2))
    return frame_bgr[top:bottom, left:right]


def score(frame_bgr, box):
    """Share (0-1) of CLIP's answer that says road damage, for the damage in `box` (x1, y1, x2, y2)
    of a CLEAN frame: nothing drawn on it, since CLIP reads text and a "Pothole" label would vote.
    None when the check is not available."""
    model = _load()
    if model is None:
        return None
    import cv2
    import torch
    from PIL import Image
    crop = _crop(frame_bgr, box)
    if crop.size == 0:
        return None
    image = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    with torch.no_grad():
        v = model.get_image_features(**_state['processor'](images=image, return_tensors='pt'))
    v = v / v.norm(dim=-1, keepdim=True)
    p = (100 * v @ _state['text'].T).softmax(-1)[0]
    return round(float(p[:len(DAMAGE_PROMPTS)].sum()), 4)


def backfill():
    """Check records analysed before the AI check existed, from the clean frames of their original
    videos. Records are only given a score: nothing is re-detected, so damage an admin already
    deleted does not come back (as it would with "Analyse again"). Returns (checked, skipped)."""
    import cv2
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from app import create_app
    from models import db, Detection, Video
    from services.video_processor import open_upright

    app = create_app()
    checked = skipped = 0
    with app.app_context():
        if _load() is None:
            raise SystemExit(problem())
        rows = (Detection.query.filter(Detection.ai_check_score.is_(None), Detection.source_type == 'ai_detection')
                .order_by(Detection.video_id, Detection.frame_number).all())
        by_video = {}
        for d in rows:
            by_video.setdefault(d.video_id, []).append(d)
        for video_id, dets in by_video.items():
            video = Video.query.get(video_id)
            path = video and os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
            if not path or not os.path.exists(path):
                skipped += len(dets)
                print(f'Survey {video_id}: original video not on the server, {len(dets)} records left unchecked')
                continue
            # Frames are read in order, as the analysis numbered them (the first frame is 1).
            cap, rotate, _w, _h = open_upright(path)
            wanted = {}
            for d in dets:
                wanted.setdefault(d.frame_number, []).append(d)
            frame_number = 0
            while wanted:
                ok, frame = cap.read()
                if not ok:
                    break
                frame_number += 1
                if frame_number not in wanted:
                    continue
                if rotate is not None:
                    frame = cv2.rotate(frame, rotate)
                for d in wanted.pop(frame_number):
                    d.ai_check_score = score(frame, (d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2))
                    checked += 1
            cap.release()
            skipped += sum(len(v) for v in wanted.values())
            db.session.commit()
            print(f'Survey {video_id}: checked {len(dets) - sum(len(v) for v in wanted.values())} records')
    return checked, skipped


if __name__ == '__main__':
    # python backend/services/damage_verifier.py --download   fetch the model once (needs internet)
    # python backend/services/damage_verifier.py --backfill   check records from before the AI check
    if '--download' in sys.argv:
        ok = _load(allow_download=True) is not None
        print(f'AI check model ready in {CACHE_DIR}' if ok else problem())
        sys.exit(0 if ok else 1)
    if '--backfill' in sys.argv:
        done, left = backfill()
        print(f'AI check: {done} records checked, {left} left unchecked')
        sys.exit(0)
    print(__doc__)

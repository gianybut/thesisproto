"""Follow each road damage across the analysed frames so it is recorded once.

A pothole seen from a moving vehicle is detected in several consecutive analysed frames: small
and near the top of the picture at first, larger and lower as the vehicle approaches, often with
rising confidence (20% far away, 50% close up). Each sighting used to be its own record. Here the
sightings are joined into one track, and a track becomes one record when the damage leaves the
view, using its best sighting (highest confidence): that frame's box, snapshot, time and position.

First, within one frame, a box lying mostly (TRACK_NESTED share of its area) inside another box is
the same damage boxed twice (a whole patch and a part of it, or two classes on one spot, which the
model's per-class overlap filter keeps); only the more confident box is kept.

Matching, per analysed frame (greedy, each box and track used at most once):
  1. a box that overlaps a track's last box by at least TRACK_MIN_IOU, best overlap first;
  2. otherwise a box whose centre lies in the area the damage can move to before the next
     analysed frame, nearest centre first. With s = the larger side of the last box, that area is
     the last box widened by s on each side, raised by s/2 and lowered by 3s. Things on the road
     move down the picture as the vehicle drives towards them, and fast: a 0.5 m pothole at
     30 km/h with 5 analysed frames a second moves about three times its own box height between
     frames, at any distance (the vehicle covers 1.7 m while the pothole is 0.5 m long). Damage
     further up the road sits above the box, outside this area, so it is not merged in.
A track that is not seen for TRACK_MAX_GAP_S seconds is finished. The kind of damage is taken
from the best sighting, since the model can call the same pothole an alligator crack in one frame.

Pure Python with no OpenCV import, so it can be tested on its own (see __main__ below).
"""

TRACK_MIN_IOU = 0.15      # overlap that counts as the same damage
TRACK_MAX_GAP_S = 1.0     # unseen this long = left the view (or was a one-off), so it is finished
TRACK_NESTED = 0.5        # share of a box inside another box in the same frame = the same damage


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def _drop_nested(sightings):
    """Keep only the most confident of boxes that lie mostly inside one another (same frame)."""
    kept = []
    for s in sorted(sightings, key=lambda x: x['conf'], reverse=True):
        b = s['box']
        area = (b[2] - b[0]) * (b[3] - b[1])
        nested = False
        for k in kept:
            kb = k['box']
            ix = max(0.0, min(b[2], kb[2]) - max(b[0], kb[0]))
            iy = max(0.0, min(b[3], kb[3]) - max(b[1], kb[1]))
            k_area = (kb[2] - kb[0]) * (kb[3] - kb[1])
            smaller = min(area, k_area)
            if smaller > 0 and ix * iy / smaller >= TRACK_NESTED:
                nested = True
                break
        if not nested:
            kept.append(s)
    return kept


def _centre(b):
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2


def _reach(b):
    """Where a damage in box b can be at the next analysed frame (see module docstring)."""
    side = max(b[2] - b[0], b[3] - b[1])
    return b[0] - side, b[1] - 0.5 * side, b[2] + side, b[3] + 3 * side


class Track:
    def __init__(self, track_id, sighting, image):
        self.id = track_id
        self.box = sighting['box']
        self.last_frame = sighting['frame']
        self.sightings = 1
        self.best = dict(sighting)
        self.best_image = image.copy() if image is not None else None

    def add(self, sighting, image):
        self.box = sighting['box']
        self.last_frame = sighting['frame']
        self.sightings += 1
        if sighting['conf'] > self.best['conf']:
            self.best = dict(sighting)
            self.best_image = image.copy() if image is not None else None


class DamageTracker:
    """Feed it each analysed frame's detections; it hands back finished tracks.

    A sighting is a dict with: box (x1, y1, x2, y2), conf, frame, and any other fields to carry
    through to the record (damage code, label, colour). Images are only copied when they become
    a track's best sighting.
    """

    def __init__(self, fps, max_gap_s=TRACK_MAX_GAP_S, min_iou=TRACK_MIN_IOU):
        self.max_gap_frames = max(1, int(round(fps * max_gap_s)))
        self.min_iou = min_iou
        self.tracks = []
        self._next_id = 1

    def update(self, frame_number, sightings, image=None):
        sightings = _drop_nested(sightings)
        finished = [t for t in self.tracks if frame_number - t.last_frame > self.max_gap_frames]
        self.tracks = [t for t in self.tracks if t not in finished]

        pairs = []   # (rank, score, track index, sighting index); higher is better
        for ti, t in enumerate(self.tracks):
            reach = _reach(t.box)
            tcx, tcy = _centre(t.box)
            diag = ((t.box[2] - t.box[0]) ** 2 + (t.box[3] - t.box[1]) ** 2) ** 0.5 or 1.0
            for si, s in enumerate(sightings):
                overlap = _iou(t.box, s['box'])
                if overlap >= self.min_iou:
                    pairs.append((1, overlap, ti, si))
                    continue
                cx, cy = _centre(s['box'])
                if reach[0] <= cx <= reach[2] and reach[1] <= cy <= reach[3]:
                    dist = ((cx - tcx) ** 2 + (cy - tcy) ** 2) ** 0.5
                    pairs.append((0, -dist / diag, ti, si))

        used_t, used_s = set(), set()
        for _rank, _score, ti, si in sorted(pairs, reverse=True):
            if ti in used_t or si in used_s:
                continue
            used_t.add(ti)
            used_s.add(si)
            self.tracks[ti].add(sightings[si], image)

        for si, s in enumerate(sightings):
            if si not in used_s:
                self.tracks.append(Track(self._next_id, s, image))
                self._next_id += 1

        return finished

    def finish_all(self):
        finished, self.tracks = self.tracks, []
        return finished


if __name__ == '__main__':
    # Self-check: python services/damage_tracker.py
    def s(frame, box, conf, code='D40'):
        return {'frame': frame, 'box': box, 'conf': conf, 'code': code}

    def run(frames, fps=30):
        tr, out = DamageTracker(fps), []
        for f, dets in frames:
            out += tr.update(f, dets)
        return out + tr.finish_all()

    # One pothole approaching: moves down 120 px and grows each analysed frame (every 6th frame
    # at 30 fps), confidence 20% -> 50%. The old 100 px grid rule made a new record every frame.
    approach = [(6 * i, [s(6 * i, (900 - 10 * i, 500 + 120 * i, 960 + 20 * i, 540 + 140 * i), c)])
                for i, c in enumerate([0.20, 0.28, 0.35, 0.50, 0.42])]
    t = run(approach)
    assert len(t) == 1 and t[0].best['conf'] == 0.50 and t[0].sightings == 5, t

    # A second pothole further up the road (above the first) stays its own record.
    ahead = [(6 * i, [s(6 * i, (900, 700 + 150 * i, 980, 750 + 170 * i), 0.4),
                      s(6 * i, (920, 420 + 40 * i, 950, 440 + 45 * i), 0.2)]) for i in range(3)]
    assert len(run(ahead)) == 2

    # Two potholes side by side in the same frames stay two records.
    pair = [(6 * i, [s(6 * i, (300, 600 + 60 * i, 380, 650 + 60 * i), 0.3),
                     s(6 * i, (1400, 600 + 60 * i, 1480, 650 + 60 * i), 0.4)]) for i in range(4)]
    assert len(run(pair)) == 2

    # The same spot seen again after a long gap (two seconds) is a new record.
    gap = [(0, [s(0, (500, 500, 600, 560), 0.3)]), (60, [s(60, (500, 500, 600, 560), 0.3)])]
    assert len(run(gap)) == 2

    # A box drawn inside a bigger one in the same frame is the same damage (seen on a real survey).
    nested = [(0, [s(0, (880, 800, 1216, 881), 0.25), s(0, (879, 810, 1055, 865), 0.43)])]
    t = run(nested)
    assert len(t) == 1 and t[0].best['conf'] == 0.43, t

    # Kind of damage follows the best sighting.
    flip = [(0, [s(0, (500, 500, 600, 560), 0.25, 'D20')]), (6, [s(6, (505, 560, 610, 630), 0.45, 'D40')])]
    assert run(flip)[0].best['code'] == 'D40'
    print('damage_tracker: all checks passed')

"""Shared helpers for the remaining evaluations (damage log check, AI-flag review, repeat drives,
device tests). Pure Python plus the standard library, so they run on any machine with the repo.

GPS time convention is the backend's (backend/services/gps_service.py): track times are seconds
from the first track point, and GPS time = video time + time_offset; outside the track the first or
last point is used (clamped), exactly as interpolate_gps() does.
"""

import csv
import math
import sqlite3
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'backend' / 'pothole_detection.db'
SNAPS = ROOT / 'backend' / 'snapshots'
UPLOADS = ROOT / 'backend' / 'uploads'
PROCESSED = ROOT / 'backend' / 'processed'
VIDEOS = ROOT / 'VID+GPX'
DATA = ROOT / 'data' / 'local'
RESULTS = ROOT / 'results'

NS = {'g': 'http://www.topografix.com/GPX/1/1', 'bk': 'urn:bantay-kalsada:capture:1'}
NAMES = {'D00': 'Longitudinal crack', 'D10': 'Transverse crack', 'D20': 'Alligator crack', 'D40': 'Pothole'}
R07_VIDEO = '20261031T021049-3x76.mov'
# The full R07 GPX is also committed as the public sample's track (its sessionId is R07's file name).
R07_GPX_IN_REPO = ROOT / 'frontend' / 'public' / 'samples' / 'alfonso-bayan-national-road' / 'track.gpx'


def parse_time(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


def read_gpx(path):
    """{'points': [(t_s_from_first, lat, lon, accuracy_m or None)], 'abs_times': [datetime],
    'capture': {<bk:capture> attributes}}. Points sorted by time, like the backend."""
    root = ET.parse(path).getroot()
    cap = root.find('g:metadata/g:extensions/bk:capture', NS)
    raw = []
    for p in root.iterfind('.//g:trkpt', NS):
        t = parse_time(p.findtext('g:time', namespaces=NS))
        if t is None:
            continue
        acc = p.findtext('g:extensions/bk:accuracy', namespaces=NS)
        raw.append((t, float(p.get('lat')), float(p.get('lon')), float(acc) if acc else None))
    raw.sort(key=lambda r: r[0])
    t0 = raw[0][0] if raw else None
    return {'points': [((t - t0).total_seconds(), la, lo, ac) for t, la, lo, ac in raw],
            'abs_times': [r[0] for r in raw],
            'capture': dict(cap.attrib) if cap is not None else {}}


def interpolate_clamped(points, video_s, offset):
    """The backend's interpolate_gps(): (lat, lon, clamped). points = [(t, lat, lon, ...)]."""
    t = video_s + offset
    if t <= points[0][0]:
        return points[0][1], points[0][2], True
    if t >= points[-1][0]:
        return points[-1][1], points[-1][2], True
    lo, hi = 0, len(points) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if points[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    a, b = points[lo], points[hi]
    f = 0.0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
    return round(a[1] + f * (b[1] - a[1]), 7), round(a[2] + f * (b[2] - a[2]), 7), False


def speed_at(points, gps_s):
    """Ground speed (m/s) of the track around GPS second gps_s, from the bracketing points."""
    for a, b in zip(points, points[1:]):
        if a[0] <= gps_s <= b[0] and b[0] > a[0]:
            return haversine_m(a[1], a[2], b[1], b[2]) / (b[0] - a[0])
    return 0.0


def haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres, R = 6,371 km (manuscript Equation 25)."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def distance_to_route_m(lat, lon, points):
    """Shortest distance (m) from (lat, lon) to the polyline through the track points (local
    equirectangular projection around the point; error well under 1 cm at these distances)."""
    kx = 111_320.0 * math.cos(math.radians(lat))
    ky = 110_574.0
    best = float('inf')
    px, py = 0.0, 0.0
    prev = None
    for p in points:
        x, y = (p[2] - lon) * kx, (p[1] - lat) * ky
        if prev is not None:
            ax, ay = prev
            dx, dy = x - ax, y - ay
            L = dx * dx + dy * dy
            f = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
            best = min(best, math.hypot(ax + f * dx - px, ay + f * dy - py))
        prev = (x, y)
    return best


def summary(values):
    """n, mean, SD (sample, n-1), median, min, max of a list of numbers."""
    v = [x for x in values if x is not None]
    if not v:
        return {'n': 0}
    return {'n': len(v), 'mean': statistics.fmean(v), 'sd': statistics.stdev(v) if len(v) > 1 else 0.0,
            'median': statistics.median(v), 'min': min(v), 'max': max(v)}


def wilson(k, n, z=1.96):
    if not n:
        return (float('nan'), float('nan'))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def connect(db=DB):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con


def survey(con, video_id):
    return con.execute('select * from videos where id = ?', (video_id,)).fetchone()


def survey_track(con, video_id):
    """The track the backend stored for the survey: [(t, lat, lon, None)] sorted, or []."""
    rows = con.execute('select timestamp, latitude, longitude from gps_track_points where video_id = ? '
                       'order by timestamp', (video_id,)).fetchall()
    return [(r['timestamp'], r['latitude'], r['longitude'], None) for r in rows]


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None, bom=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0].keys()) if rows else [])
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', newline='', encoding='utf-8-sig' if bom else 'utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def fmt(x, nd=2):
    return '' if x is None else (f'{x:.{nd}f}' if isinstance(x, float) else str(x))

"""Control-point georeferencing service.

Fallback positioning for videos uploaded WITHOUT a GPS track: the user marks a handful of
(video time -> map coordinate) control points at recognisable landmarks, and every detection
is positioned by piecewise-linear interpolation between its two bracketing control points.

Piecewise matters: a vehicle stops at lights and slows in traffic, so spreading detections
evenly over the whole route by total duration would be off by hundreds of metres.

Unlike gps_service.interpolate_gps(), a timestamp outside the control-point range returns
None rather than clamping to the first/last point — a fabricated coordinate is worse than none.
"""

# Philippine bounding box (inclusive)
PH_LAT_RANGE = (4.5, 21.5)
PH_LON_RANGE = (116.0, 127.0)

MIN_CONTROL_POINTS = 2


def _get(point, key):
    """Read a field from either a dict or a RouteControlPoint model instance."""
    if isinstance(point, dict):
        return point.get(key)
    return getattr(point, key, None)


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_control_points(points, max_time_s=None):
    """Validate a list of control points in the order given.

    Requirements:
      - at least MIN_CONTROL_POINTS points
      - numeric video_time_s, latitude, longitude on every point
      - video_time_s strictly increasing
      - video_time_s >= 0 and, when max_time_s is given, <= max_time_s
      - latitude / longitude inside the Philippine bounding box

    Returns:
        tuple: (is_valid: bool, error_message: str | None)
    """
    if not points or len(points) < MIN_CONTROL_POINTS:
        return False, f"At least {MIN_CONTROL_POINTS} control points are required"

    prev_time = None
    for i, p in enumerate(points):
        t = _as_float(_get(p, 'video_time_s'))
        lat = _as_float(_get(p, 'latitude'))
        lon = _as_float(_get(p, 'longitude'))

        if t is None or lat is None or lon is None:
            return False, f"Control point {i + 1} must have numeric video_time_s, latitude and longitude"

        if t < 0:
            return False, f"Control point {i + 1} has a negative video time ({t:.2f}s)"
        if max_time_s is not None and t > max_time_s:
            return False, (f"Control point {i + 1} is at {t:.2f}s but the video is only "
                           f"{max_time_s:.2f}s long")

        if prev_time is not None and t <= prev_time:
            return False, (f"Control point {i + 1} ({t:.2f}s) must be later than control point "
                           f"{i} ({prev_time:.2f}s) — video times must be strictly increasing")
        prev_time = t

        if not (PH_LAT_RANGE[0] <= lat <= PH_LAT_RANGE[1]):
            return False, (f"Control point {i + 1} latitude {lat:.5f} is outside the Philippines "
                           f"({PH_LAT_RANGE[0]} to {PH_LAT_RANGE[1]})")
        if not (PH_LON_RANGE[0] <= lon <= PH_LON_RANGE[1]):
            return False, (f"Control point {i + 1} longitude {lon:.5f} is outside the Philippines "
                           f"({PH_LON_RANGE[0]} to {PH_LON_RANGE[1]})")

    return True, None


def interpolate_from_control_points(control_points, video_time_s):
    """Piecewise-linear position for a video timestamp between its two bracketing control points.

    Same form as Formula 19 (G(t) = G_i + ((t - t_i) / (t_{i+1} - t_i)) × (G_{i+1} - G_i)) but
    over user-placed control points instead of a GPS track.

    Args:
        control_points: dicts or RouteControlPoint rows with video_time_s, latitude, longitude
        video_time_s: seconds from video start (Formula 18: frame_number / fps)

    Returns:
        tuple: (latitude, longitude) rounded to 7 dp, or None when video_time_s falls outside
        the [first, last] control-point range. Never clamps.
    """
    if not control_points or len(control_points) < MIN_CONTROL_POINTS:
        return None

    pts = sorted(
        ((float(_get(p, 'video_time_s')), float(_get(p, 'latitude')), float(_get(p, 'longitude')))
         for p in control_points),
        key=lambda x: x[0],
    )

    t = float(video_time_s)
    if t < pts[0][0] or t > pts[-1][0]:
        return None

    for (t_i, lat_i, lon_i), (t_next, lat_next, lon_next) in zip(pts, pts[1:]):
        if t_i <= t <= t_next:
            ratio = 0.0 if t_next == t_i else (t - t_i) / (t_next - t_i)
            lat = lat_i + ratio * (lat_next - lat_i)
            lon = lon_i + ratio * (lon_next - lon_i)
            return round(lat, 7), round(lon, 7)

    return None


def apply_control_points_to_detections(video, db):
    """Re-position every detection of a video from its stored control points.

    Detections inside the control-point range get interpolated coordinates and
    position_source='georeferenced'; every other detection is reset to no coordinate / 'none'
    so a shrunken range never leaves stale positions behind.

    Only meant for videos without a GPS track — the caller guards that.

    Returns:
        dict: {'positioned': int, 'unpositioned': int}
    """
    from models import Detection

    control_points = list(video.control_points)
    usable = len(control_points) >= MIN_CONTROL_POINTS
    detections = Detection.query.filter_by(video_id=video.id).all()

    positioned = 0
    for d in detections:
        coord = interpolate_from_control_points(control_points, d.timestamp) if usable else None
        if coord:
            d.latitude, d.longitude = coord
            d.position_source = 'georeferenced'
            positioned += 1
        else:
            d.latitude = None
            d.longitude = None
            d.position_source = 'none'

    video.position_source = 'georeferenced' if usable else 'none'
    db.session.commit()

    print(f"📍 Georeferenced video {video.id}: {positioned}/{len(detections)} detections positioned "
          f"from {len(control_points)} control points")

    return {'positioned': positioned, 'unpositioned': len(detections) - positioned}

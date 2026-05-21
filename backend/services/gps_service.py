"""GPS Track File Processing Service.

Implements GPS-Video Timestamp Synchronization from Thesis Chapter 3:
  Formula 18: t_frame = frame_number / FPS
  Formula 19: G(t) = G_i + ((t - t_i) / (t_{i+1} - t_i)) × (G_{i+1} - G_i)
"""

import csv
import io
from datetime import datetime


def parse_gpx_file(file_path):
    """Parse a GPX file and extract timestamped GPS track points.
    
    Returns:
        list of dict: [{'timestamp': float, 'latitude': float, 'longitude': float, 'elevation': float|None}, ...]
        Timestamps are in seconds from the first track point.
    """
    try:
        import gpxpy
    except ImportError:
        raise ImportError("gpxpy is required for GPX parsing. Install with: pip install gpxpy")

    with open(file_path, 'r') as f:
        gpx = gpxpy.parse(f)

    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append({
                    'time': point.time,
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                })

    # Also check waypoints if no track points
    if not points:
        for waypoint in gpx.waypoints:
            points.append({
                'time': waypoint.time,
                'latitude': waypoint.latitude,
                'longitude': waypoint.longitude,
                'elevation': waypoint.elevation,
            })

    if not points:
        raise ValueError("No GPS track points found in GPX file")

    # Convert absolute timestamps to seconds from start
    return _normalize_timestamps(points)


def parse_csv_file(file_path):
    """Parse a CSV file with GPS track data.
    
    Expected columns (case-insensitive):
        timestamp (or time, datetime), latitude (or lat), longitude (or lon, lng), elevation (or alt, optional)
    
    Returns:
        list of dict: [{'timestamp': float, 'latitude': float, 'longitude': float, 'elevation': float|None}, ...]
    """
    with open(file_path, 'r') as f:
        content = f.read()

    # Try to detect delimiter
    dialect = csv.Sniffer().sniff(content[:2048], delimiters=',;\t')
    reader = csv.DictReader(io.StringIO(content), dialect=dialect)

    # Normalize column names
    column_map = {}
    for col in reader.fieldnames:
        col_lower = col.strip().lower()
        if col_lower in ('timestamp', 'time', 'datetime', 'date_time', 'gps_time'):
            column_map['time'] = col
        elif col_lower in ('latitude', 'lat'):
            column_map['latitude'] = col
        elif col_lower in ('longitude', 'lon', 'lng', 'long'):
            column_map['longitude'] = col
        elif col_lower in ('elevation', 'alt', 'altitude', 'elev'):
            column_map['elevation'] = col

    if 'latitude' not in column_map or 'longitude' not in column_map:
        raise ValueError(
            f"CSV must contain latitude and longitude columns. "
            f"Found columns: {reader.fieldnames}"
        )

    points = []
    for row in reader:
        try:
            lat = float(row[column_map['latitude']].strip())
            lon = float(row[column_map['longitude']].strip())

            elev = None
            if 'elevation' in column_map:
                elev_val = row[column_map['elevation']].strip()
                if elev_val:
                    elev = float(elev_val)

            time_val = None
            if 'time' in column_map:
                time_str = row[column_map['time']].strip()
                time_val = _parse_timestamp_string(time_str)

            points.append({
                'time': time_val,
                'latitude': lat,
                'longitude': lon,
                'elevation': elev,
            })
        except (ValueError, KeyError):
            continue  # Skip invalid rows

    if not points:
        raise ValueError("No valid GPS points found in CSV file")

    # If no timestamps, create synthetic ones at 1 second intervals
    if all(p['time'] is None for p in points):
        for i, point in enumerate(points):
            point['time'] = datetime.fromtimestamp(i)

    return _normalize_timestamps(points)


def _parse_timestamp_string(time_str):
    """Try multiple timestamp formats to parse a time string."""
    formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',     # ISO 8601 with microseconds
        '%Y-%m-%dT%H:%M:%SZ',          # ISO 8601
        '%Y-%m-%dT%H:%M:%S.%f',        # ISO 8601 no Z
        '%Y-%m-%dT%H:%M:%S',           # ISO 8601 no Z no ms
        '%Y-%m-%d %H:%M:%S.%f',        # Space separated with ms
        '%Y-%m-%d %H:%M:%S',           # Space separated
        '%m/%d/%Y %H:%M:%S',           # US format
        '%d/%m/%Y %H:%M:%S',           # EU format
    ]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue

    # Try parsing as float (epoch seconds)
    try:
        return datetime.fromtimestamp(float(time_str))
    except (ValueError, OSError):
        pass

    raise ValueError(f"Cannot parse timestamp: {time_str}")


def _normalize_timestamps(points):
    """Convert datetime timestamps to seconds from the first point."""
    # Filter out points without valid timestamps
    valid_points = [p for p in points if p['time'] is not None]
    if not valid_points:
        raise ValueError("No GPS points with valid timestamps")

    # Sort by time
    valid_points.sort(key=lambda p: p['time'])

    # Convert to seconds from start
    start_time = valid_points[0]['time']
    result = []
    for p in valid_points:
        delta = (p['time'] - start_time).total_seconds()
        result.append({
            'timestamp': delta,
            'latitude': p['latitude'],
            'longitude': p['longitude'],
            'elevation': p['elevation'],
        })

    return result


def parse_gps_file(file_path):
    """Auto-detect file type and parse GPS track data.
    
    Returns:
        list of dict: Sorted by timestamp, normalized to seconds from start.
    """
    ext = file_path.lower().rsplit('.', 1)[-1]
    if ext == 'gpx':
        return parse_gpx_file(file_path)
    elif ext == 'csv':
        return parse_csv_file(file_path)
    else:
        raise ValueError(f"Unsupported GPS file format: .{ext}. Use .gpx or .csv")


def interpolate_gps(gps_points, video_timestamp, time_offset=0.0):
    """Interpolate GPS coordinates for a given video timestamp.
    
    Implements Formula 19 from Thesis Chapter 3:
        G(t) = G_i + ((t - t_i) / (t_{i+1} - t_i)) × (G_{i+1} - G_i)
    
    Args:
        gps_points: List of dicts with 'timestamp', 'latitude', 'longitude'
        video_timestamp: Time in seconds from video start (Formula 18: frame / FPS)
        time_offset: Offset between video start and GPS start (seconds)
    
    Returns:
        dict: {'latitude': float, 'longitude': float, 'elevation': float|None}
              or None if timestamp is outside GPS track range
    """
    if not gps_points:
        return None

    # Apply time offset: GPS time = video time + offset
    gps_time = video_timestamp + time_offset

    # Handle edge cases
    if gps_time <= gps_points[0]['timestamp']:
        return {
            'latitude': gps_points[0]['latitude'],
            'longitude': gps_points[0]['longitude'],
            'elevation': gps_points[0].get('elevation'),
        }

    if gps_time >= gps_points[-1]['timestamp']:
        return {
            'latitude': gps_points[-1]['latitude'],
            'longitude': gps_points[-1]['longitude'],
            'elevation': gps_points[-1].get('elevation'),
        }

    # Find the two bracketing GPS points
    for i in range(len(gps_points) - 1):
        t_i = gps_points[i]['timestamp']
        t_next = gps_points[i + 1]['timestamp']

        if t_i <= gps_time <= t_next:
            # Linear interpolation (Formula 19)
            if t_next == t_i:
                ratio = 0.0
            else:
                ratio = (gps_time - t_i) / (t_next - t_i)

            lat = gps_points[i]['latitude'] + ratio * (gps_points[i + 1]['latitude'] - gps_points[i]['latitude'])
            lon = gps_points[i]['longitude'] + ratio * (gps_points[i + 1]['longitude'] - gps_points[i]['longitude'])

            elev = None
            if gps_points[i].get('elevation') is not None and gps_points[i + 1].get('elevation') is not None:
                elev = gps_points[i]['elevation'] + ratio * (gps_points[i + 1]['elevation'] - gps_points[i]['elevation'])

            return {
                'latitude': round(lat, 7),
                'longitude': round(lon, 7),
                'elevation': round(elev, 2) if elev is not None else None,
            }

    return None


def validate_gps_track(gps_points, video_duration):
    """Validate that GPS track is usable with the given video.
    
    Returns:
        dict: {'valid': bool, 'message': str, 'track_duration': float, 'point_count': int}
    """
    if not gps_points:
        return {
            'valid': False,
            'message': 'No GPS track points found',
            'track_duration': 0,
            'point_count': 0,
        }

    track_duration = gps_points[-1]['timestamp'] - gps_points[0]['timestamp']

    if track_duration < 1:
        return {
            'valid': False,
            'message': 'GPS track is too short (less than 1 second)',
            'track_duration': track_duration,
            'point_count': len(gps_points),
        }

    # Warn if GPS track is much shorter than video
    coverage = min(track_duration / video_duration, 1.0) if video_duration > 0 else 0
    message = f"GPS track: {len(gps_points)} points, {track_duration:.1f}s duration, {coverage*100:.0f}% video coverage"

    return {
        'valid': True,
        'message': message,
        'track_duration': track_duration,
        'point_count': len(gps_points),
        'coverage': coverage,
    }

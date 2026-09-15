"""Severity Assessment Service — Rule-Based Scoring.

Implements the weighted severity formula:
    Severity = (0.4 × DamageTypeWeight) + (0.3 × AreaWeight) + (0.2 × ClusterWeight) + (0.1 × ConfidenceWeight)

Classification:
    0–39  → Low    (Yellow)
    40–69 → Medium (Orange)
    70–100 → High  (Red)
"""

import math

# NOTE: this service is retained for reference / future work (thesis Sec 3.1.6) and is not
# invoked anywhere in the pipeline. Detection.severity stays NULL.

# Damage type severity weights (0-100), keyed by RDD2022 code (D00 long, D10 trans, D20 allig, D40 pothole)
DAMAGE_TYPE_WEIGHTS = {
    'D20': 100,   # Alligator Crack — most severe structural damage
    'D40': 85,    # Pothole — immediate hazard
    'D00': 60,    # Longitudinal Crack — moderate structural concern
    'D10': 50,    # Transverse Crack — least severe of the four
}

# Default weight for unknown damage types
DEFAULT_DAMAGE_WEIGHT = 50


def calculate_severity(detection, all_detections=None, frame_width=640, frame_height=640):
    """Calculate severity score for a single detection.
    
    Args:
        detection: dict with keys: damage_type, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                   latitude, longitude
        all_detections: list of all detections (for cluster analysis), optional
        frame_width: video frame width for area normalization
        frame_height: video frame height for area normalization
    
    Returns:
        dict: {'score': float (0-100), 'level': str ('low'|'medium'|'high'), 'factors': dict}
    """
    # Factor A: Damage Type Weight (0.4)
    damage_type = detection.get('damage_type', 'D40')
    type_weight = DAMAGE_TYPE_WEIGHTS.get(damage_type, DEFAULT_DAMAGE_WEIGHT)

    # Factor B: Bounding Box Area Weight (0.3)
    bbox_area = abs(
        (detection.get('bbox_x2', 0) - detection.get('bbox_x1', 0)) *
        (detection.get('bbox_y2', 0) - detection.get('bbox_y1', 0))
    )
    frame_area = frame_width * frame_height
    area_ratio = bbox_area / frame_area if frame_area > 0 else 0
    # Normalize: 0-5% of frame = 0-100 score (larger is more severe)
    area_weight = min(area_ratio / 0.05, 1.0) * 100

    # Factor C: Cluster Weight (0.2)
    cluster_weight = 0
    if all_detections and detection.get('latitude') and detection.get('longitude'):
        cluster_count = _count_nearby_detections(
            detection['latitude'], detection['longitude'],
            all_detections, radius_meters=50
        )
        # 0 nearby = 0, 1-3 nearby = 33-100, 4+ = 100
        cluster_weight = min(cluster_count / 3.0, 1.0) * 100

    # Factor D: Confidence Weight (0.1)
    confidence = detection.get('confidence', 0.5)
    confidence_weight = confidence * 100

    # Weighted severity formula
    severity_score = (
        0.4 * type_weight +
        0.3 * area_weight +
        0.2 * cluster_weight +
        0.1 * confidence_weight
    )

    # Clamp to 0-100
    severity_score = max(0, min(100, severity_score))

    # Classify severity level
    if severity_score >= 70:
        level = 'high'
    elif severity_score >= 40:
        level = 'medium'
    else:
        level = 'low'

    return {
        'score': round(severity_score, 2),
        'level': level,
        'factors': {
            'damage_type': round(type_weight, 1),
            'area': round(area_weight, 1),
            'cluster': round(cluster_weight, 1),
            'confidence': round(confidence_weight, 1),
        }
    }


def _count_nearby_detections(lat, lon, all_detections, radius_meters=50):
    """Count how many other detections are within a radius (in meters).
    
    Uses the Haversine formula for geographic distance.
    """
    count = 0
    for det in all_detections:
        det_lat = det.get('latitude')
        det_lon = det.get('longitude')
        if det_lat is None or det_lon is None:
            continue
        if det_lat == lat and det_lon == lon:
            continue  # Skip self

        distance = _haversine_distance(lat, lon, det_lat, det_lon)
        if distance <= radius_meters:
            count += 1

    return count


def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS points in meters using Haversine formula."""
    R = 6371000  # Earth's radius in meters

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def batch_calculate_severity(detections, frame_width=640, frame_height=640):
    """Calculate severity for a batch of detections (enables cluster analysis).
    
    Args:
        detections: list of detection dicts
        frame_width: video frame width
        frame_height: video frame height
    
    Returns:
        list of severity result dicts (same order as input)
    """
    results = []
    for det in detections:
        result = calculate_severity(det, all_detections=detections,
                                     frame_width=frame_width, frame_height=frame_height)
        results.append(result)
    return results


def get_severity_color(level):
    """Get display color for severity level."""
    colors = {
        'high': '#ef4444',    # Red
        'medium': '#f59e0b',  # Orange
        'low': '#eab308',     # Yellow
    }
    return colors.get(level, '#64748b')


def get_severity_label(level):
    """Get display label for severity level."""
    labels = {
        'high': 'High Priority',
        'medium': 'Medium Priority',
        'low': 'Low Priority',
    }
    return labels.get(level, 'Unknown')

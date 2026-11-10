"""Step 1.1: read every recording in VID+GPX/ and write data/local/recordings.csv (R01-R21).

    python ml/local/ingest_local.py

Per recording: duration, frame rate, frame count, displayed resolution, rotation flag, codec (video,
via ffprobe and the backend's open_upright()); and from the GPX written by the phone app: road band
(roadTop/roadBottom), time offset, clock skew and video start time when present. A missing or
unusable road band falls back to the backend's default band (0.50-1.00) and is listed at the end.
IDs are given in order of video start time, so they do not change when a folder is renamed.
Nothing in VID+GPX/ is moved, renamed or written.
"""

import json
from pathlib import Path
import subprocess
import sys

from common import OUT, ROAD_REGION_BOTTOM, ROAD_REGION_TOP, find_recordings, haversine_m, open_upright, \
    parse_time, position_at, read_csv, read_gpx, road_band, write_csv


def ffprobe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format',
                          str(path)], capture_output=True, text=True, encoding='utf-8')
    if out.returncode:
        return {}
    info = json.loads(out.stdout)
    v = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), {})
    rot = 0
    for sd in v.get('side_data_list', []):
        if 'rotation' in sd:
            rot = int(round(float(sd['rotation'])))
    rot = int(v.get('tags', {}).get('rotate', rot))
    return dict(codec=v.get('codec_name', ''), probe_rotation=(-rot) % 360,
                probe_duration=float(info.get('format', {}).get('duration', 0) or 0),
                creation_time=info.get('format', {}).get('tags', {}).get('creation_time', ''))


def main():
    rows, problems = [], []
    for folder, video, gpx in find_recordings():
        r = dict(folder=folder, video=video.name if video else '', gpx=gpx.name if gpx else '')
        if not video or not gpx:
            problems.append(f'{folder}: missing {"video" if not video else "GPX"}')
        if video:
            cap, rotate_code, w, h = open_upright(str(video))
            fps = cap.get(5) or 0          # CAP_PROP_FPS
            frames = int(cap.get(7) or 0)  # CAP_PROP_FRAME_COUNT
            angle = int(round(cap.get(48) or 0)) % 360   # CAP_PROP_ORIENTATION_META
            cap.release()
            p = ffprobe(video)
            r.update(duration_s=round(frames / fps, 2) if fps else '', fps=round(fps, 3), frames=frames,
                     width=w, height=h, rotation=angle, codec=p.get('codec', ''),
                     probe_duration_s=round(p.get('probe_duration', 0), 2), creation_time=p.get('creation_time', ''))
            if p and p.get('probe_rotation') != angle:
                problems.append(f'{folder}: rotation OpenCV {angle} vs ffprobe {p.get("probe_rotation")}')
        pts, capt = read_gpx(gpx) if gpx else ([], {})
        top, bottom = capt.get('roadTop'), capt.get('roadBottom')
        band = road_band(top, bottom)
        band_src = 'gpx' if top is not None and bottom is not None and band == (float(top), float(bottom)) else 'default'
        if band_src == 'default':
            band = (ROAD_REGION_TOP, ROAD_REGION_BOTTOM)
        offset = float(capt.get('timeOffsetS', 0) or 0)
        dur = r.get('duration_s') or 0
        span = [position_at(pts, s, offset) for s in range(int(dur) + 1)]
        located = [q for q in span if q]
        length = sum(haversine_m(*a, *b) for a, b in zip(located, located[1:]))
        r.update(road_top=round(band[0], 4), road_bottom=round(band[1], 4), road_band_source=band_src,
                 time_offset_s=capt.get('timeOffsetS', ''), clock_skew_ms=capt.get('clockSkewMs', ''),
                 video_start=capt.get('videoStart', ''), video_start_source=capt.get('videoStartSource', ''),
                 capture_recording_id=capt.get('recordingId', ''), capture_part=capt.get('part', ''),
                 gps_points=len(pts), gps_hz=capt.get('achievedHz', ''), gps_errors=capt.get('gpsErrors', ''),
                 seconds_with_position=f'{len(located)}/{len(span)}', route_km=round(length / 1000, 2),
                 start_lat=round(located[0][0], 6) if located else '', start_lon=round(located[0][1], 6) if located else '',
                 end_lat=round(located[-1][0], 6) if located else '', end_lon=round(located[-1][1], 6) if located else '',
                 platform=capt.get('platform', ''), camera_pitch_deg=capt.get('cameraPitchDegAtStart', ''))
        for key in ('timeOffsetS', 'clockSkewMs', 'videoStart'):
            if key not in capt:
                problems.append(f'{folder}: GPX has no {key}')
        if band_src == 'default':
            problems.append(f'{folder}: no usable road band in the GPX, default {ROAD_REGION_TOP:.2f}-{ROAD_REGION_BOTTOM:.2f} used')
        if span and len(located) < len(span) * 0.95:
            problems.append(f'{folder}: GPS covers only {len(located)} of {len(span)} video seconds')
        rows.append(r)

    def start_key(r):
        t = parse_time(r.get('video_start')) or parse_time(r.get('creation_time'))
        return (t.timestamp() if t else float('inf'), r['folder'])
    rows.sort(key=start_key)
    # Mount: recording_mounts.csv lists the hand-held ones (team, 2026-11-09); all others were mounted.
    handheld = {m['video'] for m in read_csv(Path(__file__).resolve().parent / 'recording_mounts.csv')
                if m['mount'] == 'handheld'}
    # Ids are permanent: a recording keeps the id it was first given (matched by video file name);
    # recordings excluded later (status != used) keep their rows; new recordings get the next free ids.
    old_p = OUT / 'recordings.csv'
    old = read_csv(old_p) if old_p.exists() else []
    known = {r['video']: r['id'] for r in old}
    next_id = max([int(r['id'][1:]) for r in old] or [0]) + 1
    for r in rows:
        if r['video'] in known:
            r['id'] = known[r['video']]
        else:
            r['id'] = f'R{next_id:02d}'
            next_id += 1
        r['mount'] = 'handheld' if r['video'] in handheld else 'mounted'
        r['status'] = next((o.get('status') or 'used' for o in old if o['video'] == r['video']), 'used')
    present = {r['video'] for r in rows}
    gone_used = [o['folder'] for o in old if o['video'] not in present and (o.get('status') or 'used') == 'used']
    if gone_used and '--force' not in sys.argv:
        sys.exit(f'recordings.csv NOT rewritten: recordings in use are missing from VID+GPX: {gone_used}. '
                 'Restore them, or exclude them first (exclude_recordings.py).')
    rows += [o for o in old if o['video'] not in present]   # excluded recordings: rows kept as they were
    rows.sort(key=lambda r: int(r['id'][1:]))
    fields = list(dict.fromkeys(['id'] + [k for r in rows for k in r if k != 'id']))
    write_csv(old_p, [{k: r.get(k, '') for k in fields} for r in rows], fields)

    print(f'{"id":4} {"dur":>6} {"fps":>6} {"size":>10} {"rot":>4} {"band":>11} {"src":>7} {"offset":>7} '
          f'{"skew":>5} {"km":>5}  folder')
    used = [r for r in rows if r['status'] == 'used']
    for r in used:
        print(f'{r["id"]:4} {r.get("duration_s", ""):>6} {r.get("fps", ""):>6} {str(r.get("width")) + "x" + str(r.get("height")):>10} '
              f'{r.get("rotation", ""):>4} {float(r["road_top"]):.2f}-{float(r["road_bottom"]):.2f} {r["road_band_source"]:>7} '
              f'{r["time_offset_s"]:>7} {r["clock_skew_ms"]:>5} {r["route_km"]:>5}  {r["folder"]}')
    total = sum(float(r.get('duration_s') or 0) for r in used)
    print(f'\n{len(used)} recordings in use, {total / 3600:.2f} h of video -> {OUT / "recordings.csv"}')
    for r in rows:
        if r['status'] != 'used':
            print(f'  {r["id"]} {r["folder"]}: {r["status"]}')
    print('\nProblems:' if problems else '\nNo problems found.')
    for p in problems:
        print('  -', p)
    return 0


if __name__ == '__main__':
    sys.exit(main())

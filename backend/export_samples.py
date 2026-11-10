"""Export analysed surveys as sample surveys for the public website (frontend/public/samples/).

    python backend/export_samples.py 2 3 4 5 6            # survey ids, in the order to show them
    python backend/export_samples.py 2 --clip 120          # clip length in seconds (default 180)

For each survey it writes frontend/public/samples/<slug>/:
  video.mp4        the annotated video, cut to the CLIP_S-second stretch with the most damage the
                   AI check accepts, 720p and fast-start so phones can play it over mobile data
  poster.jpg       a frame for the picker and the player
  track.gpx        the survey's GPS file as uploaded
  detections.json  the damage in that stretch: time in the clip, code, confidence, position, AI check

and adds or updates the survey's entry in frontend/public/samples/samples.json. Title, location
and date you edited there are kept on re-export; files, counts and the model are refreshed.
gps_offset_s follows the backend's rule: GPS time (seconds from the first fix) = video time + offset.

Needs ffmpeg on PATH. Reads the database and files directly; the server does not need to run.
After swapping the model: "Analyse again" on each survey, then run this again.
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

BACKEND = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BACKEND, '..', 'frontend', 'public', 'samples')
VERIFY_THRESHOLD = 0.6   # services/damage_verifier.py; not imported, it pulls in torch
# Models that are not the team's own (app.py's DEMO PLACEHOLDER): the website says so on its samples.
STAND_IN_MODELS = {'rdd2022_pretrained.pt'}


def model_file():
    """The model file the backend loads (ml/models/model_config.json), so each sample says what produced it."""
    import model_config
    return os.path.basename(model_config.load()['weights'])


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def best_window(times, duration, clip):
    """Start of the clip-second stretch holding the most of `times` (on a 5 s grid)."""
    if duration <= clip:
        return 0.0
    starts = [s * 5.0 for s in range(int((duration - clip) // 5) + 1)]
    return max(starts, key=lambda s: sum(s <= t < s + clip for t in times))


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


def export(db, video_id, clip, model):
    v = db.execute('select * from videos where id = ?', (video_id,)).fetchone()
    if not v or v['status'] != 'completed' or not v['processed_filename']:
        sys.exit(f'Survey {video_id} is not a finished analysis.')
    if not v['gps_filename']:
        sys.exit(f'Survey {video_id} has no GPS file; samples need one.')
    title = v['display_name'] or v['original_filename']
    slug = slugify(title)
    dets = db.execute('select timestamp, damage_type, confidence, latitude, longitude, ai_check_score '
                      'from detections where video_id = ? and latitude is not null order by timestamp',
                      (video_id,)).fetchall()
    passed = [d['timestamp'] for d in dets
              if d['ai_check_score'] is None or d['ai_check_score'] >= VERIFY_THRESHOLD]
    start = best_window(passed, v['duration'], clip)
    length = min(clip, v['duration'] - start)

    folder = os.path.join(OUT, slug)
    os.makedirs(folder, exist_ok=True)
    src = os.path.join(BACKEND, 'processed', v['processed_filename'])
    ffmpeg('-ss', f'{start:.3f}', '-i', src, '-t', f'{length:.3f}', '-vf', 'scale=-2:720',
           # Capped at 1.4 Mbit/s (~30 MB for 3 minutes): trees and road texture otherwise take
           # crf 28 to 3.8 Mbit/s, too heavy for respondents on mobile data.
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '28', '-maxrate', '1400k', '-bufsize', '2800k',
           '-an', '-movflags', '+faststart',
           os.path.join(folder, 'video.mp4'))
    # The poster comes from the original video: no boxes, so no false detection on the thumbnail.
    ffmpeg('-ss', f'{start + min(5, length / 2):.3f}', '-i', os.path.join(BACKEND, 'uploads', v['filename']),
           '-frames:v', '1', '-vf', 'scale=-2:480', '-q:v', '4', os.path.join(folder, 'poster.jpg'))
    gpx_src = os.path.join(BACKEND, 'uploads', v['gps_filename'])
    shutil.copyfile(gpx_src, os.path.join(folder, 'track.gpx'))

    rows = [{'t': round(d['timestamp'] - start, 2), 'code': d['damage_type'],
             'conf': round(d['confidence'], 3), 'lat': d['latitude'], 'lon': d['longitude'],
             'ai': None if d['ai_check_score'] is None else round(d['ai_check_score'], 3)}
            for d in dets if start <= d['timestamp'] < start + length]
    with open(os.path.join(folder, 'detections.json'), 'w', encoding='utf-8') as f:
        json.dump(rows, f, separators=(',', ':'))

    # Recording date in Philippine time, from the first GPS fix.
    with open(gpx_src, encoding='utf-8') as f:
        first = re.search(r'<time>([^<]+)</time>', f.read()).group(1)
    date = (datetime.fromisoformat(first.replace('Z', '+00:00')) + timedelta(hours=8)).date().isoformat()

    print(f'Survey {video_id} -> samples/{slug}: {start:.0f}-{start + length:.0f} s of {v["duration"]:.0f} s, '
          f'{len(rows)} damages, video {os.path.getsize(os.path.join(folder, "video.mp4")) / 1e6:.1f} MB')
    return {
        'id': slug, 'title': title, 'location': v['road_name'] or '', 'date': date,
        'duration_s': round(length, 2), 'clip_start_s': round(start, 2), 'full_duration_s': round(v['duration'], 2),
        'video': f'/samples/{slug}/video.mp4', 'poster': f'/samples/{slug}/poster.jpg',
        'gpx': f'/samples/{slug}/track.gpx', 'gps_offset_s': round((v['time_offset'] or 0) + start, 3),
        'detections': f'/samples/{slug}/detections.json', 'damage_count': len(rows), 'model': model,
        'stand_in_model': model in STAND_IN_MODELS,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('surveys', type=int, nargs='+')
    ap.add_argument('--clip', type=float, default=180, help='clip length in seconds (default 180)')
    args = ap.parse_args()
    if shutil.which('ffmpeg') is None:
        sys.exit('ffmpeg is not on PATH. Install it: winget install Gyan.FFmpeg')

    db = sqlite3.connect(os.path.join(BACKEND, 'pothole_detection.db'))
    db.row_factory = sqlite3.Row
    index_path = os.path.join(OUT, 'samples.json')
    old = {}
    if os.path.exists(index_path):
        with open(index_path, encoding='utf-8') as f:
            old = {s['id']: s for s in json.load(f)}

    model = model_file()
    fresh = [export(db, vid, args.clip, model) for vid in args.surveys]
    for s in fresh:   # keep what was edited by hand
        for key in ('title', 'location', 'date'):
            if old.get(s['id'], {}).get(key):
                s[key] = old[s['id']][key]
    ids = {s['id'] for s in fresh}
    samples = fresh + [s for s in old.values() if s['id'] not in ids]
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f'{len(samples)} samples in {os.path.normpath(index_path)}')


if __name__ == '__main__':
    main()

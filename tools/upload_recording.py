"""Upload one team recording to the running backend as a survey, and wait for its analysis.

    python tools/upload_recording.py R06 [--server http://localhost:5000] [--user admin --password ...]

The end-to-end check after deploying a model. The recording (an id from data/local/recordings.csv)
is sent like the phone sends it: the video, its GPX, time_offset, and the road band. The band
comes from ml/local/road_band_overrides.csv when the recording is listed there (R04-R14: the GPX
bands are wrong), else from the GPX (common.band_for); R13/R14 use the bonnet line 0.73. The server
itself moves the top down by NEAR_ZONE_DELTA (the near zone), so the horizon line is sent as it is. Prints the analysis result per damage type.
"""

import argparse
import getpass
import sys
import time
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'ml' / 'local'))
from common import OUT, VIDEOS, band_for, read_csv  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('recording', help='e.g. R06')
    ap.add_argument('--server', default='http://localhost:5000')
    ap.add_argument('--user', default='admin')
    ap.add_argument('--password', help='asked for when left out')
    a = ap.parse_args()
    rec = {r['id']: r for r in read_csv(OUT / 'recordings.csv')}.get(a.recording)
    if not rec:
        sys.exit(f'{a.recording} is not in data/local/recordings.csv')
    if rec['status'] != 'used':
        sys.exit(f'{a.recording} is {rec["status"]}; use a mounted recording.')
    video = VIDEOS / rec['folder'] / rec['video']
    gpx = VIDEOS / rec['folder'] / rec['gpx']
    for p in (video, gpx):
        if not p.exists():
            sys.exit(f'Missing {p}')
    top, bottom, source = band_for(rec)
    from near_zone import BOTTOM   # R13/R14 bonnet line 0.73 (team decision 2026-11-10)
    if rec['id'] in BOTTOM:
        bottom, source = BOTTOM[rec['id']], source + ' + near-zone bottom'
    api = a.server.rstrip('/') + '/api'

    pw = a.password or getpass.getpass(f'Password for {a.user}: ')
    r = requests.post(f'{api}/auth/login', json={'username': a.user, 'password': pw}, timeout=30)
    if r.status_code != 200:
        sys.exit(f'Sign-in failed: {r.status_code} {r.text[:200]}')
    h = {'Authorization': f'Bearer {r.json()["token"]}'}

    print(f'Uploading {a.recording} ({rec["folder"]}, {video.stat().st_size / 1e6:.0f} MB), road band '
          f'{top:.2f}-{bottom:.2f} ({source}), time offset {rec["time_offset_s"] or 0} s')
    with open(video, 'rb') as fv, open(gpx, 'rb') as fg:
        r = requests.post(f'{api}/videos/upload', headers=h, timeout=3600,
                          files={'video': (video.name, fv), 'gps_file': (gpx.name, fg)},
                          data={'time_offset': rec['time_offset_s'] or '0', 'road_name': rec['folder'],
                                'road_top': f'{top:.4f}', 'road_bottom': f'{bottom:.4f}'})
    if r.status_code not in (200, 201):
        sys.exit(f'Upload refused: {r.status_code} {r.text[:300]}')
    vid = r.json()['video']['id']
    print(f'Survey {vid} uploaded; analysing...')
    start = time.time()
    while True:
        v = requests.get(f'{api}/videos/{vid}', headers=h, timeout=30).json()
        st = v['video']['status']
        if st in ('completed', 'failed'):
            break
        print(f'\r  {st} {v["video"].get("processing_progress") or 0:.0f}%  ({time.time() - start:.0f} s)', end='', flush=True)
        time.sleep(10)
    print()
    if st == 'failed':
        sys.exit(f'Analysis failed: {v["video"]["error_message"]}')
    d = v['detections']
    kinds = Counter(x['damage_type'] for x in d)
    print(f'Done in {time.time() - start:.0f} s: {len(d)} damage records '
          f'({", ".join(f"{k} {n}" for k, n in sorted(kinds.items()))}); '
          f'{sum(1 for x in d if x.get("latitude") is not None)} with a position; '
          f'{sum(1 for x in d if x.get("ai_flagged"))} flagged by the AI check.')
    print(f'Open it in the web app: Surveys > survey {vid}.')


if __name__ == '__main__':
    main()

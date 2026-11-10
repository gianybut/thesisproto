"""Step 1.3: one frame per second from every recording, upright and cropped to the road band.

    python ml/local/extract_frames.py [--hash-threshold 6] [--workers 4]

- Rotation: the backend's open_upright() (the phone's rotation flag), as the server reads videos.
- Road band: road_band_overrides.csv where the team approved one, else the band from the GPX
  (common.band_for). Rows int(h*top) to int(h*bottom), as in the server's pipeline.
- Near-duplicates: 64-bit perceptual hash (DCT) of the band crop; a frame whose hash is within
  --hash-threshold bits of the last KEPT frame of the same recording is dropped (the car standing
  at a junction). Only consecutive frames of one recording are compared.
- Position: the GPX interpolated at video second s with the recording's time offset (same
  convention as backend/services/gps_service.py); speed from the positions 1 s either side.

Writes data/local/frames/<Rxx>_s<ssss>.jpg (band crop, the training image),
data/local/frames_full/<same name> (the whole upright frame: the server runs the AI check (CLIP)
on the whole frame, so autolabel.py does too), manifest.csv (kept frames) and frames_all.csv
(every second, with why a frame was dropped).
"""

import argparse
import shutil
import sys
from multiprocessing import Pool

import cv2
import numpy as np

from common import OUT, VIDEOS, band_for, used_recordings, haversine_m, open_upright, position_at, read_csv, read_gpx, write_csv

FRAMES, FULL = OUT / 'frames', OUT / 'frames_full'


def phash(img):
    g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    d = cv2.dct(g)[:8, :8].flatten()
    return np.packbits(d > np.median(d[1:]))


def extract(job):
    rec, group, threshold = job
    rid = rec['id']
    top, bottom, band_src = band_for(rec)
    pts, _ = read_gpx(VIDEOS / rec['folder'] / rec['gpx'])
    offset = float(rec['time_offset_s'] or 0)
    cap, rotate, w, h = open_upright(str(VIDEOS / rec['folder'] / rec['video']))
    fps = cap.get(cv2.CAP_PROP_FPS)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    top_px, bottom_px = int(h * top), int(h * bottom)
    targets = {}
    s = 0
    while round(s * fps) < n_frames:
        targets[round(s * fps)] = s
        s += 1
    rows, last_hash, last_kept = [], None, None
    idx = 0
    while idx <= max(targets):
        if not cap.grab():
            break
        if idx in targets:
            sec = targets[idx]
            ok, frame = cap.retrieve()
            if not ok:
                break
            if rotate is not None:
                frame = cv2.rotate(frame, rotate)
            band = frame[top_px:bottom_px]
            hsh = phash(band)
            dist = int(np.unpackbits(hsh ^ last_hash).sum()) if last_hash is not None else 64
            name = f'{rid}_s{sec:04d}.jpg'
            pos = position_at(pts, sec, offset)
            a, b = position_at(pts, sec - 1, offset), position_at(pts, sec + 1, offset)
            speed = haversine_m(*a, *b) / 2 if a and b else ''
            keep = dist > threshold
            if keep:
                cv2.imwrite(str(FRAMES / name), band, [cv2.IMWRITE_JPEG_QUALITY, 95])
                cv2.imwrite(str(FULL / name), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                last_hash, last_kept = hsh, name
            rows.append(dict(frame=name, recording=rid, route_group=group, second=sec,
                             lat=round(pos[0], 7) if pos else '', lon=round(pos[1], 7) if pos else '',
                             speed_mps=round(speed, 2) if speed != '' else '', band_top=top, band_bottom=bottom,
                             band_source=band_src, band_top_px=top_px, frame_w=w, frame_h=h,
                             kept=int(keep), hash_dist_to_last_kept=dist, duplicate_of='' if keep else last_kept))
        idx += 1
    cap.release()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hash-threshold', type=int, default=6, help='drop a frame within this many bits (of 64)')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--only', default='', help='comma-separated recording ids to redo; the others are kept')
    a = ap.parse_args()

    recs = used_recordings()
    only = {x.strip() for x in a.only.split(',') if x.strip()}
    groups = {g['id']: g['route_group'] for g in read_csv(OUT / 'route_groups.csv')}
    by_video = {r['video']: r for r in read_csv(OUT / 'recordings.csv')}
    for o in read_csv(Path(__file__).resolve().parent / 'road_band_overrides.csv'):
        if o['video'] not in by_video or by_video[o['video']]['id'] != o['id']:
            sys.exit(f'road_band_overrides.csv: {o["video"]} is not recording {o["id"]}')
    if only:
        for d in (FRAMES, FULL):
            for rid in only:
                for p in d.glob(f'{rid}_s*.jpg'):
                    p.unlink()
        todo = [r for r in recs if r['id'] in only]
    else:
        for d in (FRAMES, FULL):
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True)
        todo = recs

    with Pool(a.workers) as pool:
        new = pool.map(extract, [(r, groups[r['id']], a.hash_threshold) for r in todo])
    if only:   # keep the other recordings' rows from the previous run, in recording order
        old = {}
        for x in read_csv(OUT / 'frames_all.csv'):
            for k in ('second', 'band_top_px', 'frame_w', 'frame_h', 'kept', 'hash_dist_to_last_kept'):
                x[k] = int(x[k])
            for k in ('band_top', 'band_bottom'):
                x[k] = float(x[k])
            x['speed_mps'] = float(x['speed_mps']) if x['speed_mps'] != '' else ''
            old.setdefault(x['recording'], []).append(x)
        fresh = {rr[0]['recording']: rr for rr in new}
        per_rec = [fresh.get(r['id']) or old[r['id']] for r in recs]
    else:
        per_rec = new
    rows = [x for rr in per_rec for x in rr]
    write_csv(OUT / 'frames_all.csv', rows)
    kept = [r for r in rows if r['kept']]
    write_csv(OUT / 'manifest.csv', [{k: r[k] for k in ('frame', 'recording', 'route_group', 'second', 'lat', 'lon',
                                                        'speed_mps', 'band_top', 'band_bottom', 'band_source',
                                                        'band_top_px', 'frame_w', 'frame_h')} for r in kept])

    print(f'{"rec":4} {"band":>10} {"src":>8} {"seconds":>7} {"kept":>5} {"dup":>4} {"no GPS":>6}')
    for rr in per_rec:
        r0 = rr[0]
        k = sum(x['kept'] for x in rr)
        print(f'{r0["recording"]:4} {r0["band_top"]:.2f}-{r0["band_bottom"]:.2f} {r0["band_source"]:>8} {len(rr):7} '
              f'{k:5} {len(rr) - k:4} {sum(1 for x in rr if x["kept"] and x["lat"] == ""):6}')
    dropped = [r for r in rows if not r['kept']]
    moving_dropped = sum(1 for r in dropped if r['speed_mps'] != '' and r['speed_mps'] > 2)
    still_kept = sum(1 for r in kept if r['speed_mps'] != '' and r['speed_mps'] < 0.5)
    print(f'\n{len(rows)} seconds, {len(kept)} frames kept, {len(dropped)} near-duplicates dropped '
          f'(threshold {a.hash_threshold}/64 bits).')
    print(f'Check against GPS speed: {moving_dropped} dropped frames were moving > 2 m/s; '
          f'{still_kept} kept frames were standing (< 0.5 m/s).')
    print(f'-> {FRAMES}, {FULL}, manifest.csv, frames_all.csv')


if __name__ == '__main__':
    from pathlib import Path
    main()

"""Camera steadiness and "road inside the band" per recording (team request 2026-11-09).

    python ml/local/shake_check.py

1. Contact sheet per recording: 8 whole frames spread over the video, with the road band drawn
   (data/local/contact/<Rxx>.jpg, plus all_recordings.jpg).
2. Shake/tilt score (needs the video): 12 windows of 31 consecutive frames, spread over the video.
   Between consecutive frames, the camera's motion is estimated from features in the distant part
   of the picture (15-60% of the height, where driving forward moves the picture little): a
   similarity transform via LK optical flow + RANSAC. Per window, the spread (standard deviation)
   of the vertical shift (pixels at 1080p; pitch jitter) and of the rotation (degrees; roll
   jitter); per recording, the median over windows. A mounted recording is flagged when either
   value is more than twice the median of the mounted recordings.
3. Road inside the band: every frame's band crop is scored with the backend's CLIP model
   (zero-shot: road surface vs dashboard, car interior, bonnet, trees/sky, buildings, blur);
   a frame "shows road" when the road descriptions get at least half of CLIP's answer.

Writes data/local/shake_check.csv and results/step1_mount_check.md.
"""

import sys

import cv2
import numpy as np

from common import OUT, ROOT, VIDEOS, band_for, used_recordings, open_upright, read_csv, write_csv
from services import damage_verifier

ROAD = ['an asphalt road surface seen from a car', 'a road with lane markings ahead of a car',
        'a concrete road surface', 'a street with cars ahead']
OTHER = ['a car dashboard', 'the inside of a car', 'the bonnet of a car', 'trees and sky', 'buildings and houses',
         'a very blurry photo', 'a phone screen']


def motion(path):
    cap, rot, w, h = open_upright(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dys, angs = [], []
    for start in np.linspace(n * 0.05, n * 0.95 - 31, 12).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start))
        prev, ty, an = None, [], []
        for _ in range(31):
            ok, f = cap.read()
            if not ok:
                break
            if rot is not None:
                f = cv2.rotate(f, rot)
            g = cv2.cvtColor(cv2.resize(f, (640, 360)), cv2.COLOR_BGR2GRAY)
            if prev is not None:
                mask = np.zeros_like(g)
                mask[int(360 * 0.15):int(360 * 0.60)] = 255
                p0 = cv2.goodFeaturesToTrack(prev, 400, 0.01, 8, mask=mask)
                if p0 is not None and len(p0) >= 12:
                    p1, st, _ = cv2.calcOpticalFlowPyrLK(prev, g, p0, None)
                    good = st.ravel() == 1
                    if good.sum() >= 12:
                        m, _ = cv2.estimateAffinePartial2D(p0[good], p1[good], method=cv2.RANSAC,
                                                           ransacReprojThreshold=2.0)
                        if m is not None:
                            ty.append(m[1, 2] * 1080 / 360)
                            an.append(np.degrees(np.arctan2(m[1, 0], m[0, 0])))
            prev = g
        if len(ty) >= 10:
            dys.append(np.std(ty))
            angs.append(np.std(an))
    cap.release()
    return (float(np.median(dys)), float(np.median(angs))) if dys else (None, None)


def clip_road_share(names):
    import torch
    from PIL import Image
    model = damage_verifier._load(allow_download=False)
    proc = damage_verifier._state['processor']
    with torch.no_grad():
        t = model.get_text_features(**proc(text=[f'a photo of {p}' for p in ROAD + OTHER], return_tensors='pt',
                                           padding=True))
        t = t / t.norm(dim=-1, keepdim=True)
        out = []
        for i in range(0, len(names), 32):
            ims = [Image.fromarray(cv2.cvtColor(cv2.imread(str(OUT / 'frames' / n)), cv2.COLOR_BGR2RGB))
                   for n in names[i:i + 32]]
            v = model.get_image_features(**proc(images=ims, return_tensors='pt'))
            v = v / v.norm(dim=-1, keepdim=True)
            p = (100 * v @ t.T).softmax(-1)[:, :len(ROAD)].sum(-1)
            out += [float(x) for x in p]
    return out


def main():
    recs = used_recordings()
    man = read_csv(OUT / 'manifest.csv')
    (OUT / 'contact').mkdir(parents=True, exist_ok=True)
    rows, overview = [], []
    for r in recs:
        rid = r['id']
        frames = [m['frame'] for m in man if m['recording'] == rid]
        top, bottom, _ = band_for(r)
        picks = [frames[int(i)] for i in np.linspace(0, len(frames) - 1, 8)]
        tiles = []
        for n in picks:
            im = cv2.imread(str(OUT / 'frames_full' / n))
            h = im.shape[0]
            cv2.line(im, (0, int(h * top)), (im.shape[1], int(h * top)), (0, 255, 0), 5)
            cv2.line(im, (0, int(h * bottom) - 3), (im.shape[1], int(h * bottom) - 3), (0, 0, 255), 5)
            cv2.putText(im, f'{rid} {n[5:9].lstrip("0") or "0"} s', (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.4,
                        (255, 255, 255), 6)
            tiles.append(cv2.resize(im, (480, 270)))
        sheet = np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])])
        cv2.imwrite(str(OUT / 'contact' / f'{rid}.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 82])
        overview.append(cv2.resize(np.hstack(tiles), (8 * 200, 112)))
        video = VIDEOS / r['folder'] / r['video']
        dy, ang = motion(video) if video.exists() else (None, None)
        share = clip_road_share(frames)
        rows.append(dict(id=rid, mount=r['mount'], folder=r['folder'], video_present=int(video.exists()),
                         pitch_jitter_px=round(dy, 2) if dy is not None else '',
                         roll_jitter_deg=round(ang, 3) if ang is not None else '',
                         frames=len(frames), frames_road_in_band=sum(s >= 0.5 for s in share),
                         share_road_in_band=round(sum(s >= 0.5 for s in share) / len(share), 3)))
        print(f'{rid} {r["mount"]:8} pitch {rows[-1]["pitch_jitter_px"]!s:>6} px  roll {rows[-1]["roll_jitter_deg"]!s:>6} deg  '
              f'road in band {rows[-1]["share_road_in_band"]:.0%}', flush=True)
    cv2.imwrite(str(OUT / 'contact' / 'all_recordings.jpg'), np.vstack(overview), [cv2.IMWRITE_JPEG_QUALITY, 80])

    mounted = [x for x in rows if x['mount'] == 'mounted' and x['pitch_jitter_px'] != '']
    md_p = float(np.median([x['pitch_jitter_px'] for x in mounted]))
    md_r = float(np.median([x['roll_jitter_deg'] for x in mounted]))
    for x in rows:
        f = []
        if x['pitch_jitter_px'] != '' and x['pitch_jitter_px'] > 2 * md_p:
            f.append('pitch')
        if x['roll_jitter_deg'] != '' and x['roll_jitter_deg'] > 2 * md_r:
            f.append('roll')
        x['unusually_shaky'] = ' and '.join(f)
    write_csv(OUT / 'shake_check.csv', rows)
    md = ['# Camera mount check', '',
          f'Shake: median spread of frame-to-frame vertical shift (pitch, px at 1080p) and rotation (roll, degrees) '
          f'over 12 one-second windows. Mounted medians: pitch {md_p:.2f} px, roll {md_r:.3f} deg; flagged above '
          'twice those. Road in band: share of frames whose band crop CLIP reads as road (>= 0.5).', '',
          '| Rec | Mount | Pitch jitter (px) | Roll jitter (deg) | Unusually shaky | Frames | Road in band |',
          '|---|---|---|---|---|---|---|']
    for x in rows:
        md.append(f'| {x["id"]} | {x["mount"]} | {x["pitch_jitter_px"] if x["video_present"] else "video missing"} | '
                  f'{x["roll_jitter_deg"] if x["video_present"] else "video missing"} | {x["unusually_shaky"] or "-"} | '
                  f'{x["frames"]} | {x["share_road_in_band"]:.0%} |')
    (ROOT / 'results' / 'step1_mount_check.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    sys.exit(main())

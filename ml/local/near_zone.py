"""Near zone: look only at the part of the road close enough for damage to be big enough to see.

    python ml/local/near_zone.py --propose        # analysis + figures for the team (changes nothing)
    python ml/local/near_zone.py --apply          # re-crop every kept frame to the near zone

Team decision 2026-11-10 12:05: DELTA = 0.10, R13/R14 bottom 0.73, R05 bottom stays 1.00.
--apply decodes each original video sequentially (as extract_frames.py: grab to frame
round(second * fps), upright), crops rows int(h * (band top + DELTA)) to int(h * bottom) and writes
data/local/frames_nz/<frame>.jpg (JPEG 95, 1920 px wide, no resize) for every frame in manifest.csv,
plus data/local/near_zone_bands.csv. The old crops (data/local/frames, what the review tool shows)
are untouched; build_local_yolo.py --near-zone moves the reviewed boxes into the new crops.

Every reviewed box (train/AL and val choose the rule; test is only counted) is put back into
full-frame coordinates (y + band top). On a flat road a damage's apparent size grows with its
distance below the horizon, so the rule is: near-zone top = band top (the horizon line the phone
sends as road_top) + DELTA (a fraction of the frame height); the bottom stays the band bottom,
except the changes listed in BOTTOM (R05: dashboard reflection; R13/R14: bonnet).
Writes results/near_zone_proposal.md, results/near_zone_scatter.png, results/near_zone_means.jpg.
"""

import argparse
import json
from collections import Counter, defaultdict

import cv2
import numpy as np

from common import OUT, ROOT, band_for, read_csv

CODES = ['D00', 'D10', 'D20', 'D40']
DELTAS = [0.0, 0.05, 0.075, 0.10, 0.125, 0.15]
BOTTOM = {'R13': 0.73, 'R14': 0.73}     # bonnet; R05 keeps 1.00 (team decision 2026-11-10)
DELTA = 0.10                            # team decision 2026-11-10
FRAMES_NZ = OUT / 'frames_nz'


def nz_band(rec_row):
    """(top, bottom) of the near zone for a recordings.csv row, as fractions of the frame height."""
    top, bottom, _ = band_for(rec_row)
    return round(top + DELTA, 4), BOTTOM.get(rec_row['id'], bottom)


def recrop_one(job):
    """Worker: re-crop every kept frame of one recording from its video. Returns (rec, n, top_px, bottom_px, h)."""
    from common import VIDEOS, open_upright
    rid, folder, video, top, bottom, wanted = job
    cap, rotate, w, h = open_upright(str(VIDEOS / folder / video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    targets = {round(s * fps): name for s, name in wanted}
    top_px, bottom_px = int(h * top), int(h * bottom)
    idx, n = 0, 0
    while targets and idx <= max(targets):
        if not cap.grab():
            break
        if idx in targets:
            ok, frame = cap.retrieve()
            if not ok:
                break
            if rotate is not None:
                frame = cv2.rotate(frame, rotate)
            cv2.imwrite(str(FRAMES_NZ / targets[idx]), frame[top_px:bottom_px], [cv2.IMWRITE_JPEG_QUALITY, 95])
            n += 1
        idx += 1
    cap.release()
    return rid, n, len(wanted), top_px, bottom_px, h


def apply():
    from multiprocessing import Pool
    from common import write_csv
    man = read_csv(OUT / 'manifest.csv')
    recs = {r['id']: r for r in read_csv(OUT / 'recordings.csv') if r['status'] == 'used'}
    FRAMES_NZ.mkdir(exist_ok=True)
    by = defaultdict(list)
    for m in man:
        by[m['recording']].append((int(m['second']), m['frame']))
    jobs = []
    for rid, wanted in sorted(by.items()):
        r = recs[rid]
        top, bottom = nz_band(r)
        jobs.append((rid, r['folder'], r['video'], top, bottom, sorted(wanted)))
    rows = []
    with Pool(6) as pool:
        for rid, n, want, top_px, bottom_px, h in pool.imap_unordered(recrop_one, jobs):
            r = recs[rid]
            top, bottom = nz_band(r)
            old_top, old_bottom, _ = band_for(r)
            rows.append(dict(recording=rid, video=r['video'], band_top=old_top, band_bottom=old_bottom,
                             nz_top=top, nz_bottom=bottom, frame_h=h, old_top_px=int(h * old_top),
                             nz_top_px=top_px, nz_bottom_px=bottom_px, frames=n, wanted=want))
            print(f'  {rid}: {n}/{want} frames, rows {top_px}-{bottom_px} of {h}', flush=True)
    rows.sort(key=lambda x: x['recording'])
    write_csv(OUT / 'near_zone_bands.csv', rows)
    bad = [r for r in rows if r['frames'] != r['wanted']]
    if bad:
        raise SystemExit(f'Missing frames in {[r["recording"] for r in bad]}')
    print(f'{sum(r["frames"] for r in rows)} near-zone crops in {FRAMES_NZ}')


def boxes():
    """Every reviewed box: split, recording, class, full-frame y of top/centre/bottom (fractions), height px."""
    man = {r['frame']: r for r in read_csv(OUT / 'manifest.csv')}
    split = {}
    for s in ('train', 'val', 'test'):
        for p in (OUT / 'yolo' / 'images' / s).glob('R*.jpg'):
            split[p.name] = s
    out = []
    for f, s in split.items():
        st = json.loads((OUT / 'reviewed' / 'state' / f'{f[:-4]}.json').read_text(encoding='utf-8'))
        m = man[f]
        fh, top = int(m['frame_h']), int(m['band_top_px'])
        for b in st['boxes']:
            y1, y2 = (b['y1'] + top) / fh, (b['y2'] + top) / fh
            out.append(dict(frame=f, split=s, rec=m['recording'], cls=b['cls'], y1=y1, y2=y2, yc=(y1 + y2) / 2,
                            h=b['y2'] - b['y1'], w=b['x2'] - b['x1'], band_top=float(m['band_top']),
                            band_bottom=float(m['band_bottom'])))
    return out, man


def mean_images(man):
    """Mean of every kept band crop per recording: moving road averages out, fixed things (dashboard
    reflection, bonnet) stay. Returns {rec: (mean image, band_top, band_bottom)}."""
    by = defaultdict(list)
    for f, m in man.items():
        by[m['recording']].append(f)
    res = {}
    for rec, fs in sorted(by.items()):
        acc = None
        for f in fs[::2]:
            im = cv2.imread(str(OUT / 'frames' / f)).astype(np.float32)
            acc = im if acc is None else acc + im
        res[rec] = (acc / len(fs[::2]), float(man[fs[0]]['band_top']), float(man[fs[0]]['band_bottom']))
    return res


def reflection_bottom(mean, top, bottom, fh=1080):
    """Highest row (frame fraction) of the lower half of the crop where the mean image has strong fixed
    horizontal structure (row-to-row edge energy well above the crop's median)."""
    g = cv2.cvtColor(mean.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    e = np.abs(np.diff(g, axis=1)).mean(axis=1)          # fixed vertical edges (the reflection's stripes)
    h = len(e)
    base = np.median(e[: h // 2])
    hot = [y for y in range(h // 2, h) if e[y] > 2.0 * base]
    return (int(fh * top) + hot[0]) / fh if hot else None, e, base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--propose', action='store_true')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    if a.apply:
        apply()
        return
    bx, man = boxes()
    recs = {r['id']: r for r in read_csv(OUT / 'recordings.csv') if r['status'] == 'used'}
    bands = {rid: band_for(r)[:2] for rid, r in recs.items()}

    # R05 bottom from its mean image; show every recording's mean for the team.
    means = mean_images(man)
    r05_bottom, _, _ = reflection_bottom(*means['R05'])
    bottoms = dict(BOTTOM)
    if r05_bottom:
        bottoms['R05'] = round(np.floor(r05_bottom * 100) / 100 - 0.01, 2)

    tiles = []
    for rec, (mimg, t, b) in means.items():
        im = mimg.astype(np.uint8).copy()
        fh = 1080
        h = im.shape[0]
        for d in (0.10,):
            y = int(fh * (t + d)) - int(fh * t)
            cv2.line(im, (0, y), (im.shape[1], y), (0, 200, 255), 3)
        if rec in bottoms:
            y = int(fh * bottoms[rec]) - int(fh * t)
            cv2.line(im, (0, y), (im.shape[1], y), (0, 0, 255), 3)
        im = cv2.resize(im, (640, int(h * 640 / im.shape[1])))
        head = np.full((30, 640, 3), 255, np.uint8)
        cv2.putText(head, f'{rec} band {t:.2f}-{b:.2f}' + (f'  new bottom {bottoms[rec]:.2f}' if rec in bottoms else ''),
                    (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        tiles.append(np.vstack([head, im]))
    hmax = max(t.shape[0] for t in tiles)
    tiles = [np.vstack([t, np.full((hmax - t.shape[0], 640, 3), 255, np.uint8)]) for t in tiles]
    while len(tiles) % 3:
        tiles.append(np.full((hmax, 640, 3), 255, np.uint8))
    sheet = np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)])
    cv2.imwrite(str(ROOT / 'results' / 'near_zone_means.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])

    # Scatter: box height at the model's input (imgsz 1280 -> x 2/3) vs distance below the band top.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.5))
    colors = {'D00': '#1f77b4', 'D10': '#2ca02c', 'D20': '#ff7f0e', 'D40': '#d62728'}
    for c in CODES:
        pts = [b for b in bx if b['cls'] == c and b['split'] != 'test']
        axs[0].scatter([b['yc'] - b['band_top'] for b in pts], [b['h'] * 2 / 3 for b in pts], s=12, alpha=.6,
                       c=colors[c], label=f'{c} ({len(pts)})')
        axs[1].scatter([b['yc'] for b in pts], [b['h'] * 2 / 3 for b in pts], s=12, alpha=.6, c=colors[c])
    for d in DELTAS[1:]:
        axs[0].axvline(d, color='grey', lw=.8, ls='--')
    axs[0].set_xlabel('box centre below the band top (fraction of frame height)')
    axs[1].set_xlabel('box centre position in the frame (fraction of frame height, 0 = top)')
    for ax in axs:
        ax.set_yscale('log')
        ax.set_ylabel('box height at the model input, px (imgsz 1280)')
        ax.axhline(16, color='k', lw=.6)
        ax.axhline(32, color='k', lw=.6, ls=':')
        ax.grid(alpha=.3)
    axs[0].legend(title='train + AL + val boxes')
    tops = sorted({round(t, 3) for t, _ in bands.values()})
    for t in tops:
        axs[1].axvline(t, color='purple', lw=.8, alpha=.5)
    axs[1].set_title('purple: band tops of the 18 recordings')
    axs[0].set_title('dashed: candidate DELTA')
    fig.tight_layout()
    fig.savefig(ROOT / 'results' / 'near_zone_scatter.png', dpi=110)

    # Counts lost per DELTA (a box is lost when its centre lies above the new top or below the new bottom).
    def lost(b, d):
        top = b['band_top'] + d
        bot = bottoms.get(b['rec'], b['band_bottom'])
        return b['yc'] < top or b['yc'] > bot

    md = ['# Near zone: proposal', '',
          'Rule: **near-zone top = band top + DELTA** (band top = the horizon line, `road_top`), bottom = band bottom '
          'except R05 (dashboard reflection) and R13/R14 (bonnet). A box is lost when its centre falls outside. '
          'DELTA is chosen on train + AL + val boxes; test is only counted.', '',
          '## Box size vs position', '',
          '![scatter](near_zone_scatter.png)', '',
          'Median box height at the model input (imgsz 1280), by distance below the band top (train + AL + val):', '',
          '| Below band top | Boxes | D00 | D10 | D20 | D40 | Median height px | Under 16 px | Under 32 px |', '|---|---|---|---|---|---|---|---|---|']
    edges = [0, 0.05, 0.075, 0.10, 0.125, 0.15, 0.2, 0.3, 1]
    tv = [b for b in bx if b['split'] != 'test']
    for lo, hi in zip(edges, edges[1:]):
        s = [b for b in tv if lo <= b['yc'] - b['band_top'] < hi]
        if not s:
            continue
        cc = Counter(b['cls'] for b in s)
        hs = [b['h'] * 2 / 3 for b in s]
        md.append(f'| {lo:.3f}-{hi:.3f} | {len(s)} | ' + ' | '.join(str(cc[c]) for c in CODES)
                  + f' | {np.median(hs):.0f} | {sum(h < 16 for h in hs)} | {sum(h < 32 for h in hs)} |')
    md += ['', '## Boxes lost per DELTA (with the new bottoms)', '',
           '| DELTA | Split | Kept | Lost | D00 lost | D10 lost | D20 lost | D40 lost | Kept boxes under 32 px |',
           '|---|---|---|---|---|---|---|---|---|']
    for d in DELTAS:
        for s in ('train', 'val', 'test'):
            sb = [b for b in bx if b['split'] == s]
            ls = [b for b in sb if lost(b, d)]
            kept = [b for b in sb if not lost(b, d)]
            cl = Counter(b['cls'] for b in ls)
            ct = Counter(b['cls'] for b in sb)
            md.append(f'| {d:.3f} | {s} | {len(kept)} | {len(ls)} | '
                      + ' | '.join(f'{cl[c]}/{ct[c]}' for c in CODES)
                      + f' | {sum(b["h"] * 2 / 3 < 32 for b in kept)} |')
    md += ['', '## Band tops and bottoms per recording (current -> proposed with DELTA 0.10)', '',
           '| Recording | Split | Band now | Near zone (DELTA 0.10) | Crop height now -> new (px) | Note |', '|---|---|---|---|---|---|']
    split_of = {}
    for b in bx:
        split_of.setdefault(b['rec'], b['split'])
    sp = {m['recording']: None for m in man.values()}
    for f, m in man.items():
        pass
    for s in ('train', 'val', 'test'):
        for p in (OUT / 'yolo' / 'images' / s).glob('R*.jpg'):
            sp[p.name[:3]] = s
    for rid in sorted(bands):
        t, b = bands[rid]
        nb = bottoms.get(rid, b)
        note = {'R05': f'dashboard reflection from about {r05_bottom:.2f} (mean image)' if r05_bottom else '',
                'R13': 'bonnet from about 0.74', 'R14': 'bonnet from about 0.74'}.get(rid, '')
        md.append(f'| {rid} | {sp.get(rid) or "-"} | {t:.2f}-{b:.2f} | {t + 0.10:.2f}-{nb:.2f} | '
                  f'{int(1080 * b) - int(1080 * t)} -> {int(1080 * nb) - int(1080 * (t + 0.10))} | {note} |')
    md += ['', 'Mean image of every recording (fixed things stay: reflection, bonnet), orange = near-zone top at '
           'DELTA 0.10, red = proposed new bottom: `results/near_zone_means.jpg`.']
    (ROOT / 'results' / 'near_zone_proposal.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

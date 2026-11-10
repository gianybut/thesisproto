"""Quality check of the local training/val/test images (CPU only).

    python ml/local/frame_quality.py

1. JPEG quality: what extract_frames.py writes (IMWRITE_JPEG_QUALITY) and what the files say
   (estimated from each file's luminance quantisation table against the IJG tables), plus size,
   file size and expected band crop of 5 random frames per split.
2. Fidelity: 20 random frames re-decoded from the original video by reading sequentially (grab up
   to the frame, as the extractor does; no seeking), turned upright and cropped to the same band;
   PSNR and mean absolute pixel difference against the saved image. The previous video frame is
   compared too, to show the match is the right frame and not just a similar one.
3. Sharpness (variance of the Laplacian, grey, full resolution) and blockiness (mean |horizontal
   step| on 8-px column boundaries / elsewhere; 1.0 = no block edges) for every local image in
   data/local/yolo. Outliers: below Q1 - 1.5 IQR of log sharpness, above Q3 + 1.5 IQR of
   blockiness. Contact sheet of the 12 least sharp: results/frame_quality_worst12.jpg.
Writes results/frame_quality.md and results/frame_quality.csv.
"""

import random
import re
from collections import defaultdict

import cv2
import numpy as np
from PIL import Image

from common import OUT, ROOT, VIDEOS, open_upright, read_csv, write_csv

Y = OUT / 'yolo' / 'images'
IJG_LUMA = [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56,
            14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
            49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99]


def jpeg_quality(path):
    q = Image.open(path).quantization[0]
    have = sorted(q)

    def table(qq):
        s = 5000 / qq if qq < 50 else 200 - 2 * qq
        return sorted(min(255, max(1, (v * s + 50) // 100)) for v in IJG_LUMA)
    return min(range(1, 101), key=lambda qq: sum(abs(a - b) for a, b in zip(table(qq), have)))


def blockiness(gray):
    d = np.abs(np.diff(gray.astype(np.float32), axis=1))     # d[:, x] = step between columns x and x+1
    on = d[:, 7::8].mean()
    mask = np.ones(d.shape[1], bool)
    mask[7::8] = False
    return float(on / max(d[:, mask].mean(), 1e-6))


def psnr(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return float('inf') if mse == 0 else 10 * np.log10(255 ** 2 / mse)


def main():
    rng = random.Random(42)
    man = {r['frame']: r for r in read_csv(OUT / 'manifest.csv')}
    recs = {r['id']: r for r in read_csv(OUT / 'recordings.csv')}
    src = (ROOT / 'ml' / 'local' / 'extract_frames.py').read_text(encoding='utf-8')
    saved_q = re.search(r'cv2\.imwrite\(str\(FRAMES / name\), band, \[cv2\.IMWRITE_JPEG_QUALITY, (\d+)\]', src).group(1)
    splits = {s: sorted(p.name for p in (Y / s).glob('R*.jpg')) for s in ('train', 'val', 'test')}
    md = ['# Local frame quality', '',
          f'Extractor: band crop written with `cv2.imwrite(..., [cv2.IMWRITE_JPEG_QUALITY, {saved_q}])`, no resize.', '',
          '## 1. Size and JPEG quality, 5 random frames per split', '',
          '| Split | Frame | Saved size | Video frame | Band | Expected crop | File KB | JPEG quality (from the file) |',
          '|---|---|---|---|---|---|---|---|']
    for s, names in splits.items():
        for f in rng.sample(names, 5):
            m = man[f]
            p = Y / s / f
            w, h = Image.open(p).size
            fh = int(m['frame_h'])
            exp_h = int(fh * float(m['band_bottom'])) - int(fh * float(m['band_top']))
            md.append(f'| {s} | {f} | {w}x{h} | {m["frame_w"]}x{fh} | {float(m["band_top"]):.2f}-{float(m["band_bottom"]):.2f} | '
                      f'{m["frame_w"]}x{exp_h} | {p.stat().st_size / 1024:.0f} | {jpeg_quality(p)} |')
    all_q = {jpeg_quality(Y / s / f) for s, names in splits.items() for f in names}
    all_w = {Image.open(Y / s / f).size[0] for s, names in splits.items() for f in names}
    md += ['', f'All {sum(len(v) for v in splits.values())} local images: JPEG quality {sorted(all_q)}, widths {sorted(all_w)} px.']

    # 2. fidelity against the video, sequential read
    every = [(s, f) for s, names in splits.items() for f in names]
    pick = rng.sample(every, 20)
    by_rec = defaultdict(list)
    for s, f in pick:
        by_rec[man[f]['recording']].append((s, f))
    fid = []
    for rid, items in sorted(by_rec.items()):
        rec = recs[rid]
        cap, rotate, w, h = open_upright(str(VIDEOS / rec['folder'] / rec['video']))
        fps = cap.get(cv2.CAP_PROP_FPS)
        want = {round(int(man[f]['second']) * fps): (s, f) for s, f in items}
        idx, prev = 0, None
        while want and idx <= max(want):
            if not cap.grab():
                break
            if idx in want or idx + 1 in want:
                ok, fr = cap.retrieve()
                if rotate is not None:
                    fr = cv2.rotate(fr, rotate)
                if idx in want:
                    s, f = want.pop(idx)
                    m = man[f]
                    top, bot = int(m['band_top_px']), int(h * float(m['band_bottom']))
                    saved = cv2.imread(str(Y / s / f))
                    band = fr[top:bot]
                    pband = prev[top:bot] if prev is not None else None
                    same = band.shape == saved.shape
                    fid.append((s, f, idx, same, psnr(band, saved) if same else 0.0,
                                float(np.abs(band.astype(np.int16) - saved).mean()) if same else -1,
                                psnr(pband, saved) if same and pband is not None else float('nan')))
                prev = fr
            idx += 1
        cap.release()
        print(f'  {rid}: compared {len(items)}', flush=True)
    md += ['', '## 2. Saved image vs the same frame decoded from the video (sequential read)', '',
           '| Split | Frame | Video frame no. | Same size | PSNR dB | Mean abs diff (0-255) | PSNR vs previous video frame |',
           '|---|---|---|---|---|---|---|']
    for s, f, i, same, p, d, pp in sorted(fid, key=lambda x: x[1]):
        md.append(f'| {s} | {f} | {i} | {"yes" if same else "NO"} | {p:.1f} | {d:.2f} | {pp:.1f} |')
    ps = [x[4] for x in fid]
    md.append(f'\nPSNR {min(ps):.1f}-{max(ps):.1f} dB (mean {np.mean(ps):.1f}); mean abs diff '
              f'{min(x[5] for x in fid):.2f}-{max(x[5] for x in fid):.2f}.')

    # 3. sharpness and blockiness
    rows = []
    for s, names in splits.items():
        for f in names:
            g = cv2.imread(str(Y / s / f), cv2.IMREAD_GRAYSCALE)
            rows.append({'split': s, 'frame': f, 'recording': man[f]['recording'],
                         'lap_var': round(float(cv2.Laplacian(g, cv2.CV_64F).var()), 2), 'blockiness': round(blockiness(g), 4)})
    write_csv(ROOT / 'results' / 'frame_quality.csv', rows)
    lv = np.log([r['lap_var'] for r in rows])
    q1, q3 = np.percentile(lv, [25, 75])
    lo = np.exp(q1 - 1.5 * (q3 - q1))
    bl = np.array([r['blockiness'] for r in rows])
    b1, b3 = np.percentile(bl, [25, 75])
    hi = b3 + 1.5 * (b3 - b1)
    blurry = sorted((r for r in rows if r['lap_var'] < lo), key=lambda r: r['lap_var'])
    blocky = sorted((r for r in rows if r['blockiness'] > hi), key=lambda r: -r['blockiness'])
    pct = lambda a, p: float(np.percentile(a, p))
    md += ['', '## 3. Sharpness and blockiness of every local image', '',
           '| | Min | 5% | Median | 95% | Max |', '|---|---|---|---|---|---|',
           f'| Laplacian variance | {min(r["lap_var"] for r in rows):.0f} | {pct([r["lap_var"] for r in rows], 5):.0f} | '
           f'{pct([r["lap_var"] for r in rows], 50):.0f} | {pct([r["lap_var"] for r in rows], 95):.0f} | {max(r["lap_var"] for r in rows):.0f} |',
           f'| Blockiness (1 = none) | {bl.min():.3f} | {pct(bl, 5):.3f} | {pct(bl, 50):.3f} | {pct(bl, 95):.3f} | {bl.max():.3f} |', '',
           f'Unusually blurry (Laplacian variance < {lo:.0f}): **{len(blurry)}**'
           + (': ' + ', '.join(f'{r["frame"]} ({r["split"]}, {r["lap_var"]:.0f})' for r in blurry[:40]) if blurry else '') + '.', '',
           f'Unusually blocky (blockiness > {hi:.3f}): **{len(blocky)}**'
           + (': ' + ', '.join(f'{r["frame"]} ({r["split"]}, {r["blockiness"]:.3f})' for r in blocky[:40]) if blocky else '') + '.', '',
           'By recording (median Laplacian variance): ' + ', '.join(
               f'{rid} {np.median([r["lap_var"] for r in rows if r["recording"] == rid]):.0f}'
               for rid in sorted({r['recording'] for r in rows})) + '.']

    worst = sorted(rows, key=lambda r: r['lap_var'])[:12]
    tiles = []
    for r in worst:
        im = cv2.imread(str(Y / r['split'] / r['frame']))
        im = cv2.resize(im, (800, int(im.shape[0] * 800 / im.shape[1])))
        head = np.full((36, 800, 3), 255, np.uint8)
        cv2.putText(head, f'{r["frame"]} {r["split"]}  sharpness {r["lap_var"]:.0f}  block {r["blockiness"]:.2f}',
                    (6, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
        tiles.append(np.vstack([head, im]))
    hmax = max(t.shape[0] for t in tiles)
    tiles = [np.vstack([t, np.full((hmax - t.shape[0], 800, 3), 255, np.uint8)]) for t in tiles]
    gap = np.full((hmax, 10, 3), 255, np.uint8)
    rows_img = [np.hstack([tiles[i], gap, tiles[i + 1], gap, tiles[i + 2]]) for i in range(0, 12, 3)]
    sheet = np.vstack(sum(([x, np.full((10, x.shape[1], 3), 255, np.uint8)] for x in rows_img), [])[:-1])
    cv2.imwrite(str(ROOT / 'results' / 'frame_quality_worst12.jpg'), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
    md += ['', 'Contact sheet of the 12 least sharp: `results/frame_quality_worst12.jpg`.']
    (ROOT / 'results' / 'frame_quality.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

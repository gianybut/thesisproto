"""Device tests of the mobile capture app from the recordings already made (manuscript 4.2.5, 5.5).

    python tools/device_tests.py                      # the 18 used recordings (data/local/recordings.csv + VID+GPX/)
    python tools/device_tests.py --gpx a.gpx b.gpx    # GPX files only (no video columns)

Per recording, from the files alone:
  video     duration (s), file size (MB), overall bitrate (Mbit/s = size x 8 / duration; the app asks
            for 5 Mbit/s), frame rate, resolution (ffprobe)
  GPS       fixes, achieved rate (Hz = (fixes - 1) / track span; also the app's own achievedHz), median
            interval between fixes, gaps longer than 3 s (count, longest, total), horizontal accuracy
            (mean / median / max of <bk:accuracy>, metres, 68%), GPS errors and stale fixes dropped
  sync      time offset (s, Equation 16) and clock skew (ms) as the app computed them
  parts     part number within the phone recording (recordingId), and for part N > 1 the gap between
            the end of part N-1 and the start of part N (videoStart(N) - videoStart(N-1) - duration(N-1);
            needs both parts' videos)
  ended early   a part shorter than 590 - 5 s. The app ends a part early only when the recording
            stops: by the user, or because the app left the screen. The reason (endReason) is kept on
            the phone and is not in the GPX or the video, so it cannot be told from these files; a short
            part that is followed by another part of the same recording would be an anomaly.

Not measurable from files, so not performed here: the start-time gap (filming a running stopwatch),
the midday heat test, full-length sessions observed in a moving vehicle.

Writes results/device_tests.csv and results/device_tests.md.
"""

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import DATA, RESULTS, ROOT, VIDEOS, parse_time, read_csv, read_gpx, summary, write_csv  # noqa: E402

CLIP_S = 590
GAP_S = 3.0
OVERRIDES = ROOT / 'ml' / 'local' / 'road_band_overrides.csv'


def ffprobe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', str(path)],
                       capture_output=True, text=True)
    if r.returncode:
        return {}
    info = json.loads(r.stdout)
    v = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), {})
    num, _, den = (v.get('avg_frame_rate') or '0/1').partition('/')
    return dict(duration=float(info.get('format', {}).get('duration') or 0), size=int(info.get('format', {}).get('size') or 0),
                fps=float(num) / float(den or 1) if float(den or 1) else 0.0, width=v.get('width'), height=v.get('height'),
                codec=v.get('codec_name'), audio=any(s.get('codec_type') == 'audio' for s in info.get('streams', [])))


def gps_stats(g):
    pts = g['points']
    t = [p[0] for p in pts]
    iv = [b - a for a, b in zip(t, t[1:])]
    gaps = [x for x in iv if x > GAP_S]
    acc = summary([p[3] for p in pts])
    span = t[-1] - t[0] if len(t) > 1 else 0
    return dict(fixes=len(pts), span_s=round(span, 1), rate_hz=round((len(pts) - 1) / span, 3) if span else None,
                median_interval_s=round(statistics.median(iv), 3) if iv else None,
                gaps_over_3s=len(gaps), longest_gap_s=round(max(gaps), 1) if gaps else 0, gap_total_s=round(sum(gaps), 1),
                acc_mean_m=round(acc['mean'], 2) if acc['n'] else None, acc_median_m=round(acc['median'], 2) if acc['n'] else None,
                acc_max_m=round(acc['max'], 1) if acc['n'] else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gpx', nargs='*', help='GPX files only (no videos)')
    ap.add_argument('--out', help='output stem (default results/device_tests)')
    a = ap.parse_args()
    out = Path(a.out) if a.out else RESULTS / 'device_tests'
    known = {o['video'].rsplit('.', 1)[0]: o['id'] for o in read_csv(OVERRIDES)}

    items = []
    # The public samples record each source video's full duration (export_samples.py, ffprobe of the original).
    sample_dur = {}
    sj = ROOT / 'frontend' / 'public' / 'samples' / 'samples.json'
    if sj.exists():
        for e in json.loads(sj.read_text(encoding='utf-8')):
            sample_dur[(ROOT / 'frontend' / 'public' / e['gpx'].lstrip('/')).resolve()] = float(e['full_duration_s'])
    if a.gpx:
        for p in a.gpx:
            g = read_gpx(p)
            sid = g['capture'].get('sessionId', Path(p).stem)
            items.append(dict(id=known.get(sid, ''), session=sid, gpx=Path(p), video=None,
                              duration=sample_dur.get(Path(p).resolve())))
        source = ('GPX files only (durations, where shown, from frontend/public/samples/samples.json full_duration_s; '
                  'size and bitrate need the videos): ') + ', '.join(str(Path(p).resolve().relative_to(ROOT)) if Path(p).resolve().is_relative_to(ROOT) else str(p) for p in a.gpx)
    else:
        for r in read_csv(DATA / 'recordings.csv'):
            if (r.get('status') or 'used') != 'used':
                continue
            items.append(dict(id=r['id'], session=r['video'].rsplit('.', 1)[0], gpx=VIDEOS / r['folder'] / r['gpx'],
                              video=VIDEOS / r['folder'] / r['video']))
        source = 'data/local/recordings.csv (status used) with VID+GPX/<folder>/ videos and GPX files'

    rows = []
    for it in items:
        g = read_gpx(it['gpx'])
        c = g['capture']
        row = dict(id=it['id'], session=it['session'], recording=c.get('recordingId', ''), part=c.get('part', ''),
                   video_start=c.get('videoStart', ''), platform=c.get('platform', ''))
        if it['video'] and it['video'].exists():
            f = ffprobe(it['video'])
            dur, size = f.get('duration') or 0, it['video'].stat().st_size
            row.update(duration_s=round(dur, 2), size_mb=round(size / 1e6, 1),
                       bitrate_mbps=round(size * 8 / dur / 1e6, 2) if dur else None, fps=round(f.get('fps', 0), 3),
                       resolution=f'{f.get("width")}x{f.get("height")}', codec=f.get('codec'), audio='yes' if f.get('audio') else 'no')
        elif it.get('duration'):
            row.update(duration_s=it['duration'], size_mb=None, bitrate_mbps=None, fps=None, resolution='', codec='',
                       audio='', duration_source='samples.json full_duration_s')
        else:
            row.update(duration_s=None, size_mb=None, bitrate_mbps=None, fps=None, resolution='', codec='', audio='')
        row.update(gps_stats(g), app_achieved_hz=c.get('achievedHz', ''), gps_errors=c.get('gpsErrors', ''),
                   stale_dropped=c.get('stalePointsDropped', ''), time_offset_s=c.get('timeOffsetS', ''),
                   clock_skew_ms=c.get('clockSkewMs', ''))
        rows.append(row)

    # parts: gap between consecutive parts of one phone recording, and parts that ended early
    by_rec = {}
    for r in rows:
        by_rec.setdefault(r['recording'], []).append(r)
    for parts in by_rec.values():
        parts.sort(key=lambda r: int(r['part'] or 0))
        for prev, cur in zip(parts, parts[1:]):
            if int(cur['part']) != int(prev['part']) + 1:
                cur['gap_after_previous_part_s'] = f'previous part {int(cur["part"]) - 1} not in this set'
                continue
            if prev['duration_s'] is None:
                cur['gap_after_previous_part_s'] = 'needs the videos'
                continue
            gap = (parse_time(cur['video_start']) - parse_time(prev['video_start'])).total_seconds() - prev['duration_s']
            cur['gap_after_previous_part_s'] = round(gap, 3)
        for i, r in enumerate(parts):
            r.setdefault('gap_after_previous_part_s', '' if int(r['part'] or 1) == 1 else
                         f'previous part {int(r["part"]) - 1} not in this set')
            if r['duration_s'] is None:
                r['ended_early'] = 'needs the video'
            elif r['duration_s'] < CLIP_S - 5:
                followed = i + 1 < len(parts)
                r['ended_early'] = 'yes, followed by another part (anomaly)' if followed else 'yes (last part: stopped by the user or interrupted; reason not in the files)'
            else:
                r['ended_early'] = 'no'

    rows.sort(key=lambda r: (r['video_start'], r['session']))
    fields = ['id', 'session', 'recording', 'part', 'video_start', 'duration_s', 'size_mb', 'bitrate_mbps', 'fps',
              'resolution', 'codec', 'audio', 'fixes', 'span_s', 'rate_hz', 'app_achieved_hz', 'median_interval_s',
              'gaps_over_3s', 'longest_gap_s', 'gap_total_s', 'acc_mean_m', 'acc_median_m', 'acc_max_m', 'gps_errors',
              'stale_dropped', 'time_offset_s', 'clock_skew_ms', 'gap_after_previous_part_s', 'ended_early', 'platform', 'duration_source']
    write_csv(out.with_suffix('.csv'), rows, fields)

    def f(x, nd=2):
        return '' if x in (None, '') else (f'{x:.{nd}f}' if isinstance(x, float) else str(x))
    md = ['# Device tests from the recordings (mobile capture app)', '', f'`tools/device_tests.py`. Source: {source}.', '',
          '| Rec | Part | Duration (s) | Size (MB) | Bitrate (Mbit/s) | GPS fixes | GPS rate (Hz) | Gaps > 3 s (n / longest s) | Accuracy mean / max (m) | Offset (s) | Skew (ms) | Gap after previous part (s) | Ended early |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        md.append(f'| {r["id"] or r["session"]} | {r["part"]} | {f(r["duration_s"])} | {f(r["size_mb"], 1)} | {f(r["bitrate_mbps"])} | '
                  f'{r["fixes"]} | {f(r["rate_hz"], 3)} | {r["gaps_over_3s"]} / {r["longest_gap_s"]} | {f(r["acc_mean_m"], 1)} / {f(r["acc_max_m"], 1)} | '
                  f'{r["time_offset_s"]} | {r["clock_skew_ms"]} | {f(r["gap_after_previous_part_s"], 3)} | {r["ended_early"]} |')

    def num(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    def agg(key):
        s = summary([num(r.get(key)) for r in rows])
        return (f'mean {s["mean"]:.3f}, SD {s["sd"]:.3f}, min {s["min"]:.3f}, max {s["max"]:.3f} (n = {s["n"]})' if s['n'] else 'n/a')
    md += ['', 'Across the recordings:', '',
           f'- Achieved GPS rate (Hz): {agg("rate_hz")}',
           f'- GPS gaps longer than 3 s: {sum(r["gaps_over_3s"] for r in rows)} in {sum(1 for r in rows if r["gaps_over_3s"])} of {len(rows)} recordings',
           f'- Horizontal accuracy, recording means (m): {agg("acc_mean_m")}',
           f'- Time offset (s): {agg("time_offset_s")}',
           f'- Clock skew (ms): {agg("clock_skew_ms")}',
           f'- Video bitrate (Mbit/s): {agg("bitrate_mbps")}',
           f'- Gap between consecutive parts (s): {agg("gap_after_previous_part_s")}', '',
           'Not performed (cannot be measured from the files): the video start-time gap (stopwatch filmed at the start of a '
           'recording), the midday heat test, and observed full-length sessions in a moving vehicle. Whether a part was '
           'interrupted by locking the phone is recorded only on the phone (endReason), not in the files.']
    out.with_suffix('.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

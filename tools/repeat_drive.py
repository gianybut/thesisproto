"""Positional consistency between repeat drives (RQ3 proxy, manuscript 5.4).

Not absolute accuracy: there is no surveyed reference position. Where two recordings drove the same
road, the same damage should be detected in both and placed at the same coordinates; the distance
between the two placements shows how repeatable GPS-to-video positioning is.

    python tools/repeat_drive.py find                 # which train/val recordings drove the same road
    python tools/repeat_drive.py process --password X # analyse them with the frozen deployed fusion
    python tools/repeat_drive.py pair                 # pair the detections, Haversine statistics

Run on the computer with VID+GPX/, data/local/recordings.csv and route_groups.csv, and the backend.

find     Each recording's track is sampled once per video second (GPS time = video time + offset, as
         the backend does). A pair of recordings overlaps where a sample of one lies within 15 m of
         the other's track; pairs with >= 100 m of overlap are kept. Test recordings (route groups
         G05, G13, G15: R06, R19, R21) are never used. Direction (same / opposite) is from the
         headings. Writes results/repeat_drive/overlaps.csv and .md.
process  For every recording in a kept pair, a survey analysed by the frozen deployed system is
         needed: model_config.json must equal the test-evaluated one (commit 378f0a9) with the
         second-stage classifier disabled, and the backend restarted after that. An existing survey
         of the same video analysed after 2026-11-11 13:14 (+08:00) with no classifier labels is
         reused (survey 3 = R07); otherwise the recording is uploaded with tools/upload_recording.py
         (same video, GPX, offset and road band as the phone). Writes results/repeat_drive/surveys.csv.
pair     Records of drive A inside the overlap (within 15 m of B's track) are paired one-to-one with
         records of drive B inside the overlap: same damage class, Haversine distance <= 15 m,
         greedy, closest first. Reported: number of pairs, mean, SD, median and maximum distance,
         share of overlap records paired, and the same at 5, 10, 20 and 30 m to show how much the
         15 m cut decides; per recording the GPX metadata (horizontal accuracy, achieved GPS rate,
         time offset, clock skew). Writes results/repeat_drive/pairs.csv and
         positional_consistency.md.

Caveats written into the report: a record's coordinates are the phone's position when the damage was
best seen, a few metres before the damage, so opposite-direction pairs carry about twice that
look-ahead and are reported apart; pairing within 15 m truncates the distances at 15 m and can pair
two neighbouring damages of the same class; train recordings were used to train the models, so their
detections are in-sample (this does not bias the positions, only which damages are found).
"""

import argparse
import json
import math
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import (DATA, DB, RESULTS, ROOT, VIDEOS, connect, fmt, haversine_m, read_csv, read_gpx,  # noqa: E402
                         summary, write_csv)

OUT = RESULTS / 'repeat_drive'
TEST_GROUPS = {'G05', 'G13', 'G15'}          # results/step1_split.md
TEST_RECORDINGS = {'R06', 'R19', 'R21'}      # the recordings in those groups (step1_split.md, drops table)
RADIUS_M = 15.0
MIN_OVERLAP_M = 100.0
FROZEN_COMMIT = '378f0a9'                    # model_config.json as test-evaluated (2026-11-11)
DEPLOYED_UTC = '2026-11-11 05:14:13'         # 13:14:13 +08:00


# ---------------------------------------------------------------------------------------------
def recordings(args):
    """[{id, video, gpx_path, offset, duration_s, group}] for train/val recordings only."""
    if args.gpx:   # test mode: GPX files given directly; ids = their session ids
        out = []
        for p in args.gpx:
            g = read_gpx(p)
            sid = g['capture'].get('sessionId') or Path(p).stem
            out.append(dict(id=sid, video=sid + '.mov', gpx_path=Path(p), offset=float(g['capture'].get('timeOffsetS') or 0),
                            duration_s=g['points'][-1][0] - float(g['capture'].get('timeOffsetS') or 0), group='?'))
        return out
    recs = [r for r in read_csv(DATA / 'recordings.csv') if (r.get('status') or 'used') == 'used']
    groups = {g['id']: g['route_group'] for g in read_csv(DATA / 'route_groups.csv')}
    out = []
    for r in recs:
        grp = groups.get(r['id'], '')
        if grp in TEST_GROUPS or r['id'] in TEST_RECORDINGS or not grp:
            continue
        out.append(dict(id=r['id'], video=r['video'], gpx_path=VIDEOS / r['folder'] / r['gpx'],
                        offset=float(r['time_offset_s'] or 0), duration_s=float(r['duration_s']), group=grp))
    return out


def video_track(rec):
    """[(video_s, lat, lon)] once per video second, inside the GPS track only."""
    pts = read_gpx(rec['gpx_path'])['points']
    out = []
    for s in range(int(rec['duration_s']) + 1):
        t = s + rec['offset']
        if t < pts[0][0] or t > pts[-1][0]:
            continue
        for a, b in zip(pts, pts[1:]):
            if a[0] <= t <= b[0]:
                f = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
                out.append((s, a[1] + f * (b[1] - a[1]), a[2] + f * (b[2] - a[2])))
                break
    return out


def heading(track, i):
    j, k = max(0, i - 2), min(len(track) - 1, i + 2)
    (_, la1, lo1), (_, la2, lo2) = track[j], track[k]
    return math.degrees(math.atan2((lo2 - lo1) * math.cos(math.radians(la1)), la2 - la1)) % 360


def nearest(track, lat, lon):
    best, bi = float('inf'), -1
    for i, (_, la, lo) in enumerate(track):
        if abs(la - lat) > 0.001 or abs(lo - lon) > 0.001:   # ~110 m box first
            continue
        d = haversine_m(lat, lon, la, lo)
        if d < best:
            best, bi = d, i
    return best, bi


def find(a):
    out = Path(a.out) if a.out else OUT
    recs = recordings(a)
    tracks = {r['id']: video_track(r) for r in recs}
    rows = []
    for i, ra in enumerate(recs):
        for rb in recs[i + 1:]:
            ta, tb = tracks[ra['id']], tracks[rb['id']]
            near, same, opp = [], 0, 0
            near_set = set()
            for k, (s, la, lo) in enumerate(ta):
                d, j = nearest(tb, la, lo)
                if d <= RADIUS_M:
                    near.append(k)
                    near_set.add(k)
                    diff = abs(heading(ta, k) - heading(tb, j)) % 360
                    diff = min(diff, 360 - diff)
                    same += diff < 60
                    opp += diff > 120
            length = sum(haversine_m(ta[k][1], ta[k][2], ta[k + 1][1], ta[k + 1][2]) for k in near if k + 1 in near_set)
            if length < MIN_OVERLAP_M:
                continue
            windows, start = [], None
            for k in near:
                if start is None:
                    start = prev = k
                elif k == prev + 1:
                    prev = k
                else:
                    windows.append((ta[start][0], ta[prev][0]))
                    start = prev = k
            if start is not None:
                windows.append((ta[start][0], ta[prev][0]))
            rows.append(dict(a=ra['id'], b=rb['id'], group_a=ra['group'], group_b=rb['group'], overlap_m=round(length),
                             seconds_of_a=len(near), direction='same' if same >= opp else 'opposite',
                             windows_a_s='; '.join(f'{x}-{y}' for x, y in windows if y > x)))
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / 'overlaps.csv', rows, ['a', 'b', 'group_a', 'group_b', 'overlap_m', 'seconds_of_a', 'direction', 'windows_a_s'])
    md = ['# Repeat drives: overlapping recordings (train and val only)', '',
          f'`tools/repeat_drive.py find`. Recordings considered: {", ".join(r["id"] for r in recs)} '
          f'(test route groups {", ".join(sorted(TEST_GROUPS))} excluded). Overlap = video seconds of A whose position lies '
          f'within {RADIUS_M:.0f} m of B\'s track; pairs with at least {MIN_OVERLAP_M:.0f} m kept.', '',
          '| A | B | Groups | Overlap (m) | Seconds of A | Direction |', '|---|---|---|---|---|---|'] + \
         [f'| {r["a"]} | {r["b"]} | {r["group_a"]}/{r["group_b"]} | {r["overlap_m"]} | {r["seconds_of_a"]} | {r["direction"]} |' for r in rows]
    if not rows:
        md.append('| none | | | | | |')
    (out / 'overlaps.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


# ---------------------------------------------------------------------------------------------
def frozen_config_ok():
    cur = json.loads((ROOT / 'ml' / 'models' / 'model_config.json').read_text(encoding='utf-8'))
    frozen = json.loads(subprocess.run(['git', 'show', f'{FROZEN_COMMIT}:ml/models/model_config.json'], cwd=ROOT,
                                       capture_output=True, text=True, check=True).stdout)
    if (cur.get('classifier') or {}).get('enabled'):
        return 'the second-stage classifier is enabled in ml/models/model_config.json (set "enabled": false and restart the backend)'
    diff = [k for k in set(cur) | set(frozen) if k != 'classifier' and cur.get(k) != frozen.get(k)]
    return f'model_config.json differs from the test-evaluated one ({FROZEN_COMMIT}) in: {diff}' if diff else None


def process(a):
    problem = frozen_config_ok()
    if problem:
        sys.exit(f'Not the frozen deployed system: {problem}.')
    pairs = read_csv(OUT / 'overlaps.csv')
    needed = sorted({p['a'] for p in pairs} | {p['b'] for p in pairs}, key=lambda x: int(x[1:]))
    by_id = {r['id']: r for r in recordings(a)}
    con = connect(a.db)
    rows = []
    for rid in needed:
        video = by_id[rid]['video']
        found = con.execute(
            "select v.id from videos v where v.original_filename = ? and v.status = 'completed' and v.processed_date >= ? "
            "and not exists (select 1 from detections d where d.video_id = v.id and d.classification_type is not null) "
            "order by v.id desc", (video, DEPLOYED_UTC)).fetchone()
        if found:
            rows.append(dict(recording=rid, video=video, survey_id=found['id'], how='existing survey'))
            continue
        cmd = [sys.executable, str(ROOT / 'tools' / 'upload_recording.py'), rid, '--server', a.server, '--user', a.user]
        if a.password:
            cmd += ['--password', a.password]
        print('>', ' '.join(cmd[:-1] + ['***'] if a.password else cmd))
        if subprocess.run(cmd).returncode:
            sys.exit(f'Upload of {rid} failed; surveys done so far are in the database.')
        sid = con.execute("select max(id) from videos where original_filename = ?", (video,)).fetchone()[0]
        rows.append(dict(recording=rid, video=video, survey_id=sid, how=f'uploaded {datetime.now():%Y-%m-%d %H:%M}'))
    for r in rows:
        n_cls = con.execute('select count(*) from detections where video_id = ? and classification_type is not null',
                            (r['survey_id'],)).fetchone()[0]
        if n_cls:
            sys.exit(f'Survey {r["survey_id"]} ({r["recording"]}) carries classifier labels: the backend was not restarted '
                     f'with the classifier off. Delete that survey, restart the backend, run again.')
    write_csv(OUT / 'surveys.csv', rows)
    print(f'{len(rows)} surveys -> {OUT / "surveys.csv"}')


# ---------------------------------------------------------------------------------------------
def pair(a):
    out = Path(a.out) if a.out else OUT
    overlaps = read_csv(Path(a.overlaps) if a.overlaps else OUT / 'overlaps.csv')
    surveys = {r['recording']: int(r['survey_id']) for r in read_csv(Path(a.surveys) if a.surveys else OUT / 'surveys.csv')}
    recs = {r['id']: r for r in recordings(a)}
    con = connect(a.db)
    tracks = {rid: video_track(recs[rid]) for rid in surveys if rid in recs}

    def records(rid):
        return [dict(id=d['id'], code=d['damage_type'], t=d['timestamp'], lat=d['latitude'], lon=d['longitude'])
                for d in con.execute('select * from detections where video_id = ? and latitude is not null', (surveys[rid],))]

    all_pairs, per_pair = [], []
    for ov in overlaps:
        A, B = ov['a'], ov['b']
        if A not in surveys or B not in surveys:
            continue
        ra = [r for r in records(A) if nearest(tracks[B], r['lat'], r['lon'])[0] <= RADIUS_M]
        rb = [r for r in records(B) if nearest(tracks[A], r['lat'], r['lon'])[0] <= RADIUS_M]
        cand = sorted((haversine_m(x['lat'], x['lon'], y['lat'], y['lon']), i, j)
                      for i, x in enumerate(ra) for j, y in enumerate(rb) if x['code'] == y['code'])
        by_radius = {}
        for radius in (5, 10, 15, 20, 30):
            ua, ub, got = set(), set(), []
            for d, i, j in cand:
                if d > radius:
                    break
                if i in ua or j in ub:
                    continue
                ua.add(i)
                ub.add(j)
                got.append((d, i, j))
            by_radius[radius] = got
        for d, i, j in by_radius[int(RADIUS_M)]:
            x, y = ra[i], rb[j]
            all_pairs.append(dict(a=A, b=B, direction=ov['direction'], code=x['code'], record_a=x['id'], record_b=y['id'],
                                  time_a_s=f'{x["t"]:.2f}', time_b_s=f'{y["t"]:.2f}', distance_m=f'{d:.2f}'))
        per_pair.append(dict(A=A, B=B, direction=ov['direction'], overlap_m=ov['overlap_m'], in_a=len(ra), in_b=len(rb),
                             **{f'pairs_{r}m': len(v) for r, v in by_radius.items()},
                             **{f'mean_{r}m': (sum(p[0] for p in v) / len(v)) if v else None for r, v in by_radius.items()}))
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / 'pairs.csv', all_pairs, ['a', 'b', 'direction', 'code', 'record_a', 'record_b', 'time_a_s', 'time_b_s', 'distance_m'])

    def stats_line(label, ds):
        s = summary(ds)
        return (f'| {label} | {s["n"]} | ' + (f'{s["mean"]:.2f} | {s["sd"]:.2f} | {s["median"]:.2f} | {s["max"]:.2f} |'
                                              if s['n'] else 'n/a | n/a | n/a | n/a |'))
    dist = [float(p['distance_m']) for p in all_pairs]
    md = ['# Positional consistency between repeat drives', '',
          '`tools/repeat_drive.py pair`. This is the distance between the positions the system gave to the same '
          'damage on two drives of the same road. It is repeatability, not absolute accuracy: no reference '
          'position was surveyed.', '',
          f'Pairing: same damage class, Haversine distance <= {RADIUS_M:.0f} m, one-to-one, closest first; only records '
          f'inside the overlap (within {RADIUS_M:.0f} m of the other drive\'s track).', '',
          '| Pairs | n | Mean (m) | SD (m) | Median (m) | Max (m) |', '|---|---|---|---|---|---|',
          stats_line('All', dist),
          stats_line('Same direction', [float(p['distance_m']) for p in all_pairs if p['direction'] == 'same']),
          stats_line('Opposite direction', [float(p['distance_m']) for p in all_pairs if p['direction'] == 'opposite']),
          '', 'Per recording pair, and how much the 15 m cut decides (pairs found and their mean distance at each radius):', '',
          '| A | B | Direction | Overlap (m) | Records in overlap A / B | Pairs 5 / 10 / 15 / 20 / 30 m | Mean at 15 m | Share of A paired (15 m) |',
          '|---|---|---|---|---|---|---|---|'] + \
         [f'| {p["A"]} | {p["B"]} | {p["direction"]} | {p["overlap_m"]} | {p["in_a"]} / {p["in_b"]} | '
          f'{p["pairs_5m"]} / {p["pairs_10m"]} / {p["pairs_15m"]} / {p["pairs_20m"]} / {p["pairs_30m"]} | '
          f'{fmt(p["mean_15m"])} | {(100 * p["pairs_15m"] / p["in_a"]):.0f}% |' if p['in_a'] else
          f'| {p["A"]} | {p["B"]} | {p["direction"]} | {p["overlap_m"]} | 0 / {p["in_b"]} | - | - | - |' for p in per_pair]
    md += ['', 'GPS conditions of each recording (GPX metadata written by the phone app):', '',
           '| Recording | Survey | Points | Achieved GPS rate (Hz) | Horizontal accuracy mean / median / max (m) | Time offset (s) | Clock skew (ms) |',
           '|---|---|---|---|---|---|---|']
    for rid in sorted(surveys, key=lambda x: (len(x), x)):
        if rid not in recs:
            continue
        g = read_gpx(recs[rid]['gpx_path'])
        acc = summary([p[3] for p in g['points']])
        c = g['capture']
        md.append(f'| {rid} | {surveys[rid]} | {len(g["points"])} | {c.get("achievedHz", "")} | '
                  + (f'{acc["mean"]:.1f} / {acc["median"]:.1f} / {acc["max"]:.1f}' if acc['n'] else 'n/a')
                  + f' | {c.get("timeOffsetS", "")} | {c.get("clockSkewMs", "")} |')
    md += ['', 'Caveats:', '',
           '- A record\'s coordinates are the phone\'s position when the damage was best seen, a few metres before the '
           'damage. Two drives in the same direction share that look-ahead; drives in opposite directions place the same '
           'damage about twice the look-ahead apart, so they are reported separately.',
           f'- Pairs are only formed within {RADIUS_M:.0f} m, so larger disagreements are not counted, and two neighbouring '
           'damages of the same class can be paired by mistake. The 5-30 m columns show how the result depends on the cut.',
           '- Train recordings were used to train the models, so which damages are detected there is in-sample. The '
           'positions do not depend on that.',
           f'- Per-pair distances: `{(out / "pairs.csv").relative_to(ROOT) if out.is_relative_to(ROOT) else out / "pairs.csv"}`.']
    (out / 'positional_consistency.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('find', 'process', 'pair'):
        s = sub.add_parser(name)
        s.add_argument('--gpx', nargs='*', help='test mode: GPX files instead of recordings.csv')
        s.add_argument('--db', default=str(DB))
        if name == 'process':
            s.add_argument('--server', default='http://localhost:5000')
            s.add_argument('--user', default='admin')
            s.add_argument('--password')
        s.add_argument('--out', help='output folder (default results/repeat_drive)')
        if name == 'pair':
            s.add_argument('--overlaps')
            s.add_argument('--surveys')
    a = ap.parse_args()
    {'find': find, 'process': process, 'pair': pair}[a.cmd](a)


if __name__ == '__main__':
    main()

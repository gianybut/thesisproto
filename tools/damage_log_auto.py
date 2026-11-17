"""Automatic checks of the damage log sample (RQ2, manuscript 5.3), before the review by hand.

    python tools/damage_log_auto.py                      # survey 3 (R07), the committed checklist
    python tools/damage_log_auto.py --video 3 --checklist results/damage_log_check/survey3_checklist.csv

For each of the 50 records in the checklist it computes, from data only:

  time      Is the record's time its frame divided by the frame rate (Formula 13: t = f / FPS), and
            does the frame exist in the video? With the backend database: stored timestamp vs
            frame_number / videos.fps (exact, tolerance 1 ms) and frame_number <= the video's frame
            count. Without it: the checklist's time (rounded to 0.1 s) must fit frame / FPS for one
            frame rate shared by all 50 records (tolerance 0.05 s).
  location  Are the record's coordinates the GPS track at its time? The track is interpolated at
            time + time_offset exactly as backend interpolate_gps() does; reported are the distance
            between the record and that point ("sync error", m) and the record's shortest distance
            to the route ("route distance", m). Consistent = sync error <= 1 m + the distance the
            vehicle covers in the time rounding (0.05 s without the database, 0 with it), and the
            point not clamped to a track end.
  duplicate A duplicate candidate is another record of the same survey with the same damage class,
            within 15 m (Haversine) and within 5 s of video time. With the database all records of
            the survey are compared; without it only the 50 sampled ones (a lower bound).

These checks test that the stored time and position follow from the frame and the track. They do
not show that the damage is really at that place: that is the reviewer's call on the review page
(tools/review_log/server.py), which starts from these results.

Data used, in order of preference: the backend database (backend/pothole_detection.db; the survey
must be R07's video, 20261031T021049-3x76.mov, and every checklist record must still exist with the
same frame, or the script stops: re-analysing a survey replaces its records); otherwise the
checklist itself plus R07's GPX (frontend/public/samples/alfonso-bayan-national-road/track.gpx, whose
sessionId is R07) and the GPX's timeOffsetS.

Writes results/damage_log_check/survey<id>_autocheck.csv and _autocheck.md.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import (DB, R07_GPX_IN_REPO, R07_VIDEO, RESULTS, UPLOADS, connect, distance_to_route_m, fmt,  # noqa: E402
                         haversine_m, interpolate_clamped, read_csv, read_gpx, speed_at, summary, survey,
                         survey_track, write_csv)

DUP_RADIUS_M = 15.0
DUP_WINDOW_S = 5.0
SYNC_TOL_M = 1.0


def rel(p):
    try:
        return Path(p).resolve().relative_to(RESULTS.parent)
    except ValueError:
        return p


def code_of(type_text):
    return type_text.rsplit('(', 1)[-1].rstrip(')').strip() if '(' in type_text else type_text.strip()


def video_frame_count(path):
    try:
        import cv2
    except ImportError:
        return None
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    return n or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', type=int, default=3)
    ap.add_argument('--checklist', default=str(RESULTS / 'damage_log_check' / 'survey3_checklist.csv'))
    ap.add_argument('--db', default=str(DB))
    ap.add_argument('--expect-video', default=R07_VIDEO, help='original file name the survey must have')
    ap.add_argument('--gpx', default=str(R07_GPX_IN_REPO), help='GPX used when the database is not usable')
    ap.add_argument('--no-db', action='store_true', help='ignore the database even if it holds the survey')
    ap.add_argument('--out', help='output stem (default results/damage_log_check/survey<id>_autocheck)')
    a = ap.parse_args()

    rows = read_csv(a.checklist)
    out_stem = Path(a.out) if a.out else RESULTS / 'damage_log_check' / f'survey{a.video}_autocheck'
    notes = []

    # --- data source --------------------------------------------------------------------------
    use_db, con, v = False, None, None
    if not a.no_db and Path(a.db).exists():
        con = connect(a.db)
        v = survey(con, a.video)
        if v is not None and v['original_filename'] == a.expect_video:
            use_db = True
        else:
            notes.append(f'The database at {a.db} does not hold survey {a.video} as {a.expect_video} '
                         f'(it has {v["original_filename"] if v else "no such survey"}); it was not used.')
    if use_db:
        recs = {r['id']: r for r in con.execute('select * from detections where video_id = ?', (a.video,))}
        missing = [r['record_id'] for r in rows if int(r['record_id']) not in recs]
        moved = [r['record_id'] for r in rows if int(r['record_id']) in recs
                 and recs[int(r['record_id'])]['frame_number'] != int(r['frame'])]
        if missing or moved:
            sys.exit(f'The checklist no longer matches survey {a.video}: records missing {missing}, frame changed '
                     f'{moved}. The survey was probably analysed again; the checklist must not be re-drawn '
                     f'silently. Stop and decide with the team.')
        fps = float(v['fps'])
        offset = float(v['time_offset'] or 0)
        track = survey_track(con, a.video)
        if not track:
            sys.exit(f'Survey {a.video} has no stored GPS track.')
        all_recs = list(recs.values())
        frame_count = video_frame_count(UPLOADS / v['filename'])
        time_tol = 0.001
        round_s = 0.0
        source = (f'backend database {a.db} (survey {a.video} = {v["original_filename"]}, fps {fps:.4f}, '
                  f'time offset {offset} s, {len(track)} stored track points, {len(all_recs)} records)')
        if frame_count is None:
            notes.append(f'The uploaded video {v["filename"]} could not be opened, so frame <= frame count was not checked.')
    else:
        g = read_gpx(a.gpx)
        cap = g['capture']
        if cap.get('sessionId') and a.expect_video.startswith(cap['sessionId']) is False:
            sys.exit(f'{a.gpx} is session {cap.get("sessionId")}, not {a.expect_video}.')
        track = g['points']
        offset = float(cap.get('timeOffsetS') or 0)
        all_recs = None
        frame_count = None
        time_tol = 0.05
        round_s = 0.05
        # Frame rates consistent with every row: f / (t + 0.05) <= FPS <= f / (t - 0.05)
        lo = max(int(r['frame']) / (float(r['time_s']) + time_tol) for r in rows)
        hi = min(int(r['frame']) / (float(r['time_s']) - time_tol) for r in rows if float(r['time_s']) > time_tol)
        fps = (lo + hi) / 2 if lo <= hi else None
        source = (f'checklist `{rel(a.checklist)}` (times rounded to 0.1 s) and GPX `{rel(a.gpx)}` (session {cap.get("sessionId")}, '
                  f'{len(track)} points, timeOffsetS {offset}); the backend database was not available')
        notes.append(f'Frame rates consistent with all {len(rows)} (frame, time) pairs: {lo:.4f} to {hi:.4f} fps'
                     + ('' if lo <= hi else ' - EMPTY: no single frame rate fits every record') + '.')
        notes.append('Duplicates were looked for among the 50 sampled records only (no database): a lower bound. '
                     'Run this script on the computer that holds survey 3 for the full check.')

    # --- per record ---------------------------------------------------------------------------
    out = []
    for r in rows:
        rid, frame = int(r['record_id']), int(r['frame'])
        code = code_of(r['type'])
        if use_db:
            d = recs[rid]
            t, lat, lon = float(d['timestamp']), d['latitude'], d['longitude']
        else:
            t, lat, lon = float(r['time_s']), float(r['latitude']), float(r['longitude'])
        # time
        expected_t = frame / fps if fps else None
        dt = None if expected_t is None else t - expected_t
        time_ok = dt is not None and abs(dt) <= time_tol and (frame_count is None or 1 <= frame <= frame_count)
        # location
        ilat, ilon, clamped = interpolate_clamped(track, t, offset)
        sync_err = haversine_m(lat, lon, ilat, ilon)
        route_d = distance_to_route_m(lat, lon, track)
        spd = speed_at(track, t + offset)
        tol = SYNC_TOL_M + spd * round_s
        loc_ok = sync_err <= tol and not clamped
        # duplicates
        pool = ([dict(id=q['id'], code=q['damage_type'], t=q['timestamp'], lat=q['latitude'], lon=q['longitude'])
                 for q in all_recs] if use_db else
                [dict(id=int(q['record_id']), code=code_of(q['type']), t=float(q['time_s']),
                      lat=float(q['latitude']), lon=float(q['longitude'])) for q in rows])
        cands = []
        for q in pool:
            if q['id'] == rid or q['code'] != code or q['lat'] is None:
                continue
            dist = haversine_m(lat, lon, q['lat'], q['lon'])
            if dist <= DUP_RADIUS_M and abs(q['t'] - t) <= DUP_WINDOW_S:
                cands.append((dist, q['id'], q['t'] - t))
        cands.sort()
        out.append(dict(
            item=r['item'], record_id=rid, type=code, time_s=f'{t:.3f}', frame=frame,
            expected_time_s=fmt(expected_t, 3), time_diff_s=fmt(dt, 3), time_auto='yes' if time_ok else 'no',
            latitude=f'{lat:.7f}', longitude=f'{lon:.7f}', track_lat=f'{ilat:.7f}', track_lon=f'{ilon:.7f}',
            clamped_to_track_end='yes' if clamped else 'no', speed_mps=f'{spd:.1f}',
            sync_error_m=f'{sync_err:.2f}', sync_tolerance_m=f'{tol:.2f}', route_distance_m=f'{route_d:.2f}',
            location_auto='yes' if loc_ok else 'no',
            duplicate_auto='yes' if cands else 'no',
            duplicate_candidates='; '.join(f'{cid} ({dist:.1f} m, {dts:+.1f} s)' for dist, cid, dts in cands),
            duplicate_of_auto=str(cands[0][1]) if cands else '',
            check_source='database' if use_db else 'checklist+gpx (duplicates among the sample only)'))

    fields = list(out[0].keys())
    write_csv(out_stem.with_suffix('.csv'), out, fields)

    # --- summary ------------------------------------------------------------------------------
    n = len(out)
    t_ok = sum(o['time_auto'] == 'yes' for o in out)
    l_ok = sum(o['location_auto'] == 'yes' for o in out)
    dups = [o for o in out if o['duplicate_auto'] == 'yes']
    se = summary([float(o['sync_error_m']) for o in out])
    rd = summary([float(o['route_distance_m']) for o in out])
    md = [f'# Damage log: automatic checks of the survey {a.video} sample', '',
          f'Written by `tools/damage_log_auto.py`. Source: {source}.', '',
          f'Checklist: `{rel(a.checklist)}` ({n} records, drawn at random with seed 42 by `tools/damage_log_check.py export`).', '',
          '| Check | Consistent | Not consistent | Definition |', '|---|---|---|---|',
          f'| Time | {t_ok} | {n - t_ok} | stored time = frame / FPS (Formula 13) within {time_tol} s'
          + (', frame within the video' if use_db else '') + ' |',
          f'| Location | {l_ok} | {n - l_ok} | record within (1 m + speed x {round_s} s) of the track interpolated at time + offset, not clamped |',
          f'| Duplicate candidate | {len(dups)} | {n - len(dups)} | another record, same class, <= {DUP_RADIUS_M:.0f} m and <= {DUP_WINDOW_S:.0f} s'
          + (' (all records of the survey)' if use_db else ' (among the 50 sampled records only)') + ' |', '',
          f'Sync error (record vs track at its time), m: mean {se["mean"]:.3f}, SD {se["sd"]:.3f}, max {se["max"]:.3f} (n = {se["n"]}).',
          f'Distance from record to the route, m: mean {rd["mean"]:.3f}, SD {rd["sd"]:.3f}, max {rd["max"]:.3f}.', '']
    if dups:
        md += ['Duplicate candidates (to be confirmed on the review page):', ''] + \
              [f'- item {o["item"]}, record {o["record_id"]} ({o["type"]}, {float(o["time_s"]):.1f} s): {o["duplicate_candidates"]}'
               for o in dups] + ['']
    bad = [o for o in out if o['time_auto'] == 'no' or o['location_auto'] == 'no']
    if bad:
        md += ['Records not consistent:', ''] + \
              [f'- item {o["item"]}, record {o["record_id"]}: time diff {o["time_diff_s"]} s, sync error {o["sync_error_m"]} m'
               f' (tolerance {o["sync_tolerance_m"]}), clamped {o["clamped_to_track_end"]}' for o in bad] + ['']
    md += ['Notes:', ''] + [f'- {x}' for x in notes] + \
          ['- These are consistency checks: they show the stored time and position follow from the frame and the GPS '
           'track as the method intends. Whether the damage is really at that time and place is decided by the reviewer.',
           f'- Per-record values: `{rel(out_stem.with_suffix(".csv"))}`.']
    out_stem.with_suffix('.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()

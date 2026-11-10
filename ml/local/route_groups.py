"""Step 1.2: group recordings that cover the same road, so a road never ends up in two splits.

    python ml/local/route_groups.py [--min-share 0.20] [--radius-m 30]

Two recordings share a route group when at least --min-share of one track (its 1-per-second
positions during the video) lies within --radius-m of the other track, in either direction (so
opposite-direction drives of one road merge). A folder named "... Part N ..." joins the clip
before it in the same capture session, which must carry the same road name before "Part".
Groups are the connected components of those links.

Reads data/local/recordings.csv (ingest_local.py). Writes data/local/route_groups.csv,
route_overlap.csv (every pair with any shared stretch) and route_groups.html (Leaflet map, one
colour per group). Edit route_groups.csv by hand if the team changes a group; later steps read it.
"""

import argparse
import json
import math
import re
import sys

import numpy as np

from common import OUT, VIDEOS, refuse_overwrite, used_recordings, position_at, read_csv, read_gpx, write_csv

COLORS = ['#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6', '#9a6324',
          '#000075', '#808000', '#800000', '#469990', '#bfef45', '#fabed4', '#dcbeff', '#a9a9a9',
          '#ffe119', '#aaffc3', '#ffd8b1', '#000000', '#fffac8']


def tracks(recs):
    out = {}
    for r in recs:
        pts, _ = read_gpx(VIDEOS / r['folder'] / r['gpx'])
        off = float(r['time_offset_s'] or 0)
        seq = [position_at(pts, s, off) for s in range(int(float(r['duration_s'])) + 1)]
        out[r['id']] = np.array([p for p in seq if p])
    return out


def to_metres(latlon, lat0):
    k = 111_320.0
    return np.column_stack([latlon[:, 0] * k, latlon[:, 1] * k * math.cos(math.radians(lat0))])


def near_share(a, b, radius):
    """Share of a's points within radius of any point of b (both in metres)."""
    near = np.zeros(len(a), bool)
    for i in range(0, len(a), 256):
        d2 = ((a[i:i + 256, None, :] - b[None, :, :]) ** 2).sum(-1)
        near[i:i + 256] = d2.min(1) <= radius ** 2
    return near.mean() if len(a) else 0.0


def base_name(folder):
    """Road name before 'Part N', without a trailing time like '10_40' or '11_00'."""
    name = re.split(r'\bpart\s*\d+', folder, flags=re.I)[0]
    return re.sub(r'[\s_]*\d{1,2}_\d{2}(AM|PM)?\s*$', '', name, flags=re.I).strip(' -_,').lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-share', type=float, default=0.20)
    ap.add_argument('--radius-m', type=float, default=30.0)
    a = ap.parse_args()

    refuse_overwrite(OUT / 'route_groups.csv', 'the route groups the team confirmed on 2026-11-09')
    recs = used_recordings()
    by_id = {r['id']: r for r in recs}
    tr = tracks(recs)
    lat0 = float(np.mean(np.vstack(list(tr.values()))[:, 0]))
    m = {k: to_metres(v, lat0) for k, v in tr.items()}

    parent = {r['id']: r['id'] for r in recs}
    reasons = {r['id']: [] for r in recs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[max(rx, ry)] = min(rx, ry)

    overlap_rows = []
    ids = [r['id'] for r in recs]
    for i, x in enumerate(ids):
        for y in ids[i + 1:]:
            sxy, syx = near_share(m[x], m[y], a.radius_m), near_share(m[y], m[x], a.radius_m)
            if max(sxy, syx) > 0:
                linked = max(sxy, syx) >= a.min_share
                overlap_rows.append(dict(a=x, b=y, share_of_a_near_b=round(sxy, 3), share_of_b_near_a=round(syx, 3),
                                         linked=int(linked), folder_a=by_id[x]['folder'], folder_b=by_id[y]['folder']))
                if linked:
                    union(x, y)
                    reasons[x].append(f'{y} overlap {max(sxy, syx):.0%}')
                    reasons[y].append(f'{x} overlap {max(sxy, syx):.0%}')

    # "Part N" folders join the previous clip of the same capture session with the same road name.
    for r in recs:
        mt = re.search(r'\bpart\s*(\d+)', r['folder'], flags=re.I)
        if not mt:
            continue
        prev = [q for q in recs if q['capture_recording_id'] == r['capture_recording_id']
                and q['capture_part'] and r['capture_part'] and int(q['capture_part']) == int(r['capture_part']) - 1]
        prev = [q for q in prev if base_name(q['folder']) == base_name(r['folder'])]
        if prev:
            union(r['id'], prev[0]['id'])
            reasons[r['id']].append(f'Part {mt.group(1)} of {prev[0]["id"]}')
            reasons[prev[0]['id']].append(f'{r["id"]} is its Part {mt.group(1)}')
        else:
            print(f'WARNING: {r["id"]} "{r["folder"]}" is a Part folder but its first part was not found')

    roots = sorted({find(i) for i in ids}, key=lambda x: int(x[1:]))
    gid = {root: f'G{n:02d}' for n, root in enumerate(roots, 1)}
    total_s = sum(float(r['duration_s']) for r in recs)
    rows = []
    for r in recs:
        rows.append(dict(id=r['id'], route_group=gid[find(r['id'])], duration_s=r['duration_s'],
                         joined_by='; '.join(reasons[r['id']]), capture_session=r['capture_recording_id'],
                         capture_part=r['capture_part'], folder=r['folder']))
    write_csv(OUT / 'route_groups.csv', rows)
    write_csv(OUT / 'route_overlap.csv', overlap_rows or [dict(a='', b='')])

    print(f'Rule: share >= {a.min_share:.0%} of one track within {a.radius_m:.0f} m of the other, either direction; '
          f'"Part N" folders join their first part.\n')
    for g in sorted(set(gid.values())):
        members = [x for x in rows if x['route_group'] == g]
        secs = sum(float(x['duration_s']) for x in members)
        print(f'{g}  {secs / 60:5.1f} min  ({secs / total_s:5.1%} of video)')
        for x in members:
            print(f'      {x["id"]}  {x["folder"]}' + (f'   <- {x["joined_by"]}' if x['joined_by'] else ''))
    near_misses = [o for o in overlap_rows if not o['linked'] and max(o['share_of_a_near_b'], o['share_of_b_near_a']) >= 0.05]
    if near_misses:
        print('\nShared stretches below the threshold (not merged):')
        for o in near_misses:
            print(f'      {o["a"]}-{o["b"]}: {o["share_of_a_near_b"]:.0%} / {o["share_of_b_near_a"]:.0%}  '
                  f'({o["folder_a"]} / {o["folder_b"]})')
    write_map(rows, tr, gid)
    print(f'\nWrote {OUT / "route_groups.csv"}, route_overlap.csv, route_groups.html')


def write_map(rows, tr, gid):
    groups = sorted(set(gid.values()))
    color = {g: COLORS[i % len(COLORS)] for i, g in enumerate(groups)}
    feats = [dict(id=r['id'], group=r['route_group'], folder=r['folder'], color=color[r['route_group']],
                  path=[[round(p[0], 6), round(p[1], 6)] for p in tr[r['id']][::2]]) for r in rows]
    legend = ''.join(
        f'<div><span style="background:{color[g]}"></span><b>{g}</b> '
        f'{", ".join(r["id"] for r in rows if r["route_group"] == g)}</div>' for g in groups)
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Route groups</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body {{ margin: 0; height: 100%; font: 14px/1.4 system-ui, sans-serif; background: #f6f8fb; color: #1b2430; }}
  #map {{ position: absolute; inset: 0; }}
  .legend {{ position: absolute; z-index: 1000; top: 12px; right: 12px; background: #fff; padding: 10px 12px;
            border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.25); max-height: 85vh; overflow: auto; }}
  .legend span {{ display: inline-block; width: 14px; height: 14px; border-radius: 3px; margin-right: 6px;
                 vertical-align: -2px; }}
</style></head><body>
<div id="map"></div>
<div class="legend"><b>Route groups</b> (hover a line for its recording){legend}</div>
<script>
const feats = {json.dumps(feats)};
const map = L.map('map');
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'}}).addTo(map);
const all = [];
for (const f of feats) {{
  if (!f.path.length) continue;
  L.polyline(f.path, {{color: f.color, weight: 5, opacity: .8}}).addTo(map)
    .bindTooltip(`${{f.id}} · ${{f.group}} · ${{f.folder}}`, {{sticky: true}});
  L.circleMarker(f.path[0], {{radius: 5, color: f.color, fillOpacity: 1}}).addTo(map)
    .bindTooltip(`${{f.id}} start`);
  all.push(...f.path);
}}
map.fitBounds(all);
</script></body></html>
'''
    (OUT / 'route_groups.html').write_text(html, encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())

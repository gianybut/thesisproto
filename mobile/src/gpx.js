// GPX 1.1 writer and t_offset calculation. Pure functions, no Expo imports, so
// they can be exercised under plain Node (see scripts/check-gpx.mjs).

const NS_EXT = 'urn:bantay-kalsada:capture:1';

const esc = (v) =>
  String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const iso = (ms) => new Date(ms).toISOString();

const median = (xs) => {
  if (!xs.length) return 0;
  const a = [...xs].sort((x, y) => x - y);
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
};

/**
 * Sort by fix time and drop duplicates (Android can deliver a batch that
 * repeats a timestamp).
 */
export function cleanPoints(points) {
  const out = [];
  let last = -Infinity;
  for (const p of [...points].sort((a, b) => a.t - b.t)) {
    if (p.t > last) {
      out.push(p);
      last = p.t;
    }
  }
  return out;
}

/**
 * Drop cached fixes at the start of the track. When updates start, both iOS and
 * Android may first hand over the last known location, whose fix time can be
 * seconds to hours old. Such a point shows as delivery lag (rx - t) far above
 * the session's typical lag. Only the leading run is checked: later fixes can
 * legitimately arrive late in a batch.
 */
export function dropStalePoints(points, toleranceMs = 5000) {
  if (points.length < 3) return { points, dropped: 0 };
  const typicalLag = median(points.map((p) => p.rx - p.t));
  let i = 0;
  while (i < points.length - 1 && points[i].rx - points[i].t > typicalLag + toleranceMs) i++;
  return { points: points.slice(i), dropped: i };
}

/**
 * Work out the value to send as the backend's `time_offset`.
 *
 * The backend normalises the GPX to seconds-from-first-point and looks up
 * gps_time = video_time + time_offset (backend/services/gps_service.py), so
 *
 *     time_offset = video_start - first_point_time      (same clock, seconds)
 *
 * GPX timestamps are fix times (GNSS-derived where the provider supplies them);
 * the video start is read from the device clock. `skewMs` is the median of
 * (device receipt time - fix time) over all points, which converts the device
 * clock onto the fix clock. It also absorbs the delivery latency of each fix,
 * typically well under a second.
 */
export function computeTimeOffset(points, videoStartDeviceMs) {
  if (!points.length) return { timeOffsetS: 0, skewMs: 0 };
  const skewMs = median(points.map((p) => p.rx - p.t));
  const videoStartFixMs = videoStartDeviceMs - skewMs;
  return { timeOffsetS: (videoStartFixMs - points[0].t) / 1000, skewMs };
}

/** Gaps longer than `thresholdMs` between consecutive fixes. */
export function findGaps(points, thresholdMs = 3000) {
  const gaps = [];
  for (let i = 1; i < points.length; i++) {
    const d = points[i].t - points[i - 1].t;
    if (d > thresholdMs) gaps.push({ from: iso(points[i - 1].t), seconds: Math.round(d / 1000) });
  }
  return gaps;
}

/**
 * Build a GPX 1.1 document. Per-point horizontal accuracy (metres, 68%) goes in
 * a namespaced <extensions> element — GPX's own <hdop> is a unitless dilution
 * value and would be the wrong field for it.
 */
export function buildGpx({ name, points, capture }) {
  const trkpts = points
    .map((p) => {
      const ele = p.alt == null ? '' : `<ele>${p.alt.toFixed(1)}</ele>`;
      const acc = p.acc == null ? '' : `<extensions><bk:accuracy>${p.acc.toFixed(1)}</bk:accuracy></extensions>`;
      return `      <trkpt lat="${p.lat.toFixed(7)}" lon="${p.lon.toFixed(7)}">${ele}<time>${iso(p.t)}</time>${acc}</trkpt>`;
    })
    .join('\n');

  const attrs = Object.entries(capture)
    .map(([k, v]) => `${k}="${esc(v)}"`)
    .join(' ');

  return `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Bantay Kalsada Capture"
  xmlns="http://www.topografix.com/GPX/1/1"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:bk="${NS_EXT}"
  xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <metadata>
    <name>${esc(name)}</name>
    <time>${points.length ? iso(points[0].t) : iso(Date.now())}</time>
    <extensions><bk:capture ${attrs}/></extensions>
  </metadata>
  <trk>
    <name>${esc(name)}</name>
    <trkseg>
${trkpts}
    </trkseg>
  </trk>
</gpx>
`;
}

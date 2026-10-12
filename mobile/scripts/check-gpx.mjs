// Dev check for src/gpx.js: writes a synthetic 60 s drive to stdout-named file.
// Validate with: xmllint --noout --schema gpx.xsd <file>, and parse with the
// backend's gps_service (see README "Checking the GPX output").
import { writeFileSync } from 'node:fs';
import { buildGpx, cleanPoints, computeTimeOffset, dropStalePoints, findGaps } from '../src/gpx.js';

const out = process.argv[2] || 'sample.gpx';
const t0 = Date.parse('2026-09-26T01:00:00Z');
const skew = 180; // device clock runs 180 ms ahead of fix time
const raw = [];
for (let i = 0; i < 60; i++) {
  if (i >= 30 && i < 35) continue; // 5 s GPS gap
  const t = t0 + i * 1000;
  raw.push({ t, rx: t + skew, lat: 14.1285 + i * 0.00005, lon: 120.9063 + i * 0.00002, alt: 350 + i * 0.1, acc: 4 + (i % 3) });
}
raw.push({ ...raw[10] }); // duplicate from a batched delivery
// cached last-known fix handed over first: 40 min old, delivered at session start
raw.unshift({ t: t0 - 2_400_000, rx: t0 - 500 + skew, lat: 14.2, lon: 121.0, alt: null, acc: 30 });
const { points, dropped } = dropStalePoints(cleanPoints(raw));
const videoStartDevice = t0 + 2400 + skew; // camera started 2.4 s after the first fix
const { timeOffsetS, skewMs } = computeTimeOffset(points, videoStartDevice);
writeFileSync(out, buildGpx({
  name: 'check & <sample>',
  points,
  capture: { sessionId: 'check', timeOffsetS: timeOffsetS.toFixed(3), clockSkewMs: Math.round(skewMs), points: points.length },
}));
console.log(JSON.stringify({ out, points: points.length, staleDropped: dropped, timeOffsetS, skewMs, gaps: findGaps(points) }));

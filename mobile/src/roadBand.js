// The road band: the two lines on the camera screen, horizon (top) and bonnet (bottom), as
// fractions of the picture height from the top. Each survey records the band it was filmed with
// (session.roadTop / roadBottom) and sends it with the upload (road_top / road_bottom), and the
// server looks for damage only between the lines (backend/services/video_processor.py).
//
// A phone in a car mount keeps the same view from one drive to the next, so the lines are
// remembered, separately for landscape and portrait. The horizon is null until the user drags
// it: then it follows the tilt estimate (src/level.js). The bonnet starts at the bottom edge.
import { useEffect, useState } from 'react';
import { File, Paths } from 'expo-file-system';

const STORE = new File(Paths.document, 'road_band.json');
const DEFAULT = { landscape: { top: null, bottom: 1 }, portrait: { top: null, bottom: 1 } };
export const MIN_GAP = 0.1;   // the lines never come closer than this (backend ROAD_REGION_MIN)

let saved = DEFAULT;
try {
  if (STORE.exists) saved = { ...DEFAULT, ...JSON.parse(STORE.textSync()) };
} catch {
  // keep defaults
}
const listeners = new Set();

function save(next) {
  saved = next;
  try {
    STORE.write(JSON.stringify(saved));
  } catch {
    // still applies for this session
  }
  listeners.forEach((fn) => fn(saved));
}

const key = (landscape) => (landscape ? 'landscape' : 'portrait');

/** Move one line. `which` is 'top' or 'bottom'; y is clamped to keep the lines apart. */
export function setLine(landscape, which, y, autoTop) {
  const cur = saved[key(landscape)];
  const top = cur.top ?? autoTop ?? 0.5;
  const v = which === 'top'
    ? Math.max(0.02, Math.min(y, cur.bottom - MIN_GAP))
    : Math.min(1, Math.max(y, top + MIN_GAP));
  save({ ...saved, [key(landscape)]: { ...cur, [which]: v } });
}

/** Back to the horizon from the tilt sensor and the bonnet at the bottom edge. */
export function resetLines(landscape) {
  save({ ...saved, [key(landscape)]: { top: null, bottom: 1 } });
}

/**
 * The band for the current orientation: { top, bottom, manual }. `autoTop` is the tilt
 * estimate, used while the horizon has not been dragged (0.5 without a sensor).
 */
export function useRoadBand(landscape, autoTop) {
  const [all, setAll] = useState(saved);
  useEffect(() => {
    listeners.add(setAll);
    return () => listeners.delete(setAll);
  }, []);
  const cur = all[key(landscape)];
  const manual = cur.top != null || cur.bottom < 1;
  const top = cur.top ?? autoTop ?? 0.5;
  return { top: Math.min(top, cur.bottom - MIN_GAP), bottom: cur.bottom, manual, topSet: cur.top != null };
}

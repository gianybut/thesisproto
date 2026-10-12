// Background GPS logging. The task is defined at module scope (imported from
// index.js before the app registers) so Android can deliver fixes while the
// screen is off or the app is in the background. On Android it runs inside a
// foreground service with a persistent notification.
//
// Every fix is appended as one JSON line to the active session's points.jsonl,
// so a crash mid-drive loses at most the fix being written; the GPX is built
// from that file when recording stops.
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import { File, Paths } from 'expo-file-system';
import { GPS_INTERVAL_MS } from './config';

export const LOCATION_TASK = 'bk-survey-gps';
const ACTIVE = new File(Paths.document, 'active_capture.json');

let active = null; // { id, pointsUri }
const listeners = new Set();

function readActive() {
  if (active) return active;
  try {
    active = ACTIVE.exists ? JSON.parse(ACTIVE.textSync()) : null;
  } catch {
    active = null;
  }
  return active;
}

export function onFix(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

TaskManager.defineTask(LOCATION_TASK, ({ data, error }) => {
  const a = readActive();
  const rx = Date.now();
  if (error) {
    // e.g. location permission revoked mid-session. Log it and keep the file
    // valid; the points already written are untouched.
    if (a) new File(a.pointsUri).write(JSON.stringify({ error: error.message, rx }) + '\n', { append: true });
    listeners.forEach((fn) => fn({ error: error.message, rx }));
    return;
  }
  if (!a || !data?.locations?.length) return;

  const lines = data.locations.map((loc) => {
    const p = {
      t: loc.timestamp,
      rx,
      lat: loc.coords.latitude,
      lon: loc.coords.longitude,
      alt: loc.coords.altitude,
      acc: loc.coords.accuracy,
    };
    if (loc.mocked) p.mocked = true;
    return p;
  });
  new File(a.pointsUri).write(lines.map((p) => JSON.stringify(p)).join('\n') + '\n', { append: true });
  const last = lines[lines.length - 1];
  listeners.forEach((fn) => fn(last));
});

export async function startLogging(sessionId, pointsFile) {
  if (!pointsFile.exists) pointsFile.create();
  active = { id: sessionId, pointsUri: pointsFile.uri };
  ACTIVE.write(JSON.stringify(active));

  await Location.startLocationUpdatesAsync(LOCATION_TASK, {
    accuracy: Location.Accuracy.BestForNavigation,
    timeInterval: GPS_INTERVAL_MS,
    distanceInterval: 0,
    pausesUpdatesAutomatically: false,
    activityType: Location.ActivityType.AutomotiveNavigation,
    showsBackgroundLocationIndicator: true,
    foregroundService: {
      notificationTitle: 'Recording road survey',
      notificationBody: 'GPS is being logged for the current survey video.',
      notificationColor: '#0E5661',
      killServiceOnDestroy: false,
    },
  });
}

export async function stopLogging() {
  if (await Location.hasStartedLocationUpdatesAsync(LOCATION_TASK).catch(() => false)) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK);
  }
  active = null;
  if (ACTIVE.exists) ACTIVE.delete();
}

/** Read points.jsonl back. Error lines are counted, not returned as points. */
export function readPoints(pointsFile) {
  const points = [];
  const errors = [];
  if (!pointsFile.exists) return { points, errors };
  for (const line of pointsFile.textSync().split('\n')) {
    if (!line.trim()) continue;
    try {
      const o = JSON.parse(line);
      if (o.error) errors.push(o);
      else points.push(o);
    } catch {
      // a line cut short by a crash; skip it
    }
  }
  return { points, errors };
}

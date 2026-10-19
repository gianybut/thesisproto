// After upload, follow the survey's analysis on the server so the phone can say
// "Analysing 40%" and then "Ready, 12 damages found", as the web app does. Polls
// GET /api/videos/<id> for uploaded sessions whose analysis has not finished, and
// stores the answer on the session record (serverStatus, serverProgress,
// serverDetections). Runs only while signed in and the app is open; App.js starts
// and stops it with the upload queue.
import { AppState } from 'react-native';
import { fetchVideo } from './api';
import { getSessions, updateSession } from './storage';

const POLL_MS = 5000;
const FINAL = new Set(['completed', 'failed', 'missing']);

let timer = null;
let busy = false;
let appSub = null;

const watching = () => getSessions().filter(
  (x) => x.status === 'uploaded' && x.serverVideoId != null && !FINAL.has(x.serverStatus),
);

export async function checkNow() {
  if (busy || AppState.currentState !== 'active') return;
  busy = true;
  try {
    for (const x of watching()) {
      let video;
      try {
        video = await fetchVideo(x.serverVideoId);
      } catch {
        return; // offline or signed out: try again on the next tick
      }
      if (!video) {
        updateSession(x.id, { serverStatus: 'missing' });
        continue;
      }
      const patch = {
        serverStatus: video.status,
        serverProgress: video.processing_progress ?? null,
        serverDetections: video.total_detections ?? null,
        serverError: video.error_message ?? null,
      };
      if (patch.serverStatus !== x.serverStatus || patch.serverProgress !== x.serverProgress
        || patch.serverDetections !== x.serverDetections || patch.serverError !== x.serverError) {
        updateSession(x.id, patch);
      }
    }
  } finally {
    busy = false;
  }
}

export function startStatusPolling() {
  if (timer) return;
  timer = setInterval(checkNow, POLL_MS);
  appSub = AppState.addEventListener('change', (next) => { if (next === 'active') checkNow(); });
  checkNow();
}

export function stopStatusPolling() {
  clearInterval(timer);
  timer = null;
  appSub?.remove();
  appSub = null;
}

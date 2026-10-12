// One-at-a-time upload queue with backoff. State lives in the session records
// (storage.js), so the queue survives restarts: on launch anything left
// `uploading` goes back to `queued` and is picked up again.
import * as Network from 'expo-network';
import { File, Paths } from 'expo-file-system';
import { uploadSession } from './api';
import { getToken } from './auth';
import { MAX_AUTO_ATTEMPTS, RETRY_BASE_MS } from './config';
import { getSession, getSessions, updateSession } from './storage';

const SETTINGS = new File(Paths.document, 'settings.json');

let settings = { wifiOnly: true };
try {
  if (SETTINGS.exists) settings = { ...settings, ...JSON.parse(SETTINGS.textSync()) };
} catch {
  // keep defaults
}

let current = null; // { id, cancel }
let timer = null;
let netSub = null;
let paused = false;
const settingsListeners = new Set();

export const getSettings = () => settings;

export function setWifiOnly(wifiOnly) {
  settings = { ...settings, wifiOnly };
  SETTINGS.write(JSON.stringify(settings));
  settingsListeners.forEach((fn) => fn(settings));
  run();
}

export function onSettings(fn) {
  settingsListeners.add(fn);
  return () => settingsListeners.delete(fn);
}

async function networkAllows() {
  const n = await Network.getNetworkStateAsync().catch(() => null);
  if (!n || !n.isConnected || n.isInternetReachable === false) return false;
  if (settings.wifiOnly) {
    return n.type === Network.NetworkStateType.WIFI || n.type === Network.NetworkStateType.ETHERNET;
  }
  return true;
}

/** Why the queue is idle, for the session list header. */
export async function describeWait() {
  if (!getToken()) return 'Log in to upload.';
  const n = await Network.getNetworkStateAsync().catch(() => null);
  if (!n || !n.isConnected) return 'No connection. Uploads will start when one is available.';
  if (settings.wifiOnly && n.type !== Network.NetworkStateType.WIFI && n.type !== Network.NetworkStateType.ETHERNET) {
    return 'Waiting for Wi-Fi. Turn off "Wi-Fi only" to upload over mobile data.';
  }
  return null;
}

/**
 * Paused while a recording is running: an upload would compete with the
 * camera for CPU and heat, and a 401 from it would unmount the camera screen.
 */
export function setPaused(p) {
  paused = p;
  if (p && current) {
    current.requeue = true;
    current.cancel();
  }
  if (!p) run();
}

export async function run() {
  if (current || paused || !getToken()) return;
  const now = Date.now();
  const next = getSessions()
    .filter((x) => x.status === 'queued' && (x.nextAttemptAt || 0) <= now)
    .sort((a, b) => a.createdAt - b.createdAt)[0];
  if (!next) return;
  if (!(await networkAllows())) return;
  if (current || paused) return; // state changed while we awaited

  const id = next.id;
  if (!next.videoUri) {
    // Saving the recording failed, so there is no file to send.
    updateSession(id, { status: 'failed', broken: true, progress: 0, lastError: next.lastError || 'This session has no video file.' });
    run();
    return;
  }
  updateSession(id, { status: 'uploading', progress: 0, lastError: null });

  let lastPct = -1;
  current = { id, cancel: () => {}, requeue: false };

  try {
    const task = uploadSession(next, (frac) => {
      const pct = Math.floor(frac * 100);
      if (pct !== lastPct) {
        lastPct = pct;
        updateSession(id, { progress: frac });
      }
    });
    current.cancel = task.cancel;
    const video = await task.promise;
    updateSession(id, {
      status: 'uploaded', progress: 1, uploadedAt: Date.now(), serverVideoId: video?.id ?? null, lastError: null,
    });
  } catch (e) {
    const s = getSession(id);
    const attempts = (s?.attempts || 0) + 1;
    if (e.status === 401) {
      // Stays queued; resumes after the user logs in again.
      updateSession(id, { status: 'queued', progress: 0, lastError: e.message });
    } else if (e.cancelled && current?.requeue) {
      updateSession(id, { status: 'queued', progress: 0 });
    } else if (e.cancelled) {
      updateSession(id, { status: 'recorded', progress: 0, lastError: null });
    } else if (!e.retryable || attempts >= MAX_AUTO_ATTEMPTS) {
      updateSession(id, { status: 'failed', progress: 0, attempts, lastError: e.message });
    } else {
      updateSession(id, {
        status: 'queued', progress: 0, attempts, lastError: e.message,
        nextAttemptAt: Date.now() + RETRY_BASE_MS * 2 ** (attempts - 1),
      });
    }
  } finally {
    current = null;
  }
  run();
}

export function enqueue(id) {
  updateSession(id, { status: 'queued', attempts: 0, nextAttemptAt: 0, lastError: null });
  run();
}

export function cancelUpload(id) {
  if (current?.id === id) current.cancel();
}

export const isUploading = (id) => current?.id === id;

export function startQueue() {
  if (timer) return;
  timer = setInterval(run, 15_000);
  netSub = Network.addNetworkStateListener(() => run());
  run();
}

export function stopQueue() {
  clearInterval(timer);
  timer = null;
  netSub?.remove();
  netSub = null;
}

// Session list persisted as one JSON file in the app's document directory, so
// recordings and the upload queue survive app restarts. Each session's files
// live in documents/sessions/<id>/.
//
// Session status: recording -> recorded -> queued -> uploading -> uploaded
//                                                  \-> failed (manual retry)
import { Directory, File, Paths } from 'expo-file-system';

const INDEX = new File(Paths.document, 'sessions.json');
const ROOT = new Directory(Paths.document, 'sessions');

let sessions = null;
const listeners = new Set();

function load() {
  if (sessions) return sessions;
  try {
    sessions = INDEX.exists ? JSON.parse(INDEX.textSync()) : [];
  } catch {
    sessions = [];
  }
  return sessions;
}

function persist() {
  INDEX.write(JSON.stringify(sessions));
  const snapshot = [...sessions];
  listeners.forEach((fn) => fn(snapshot));
}

export function getSessions() {
  return [...load()];
}

export function getSession(id) {
  return load().find((x) => x.id === id) || null;
}

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function sessionDir(id) {
  const dir = new Directory(ROOT, id);
  if (!dir.exists) dir.create({ intermediates: true });
  return dir;
}

export function addSession(session) {
  load().unshift(session);
  persist();
}

export function updateSession(id, patch) {
  load();
  sessions = sessions.map((x) => (x.id === id ? { ...x, ...patch } : x));
  persist();
}

export function deleteSession(id) {
  load();
  const dir = new Directory(ROOT, id);
  if (dir.exists) dir.delete();
  sessions = sessions.filter((x) => x.id !== id);
  persist();
}

/**
 * Called once at startup. A session left `recording` means the app was killed
 * mid-capture; one left `uploading` means an upload was interrupted.
 */
export function recoverAfterRestart() {
  load();
  let changed = false;
  sessions = sessions.map((x) => {
    if (x.status === 'uploading') {
      changed = true;
      return { ...x, status: 'queued', progress: 0 };
    }
    if (x.status === 'recording') {
      changed = true;
      // The camera's output never reached the session folder, so there is
      // nothing to retry. Kept in the list so the loss is visible; delete only.
      return { ...x, status: 'failed', broken: true, lastError: 'The app closed during recording. The video was not saved.' };
    }
    return x;
  });
  if (changed) persist();
}

export const newSessionId = () =>
  new Date().toISOString().replace(/[-:]/g, '').replace(/\..+/, '') + '-' + Math.random().toString(36).slice(2, 6);

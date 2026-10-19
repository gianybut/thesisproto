// Plain-language names for what the app stores, in the web app's words
// (frontend/src/labels.js, frontend/src/roles.js). Screens show these, never raw status values.
import { MAX_RECORD_S } from './config';

// The two system roles (backend models.ROLES). Both may record and upload on the phone;
// the admin-only tasks are on the web app.
export const ROLE_LABELS = {
  personnel: 'Road maintenance personnel',
  admin: 'System administrator',
};
export const roleLabel = (user) => user?.role_label || ROLE_LABELS[user?.role] || ROLE_LABELS.personnel;

/**
 * One status per survey, icon plus words (design.md §4). Before upload it describes the phone's
 * copy; after upload it follows the server's Video.status with the web app's labels.
 * tone: waiting | running | ready | failed, which StatusLabel turns into colours.
 */
export function surveyStatus(x) {
  if (x.broken) return { icon: 'alert-circle', tone: 'failed', text: 'Not saved' };
  switch (x.status) {
    case 'recording': return { icon: 'half-circle', tone: 'running', text: 'Recording' };
    case 'recorded': return { icon: 'clock', tone: 'waiting', text: 'Not uploaded' };
    case 'queued': return { icon: 'clock', tone: 'waiting', text: 'Waiting to upload' };
    case 'uploading': {
      const pct = Math.round((x.progress || 0) * 100);
      return { icon: 'half-circle', tone: 'running', text: `Uploading ${pct}%`, progress: pct };
    }
    case 'failed': return { icon: 'alert-circle', tone: 'failed', text: 'Upload failed' };
    case 'uploaded':
      switch (x.serverStatus) {
        case 'uploaded': return { icon: 'clock', tone: 'waiting', text: 'Waiting to start' };
        case 'processing': {
          const pct = Math.round(x.serverProgress || 0);
          return { icon: 'half-circle', tone: 'running', text: `Analysing ${pct}%`, progress: pct };
        }
        case 'completed': return { icon: 'check', tone: 'ready', text: 'Ready' };
        case 'failed': return { icon: 'alert-circle', tone: 'failed', text: 'Analysis failed' };
        case 'missing': return { icon: 'info-circle', tone: 'waiting', text: 'Removed from the web app' };
        default: return { icon: 'check', tone: 'ready', text: 'Uploaded' };
      }
    default: return { icon: 'clock', tone: 'waiting', text: x.status };
  }
}

/** The one thing to do next with a survey, or null. Shared by the list and the survey screen. */
export function nextStep(x) {
  if (x.broken || !x.videoUri) return null;
  if (x.status === 'recorded') return { kind: 'upload', label: 'Upload', icon: 'upload' };
  if (x.status === 'failed') return { kind: 'upload', label: 'Try the upload again', icon: 'refresh' };
  if (x.status === 'queued' && (x.nextAttemptAt || 0) > Date.now()) return { kind: 'upload', label: 'Upload now', icon: 'upload' };
  if (x.status === 'uploading') return { kind: 'cancel', label: 'Cancel upload', icon: 'x' };
  // The server keeps the files, so a failed analysis is rerun there; re-uploading is only the
  // fallback when the server no longer has them (surveyActions.runNextStep).
  if (x.status === 'uploaded' && x.serverStatus === 'failed') return { kind: 'reanalyse', label: 'Analyse again', icon: 'refresh' };
  return null;
}

/** One line under the status: the result, or what went wrong. Returns { text, danger } or null. */
export function surveyNote(x) {
  if (x.status === 'uploaded') {
    if (x.serverStatus === 'completed' && x.serverDetections != null) return { text: damageCount(x.serverDetections) };
    if (x.serverStatus === 'failed') {
      return { text: x.serverError || 'The server could not finish analysing this survey.', danger: true };
    }
    if (x.serverStatus === 'missing') return { text: 'This survey was deleted on the web app. The copy on this phone is still here.' };
    return null;
  }
  if (x.lastError && (x.status === 'failed' || x.status === 'queued')) {
    const retry = x.status === 'queued' && x.attempts ? ' Trying again by itself.' : '';
    return { text: `${x.lastError}${retry}`, danger: true };
  }
  return null;
}

export const damageCount = (n) => `${n} ${n === 1 ? 'damage' : 'damages'} found`;

export const surveyTitle = (x) => x.roadName || `Survey ${formatDateTime(x.createdAt)}`;

export const formatDuration = (sec) => {
  if (sec == null) return '—';
  return `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, '0')}`;
};

// Camera clock: always two-digit minutes so the width does not jump.
export const formatClock = (sec) =>
  `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(Math.floor(sec % 60)).padStart(2, '0')}`;

export const formatSize = (bytes) => {
  if (bytes == null) return '—';
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
  if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
};

export const formatDateTime = (ms) => (ms
  ? new Date(ms).toLocaleString('en-PH', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })
  : '—');

export const formatTime = (ms) => (ms
  ? new Date(ms).toLocaleTimeString('en-PH', { hour: 'numeric', minute: '2-digit' })
  : '—');

const limit = `${Math.floor(MAX_RECORD_S / 60)} min ${MAX_RECORD_S % 60} s`;
export const END_REASONS = {
  stopped: 'Stopped by you',
  duration_cap: `Reached the ${limit} limit`,
  size_cap: 'Reached the size limit',
  camera_stopped: 'The camera stopped',
  app_left_foreground: 'The app left the screen',
  camera_error: 'Camera error',
};

// Plain-language names for the codes the backend stores. Pages show these names and set the
// code beside them, never the code alone.

// RDD2022 codes; there is no D30. Map colours live with the map in DamageMapPage.jsx.
export const DAMAGE_NAMES = {
  D00: 'Longitudinal crack',
  D10: 'Transverse crack',
  D20: 'Alligator crack',
  D40: 'Pothole',
};
export const DAMAGE_CODES = Object.keys(DAMAGE_NAMES);
export const damageName = (code) => DAMAGE_NAMES[code] || 'Unclassified damage';

// Detection.inspection_status, in workflow order.
export const STATUSES = ['pending_validation', 'inspected', 'scheduled', 'ongoing_repair', 'resolved'];
export const STATUS_LABELS = {
  pending_validation: 'Not yet checked',
  inspected: 'Checked on site',
  scheduled: 'Repair scheduled',
  ongoing_repair: 'Repair under way',
  resolved: 'Repaired',
};
export const statusLabel = (s) => STATUS_LABELS[s] || 'Not yet checked';

// Video.status
export const VIDEO_STATUS_LABELS = {
  uploaded: 'Waiting to start',
  processing: 'Analysing',
  completed: 'Ready',
  failed: 'Analysis failed',
};
export const videoStatusLabel = (s) => VIDEO_STATUS_LABELS[s] || s;

// Video.position_source
export const locationLabel = (v) => {
  if (v.has_gps || v.position_source === 'gps_file') return 'GPS track';
  if (v.position_source === 'georeferenced') return 'Placed by hand';
  return 'No location yet';
};

// One answer, used everywhere, to "what can the user do next with this survey?"
export const isRunning = (v) => v?.status === 'uploaded' || v?.status === 'processing';
export const hasLocation = (v) => Boolean(v?.has_gps || v?.position_source === 'georeferenced');
export const canPlaceByHand = (v) => Boolean(v && !v.has_gps && v.status !== 'failed');
export const surveyName = (v) => v?.name || v?.original_filename || 'Untitled survey';

export const MAX_VIDEO_MINUTES = 10;   // backend app.py MAX_VIDEO_DURATION_S = 600
export const VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'mkv', 'webm'];   // backend ALLOWED_VIDEO_EXTENSIONS
export const GPS_EXTENSIONS = ['gpx', 'csv'];

export const formatDuration = (s) => {
  if (!s) return '—';
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
};

export const formatSize = (bytes) => {
  if (!bytes) return '—';
  if (bytes >= 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
};

export const formatDate = (iso) => (iso
  ? new Date(iso).toLocaleDateString('en-PH', { year: 'numeric', month: 'short', day: 'numeric' })
  : '—');

// Turn an axios error into a sentence that says what failed and what to do.
export const errorMessage = (err, fallback) => {
  if (err?.response?.data?.error) return err.response.data.error;
  if (err?.request && !err?.response) {
    return 'Could not reach the server. Check that the backend is running, then try again.';
  }
  return fallback;
};

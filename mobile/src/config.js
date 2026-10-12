// Capture limits. Each one mirrors a backend limit with a margin, so a finished
// recording is never rejected at upload.

// backend app.py: MAX_VIDEO_DURATION_S = 600, rejected when duration > 600.
// The container can report a few hundred ms more than the wall-clock recording.
export const MAX_RECORD_S = 590;

// Size cap OFF for now (null): the backend's MAX_CONTENT_LENGTH is off too, and
// iPhone recordings outgrew 500 MB. Length is still capped by MAX_RECORD_S.
// To restore: 480 * 1024 * 1024 here, 500 MB in backend app.py (video + GPX +
// form fields must fit under it).
export const MAX_VIDEO_BYTES = null;

// 1080p at 5 Mbit/s, no audio: ~37 MB/min, ~365 MB for a full 590 s session.
// Measure on each test device and record the real figure for Chapter 3.
export const VIDEO_QUALITY = '1080p';
export const VIDEO_BITRATE = 5_000_000;

// Refuse to start unless this much is free. With no size cap there is no
// "full-size video" to reserve for; 2 GB covers a 10-minute recording at well
// above the requested bitrate. If the phone fills up anyway, the camera stops
// and the part already recorded is kept.
export const MIN_FREE_BYTES = MAX_VIDEO_BYTES ? MAX_VIDEO_BYTES + 64 * 1024 * 1024 : 2 * 1024 * 1024 * 1024;

// GPS
export const GPS_INTERVAL_MS = 1000;       // 1 Hz
export const MIN_FIX_ACCURACY_M = 20;      // recording cannot start until a fix is at least this good
export const GPS_STALE_MS = 5000;          // no point for this long during recording = "GPS lost"

// Upload queue
export const MAX_AUTO_ATTEMPTS = 5;        // after this many failures a session waits for a manual retry
export const RETRY_BASE_MS = 15_000;       // backoff: 15 s, 30 s, 60 s, ...

export const DEFAULT_SERVER_URL = 'http://192.168.1.10:5000';

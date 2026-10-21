// Upload to the existing endpoint: POST /api/videos/upload with multipart fields
// video, gps_file, time_offset, road_name, road_top, road_bottom
// (backend/routes/videos.py). One clip of a long recording is one upload.
//
// Android: XMLHttpRequest + FormData, which streams the file from disk and
// reports progress. This is the original path, unchanged.
//
// iOS: React Native's iOS networking copies every multipart part into one
// in-memory buffer before sending (RCTNetworking.mm), so a ~365 MB survey
// would need that much RAM and risks the app being killed mid-upload.
// Instead the whole multipart body is written to a file and sent with
// expo-file-system's native upload task, which streams from disk. Costs a
// temporary copy of the video on disk during the upload.
import { File, FileMode, Paths, UploadType } from 'expo-file-system';
import { authHeader, getServerUrl, handleUnauthorized } from './auth';
import { multipartHead, multipartTail, newBoundary } from './multipart';
import { freeBytes, IS_IOS } from './platform';

export class UploadError extends Error {
  constructor(message, { status = 0, retryable = true, cancelled = false } = {}) {
    super(message);
    this.status = status;
    this.retryable = retryable;
    this.cancelled = cancelled;
  }
}

const cancelledError = () => new UploadError('Upload cancelled.', { retryable: false, cancelled: true });

/** Same interpretation of the server's answer on both platforms. */
function interpretResponse(status, text) {
  let body = {};
  try {
    body = JSON.parse(text);
  } catch {
    // non-JSON error page
  }
  if (status >= 200 && status < 300) return body.video;
  if (status === 401) {
    handleUnauthorized();
    throw new UploadError('Signed out. Sign in again to upload.', { status: 401 });
  }
  // 400 (too long, wrong type) and 413 (too large) will fail the same way
  // every time; server errors and anything else are worth retrying.
  const retryable = !(status === 400 || status === 413);
  throw new UploadError(body.error || `Upload failed (HTTP ${status})`, { status, retryable });
}

const videoPart = (session) => ({
  name: `${session.id}.${session.videoExt || 'mp4'}`,
  mime: session.videoMime || 'video/mp4',
});

/**
 * Returns { promise, cancel }. The promise resolves to the created Video record.
 */
export function uploadSession(session, onProgress) {
  return IS_IOS ? uploadStreamedFromFile(session, onProgress) : uploadWithXhr(session, onProgress);
}

function uploadWithXhr(session, onProgress) {
  const xhr = new XMLHttpRequest();

  const promise = new Promise((resolve, reject) => {
    const form = new FormData();
    const v = videoPart(session);
    form.append('video', { uri: session.videoUri, name: v.name, type: v.mime });
    if (session.gpxUri) {
      form.append('gps_file', { uri: session.gpxUri, name: `${session.id}.gpx`, type: 'application/gpx+xml' });
      form.append('time_offset', String(session.timeOffsetS));
    }
    if (session.roadName) form.append('road_name', session.roadName);
    if (session.roadTop != null) {
      form.append('road_top', String(session.roadTop));
      form.append('road_bottom', String(session.roadBottom ?? 1));
    }

    xhr.open('POST', `${getServerUrl()}/api/videos/upload`);
    Object.entries(authHeader()).forEach(([k, v]) => xhr.setRequestHeader(k, v));
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total);
    };
    xhr.onload = () => {
      try {
        resolve(interpretResponse(xhr.status, xhr.responseText));
      } catch (e) {
        reject(e);
      }
    };
    xhr.onerror = () => reject(new UploadError('Network error during upload.'));
    xhr.ontimeout = () => reject(new UploadError('Upload timed out.'));
    xhr.onabort = () => reject(cancelledError());
    xhr.send(form);
  });

  return { promise, cancel: () => xhr.abort() };
}

/**
 * The server's record for an uploaded survey (GET /api/videos/<id>), to follow its analysis.
 * Resolves null when the server no longer has it (deleted on the web app).
 * Throws on a network error; a 401 signs out like any other call.
 */
export async function fetchVideo(videoId) {
  const res = await fetch(`${getServerUrl()}/api/videos/${videoId}`, { headers: authHeader() });
  if (res.status === 401) {
    handleUnauthorized();
    throw new UploadError('Signed out.', { status: 401 });
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new UploadError(`Could not check the survey (HTTP ${res.status})`, { status: res.status });
  const body = await res.json();
  return body.video;
}

/**
 * Ask the server to analyse a failed survey again from the files it already has
 * (POST /api/videos/<id>/reprocess). Resolves to the survey, or null when the server no longer
 * has it (404) or its video (410), in which case the phone has to upload it again.
 * Other refusals throw with the server's own sentence.
 */
export async function reprocessVideo(videoId) {
  const res = await fetch(`${getServerUrl()}/api/videos/${videoId}/reprocess`, { method: 'POST', headers: authHeader() });
  if (res.status === 401) {
    handleUnauthorized();
    throw new UploadError('Signed out. Sign in again first.', { status: 401 });
  }
  if (res.status === 404 || res.status === 410) return null;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new UploadError(body.error || `Could not start the analysis again (HTTP ${res.status})`, { status: res.status });
  return body.video;
}

const COPY_CHUNK = 4 * 1024 * 1024;
const yieldToUi = () => new Promise((r) => setTimeout(r, 0));

async function writeMultipartBody(session, body, boundary, isCancelled) {
  const head = multipartHead({
    boundary,
    fields: {
      time_offset: session.gpxUri ? String(session.timeOffsetS) : null,
      road_name: session.roadName || null,
      road_top: session.roadTop != null ? String(session.roadTop) : null,
      road_bottom: session.roadTop != null ? String(session.roadBottom ?? 1) : null,
    },
    gpx: session.gpxUri ? { name: `${session.id}.gpx`, text: new File(session.gpxUri).textSync() } : null,
    video: videoPart(session),
  });
  const enc = new TextEncoder();

  body.create({ overwrite: true });
  const out = body.open(FileMode.Truncate);
  const src = new File(session.videoUri).open(FileMode.ReadOnly);
  try {
    out.writeBytes(enc.encode(head));
    for (;;) {
      if (isCancelled()) throw cancelledError();
      const chunk = src.readBytes(COPY_CHUNK);
      if (!chunk.length) break;
      out.writeBytes(chunk);
      await yieldToUi();
    }
    out.writeBytes(enc.encode(multipartTail(boundary)));
  } finally {
    src.close();
    out.close();
  }
}

function uploadStreamedFromFile(session, onProgress) {
  let cancelled = false;
  let task = null;
  const body = new File(Paths.cache, `upload-${session.id}.bin`);

  const promise = (async () => {
    try {
      const need = new File(session.videoUri).size + 4 * 1024 * 1024;
      const free = await freeBytes();
      if (free < need) {
        throw new UploadError(
          `The upload needs ${Math.ceil(need / 1048576)} MB free to prepare the file (${Math.floor(free / 1048576)} MB free). Free some space, then retry.`,
          { retryable: false },
        );
      }
      const boundary = newBoundary();
      await writeMultipartBody(session, body, boundary, () => cancelled);
      if (cancelled) throw cancelledError();

      task = body.createUploadTask(`${getServerUrl()}/api/videos/upload`, {
        httpMethod: 'POST',
        uploadType: UploadType.BINARY_CONTENT,
        headers: { ...authHeader(), 'Content-Type': `multipart/form-data; boundary=${boundary}` },
        // A background session keeps going after the app is suspended, but if the
        // app is then terminated the finished upload is never reported back and
        // the queue would send it again: a duplicate survey on the server.
        // Foreground matches Android: the upload needs the app open.
        sessionType: 'foreground',
      });
      const sub = task.addListener('progress', ({ bytesSent, totalBytes }) => {
        if (totalBytes > 0 && onProgress) onProgress(bytesSent / totalBytes);
      });
      let res;
      try {
        res = await task.uploadAsync();
      } catch (e) {
        if (cancelled) throw cancelledError();
        throw new UploadError(`Network error during upload. (${e.message})`);
      } finally {
        sub.remove();
      }
      return interpretResponse(res.status, res.body);
    } finally {
      if (body.exists) body.delete();
    }
  })();

  return {
    promise,
    cancel: () => {
      cancelled = true;
      task?.cancel();
    },
  };
}

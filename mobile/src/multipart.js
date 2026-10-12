// multipart/form-data body for the iOS upload path, built as text around the
// video so the video bytes can be streamed in between from disk. Pure, so it
// can be checked against the real backend under Node.
//
// Same fields as the Android XMLHttpRequest path and the web app:
// time_offset, road_name, gps_file (GPX), video.

const CRLF = '\r\n';
const quote = (s) => String(s).replace(/"/g, '%22').replace(/\r|\n/g, ' ');

export function newBoundary() {
  return `----bk${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`;
}

/** Everything that goes before the video bytes. */
export function multipartHead({ boundary, fields, gpx, video }) {
  let out = '';
  for (const [name, value] of Object.entries(fields)) {
    if (value == null || value === '') continue;
    out += `--${boundary}${CRLF}Content-Disposition: form-data; name="${quote(name)}"${CRLF}${CRLF}${value}${CRLF}`;
  }
  if (gpx) {
    out += `--${boundary}${CRLF}Content-Disposition: form-data; name="gps_file"; filename="${quote(gpx.name)}"${CRLF}`;
    out += `Content-Type: application/gpx+xml${CRLF}${CRLF}${gpx.text}${CRLF}`;
  }
  out += `--${boundary}${CRLF}Content-Disposition: form-data; name="video"; filename="${quote(video.name)}"${CRLF}`;
  out += `Content-Type: ${video.mime}${CRLF}${CRLF}`;
  return out;
}

/** Everything that goes after the video bytes. */
export function multipartTail(boundary) {
  return `${CRLF}--${boundary}--${CRLF}`;
}

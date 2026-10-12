// Dev check for src/mp4.js and src/multipart.js. Usage:
//   node scripts/check-upload-body.mjs <video> <gpx> <out-body>
// Prints the atoms, whether the movie is finalized, and writes the exact
// multipart body the iOS path would stream, plus its boundary.
import { closeSync, openSync, readFileSync, readSync, statSync, writeFileSync, appendFileSync } from 'node:fs';
import { topLevelAtoms, isFinalizedMovie } from '../src/mp4.js';
import { multipartHead, multipartTail, newBoundary } from '../src/multipart.js';

const [video, gpx, out] = process.argv.slice(2);
const size = statSync(video).size;
const fd = openSync(video, 'r');
const read = (off, len) => { const b = Buffer.alloc(len); const n = readSync(fd, b, 0, len, off); return b.subarray(0, n); };
const atoms = topLevelAtoms(read, size).map((a) => `${a.type}:${a.size}`);
const finalized = isFinalizedMovie(read, size);
closeSync(fd);
const report = { video, size, atoms, finalized };
if (out) {
  const boundary = newBoundary();
  const ext = video.split('.').pop();
  const head = multipartHead({
    boundary,
    fields: { time_offset: '2.400', road_name: 'Mendez–Tagaytay Rd (Nuñez)' },
    gpx: { name: 'check.gpx', text: readFileSync(gpx, 'utf8') },
    video: { name: `check.${ext}`, mime: ext === 'mov' ? 'video/quicktime' : 'video/mp4' },
  });
  writeFileSync(out, head);
  appendFileSync(out, readFileSync(video));
  appendFileSync(out, multipartTail(boundary));
  report.boundary = boundary;
}
console.log(JSON.stringify(report));

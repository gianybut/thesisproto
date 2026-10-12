// Minimal ISO-BMFF (MP4 / QuickTime .mov) check: walk the top-level atoms and
// report whether a `moov` atom is present. A recording cut off before the
// camera finalised the file has `mdat` but no `moov`; OpenCV on the server
// reads such a file as 0 frames, so it would upload fine and then fail.
//
// `read(offset, length)` returns a Uint8Array; kept abstract so this runs
// under Node (scripts/check-upload-body.mjs) as well as on the phone.

const type4 = (b, i) => String.fromCharCode(b[i], b[i + 1], b[i + 2], b[i + 3]);
const u32 = (b, i) => ((b[i] << 24) >>> 0) + (b[i + 1] << 16) + (b[i + 2] << 8) + b[i + 3];

export function topLevelAtoms(read, fileSize) {
  const atoms = [];
  let offset = 0;
  while (offset + 8 <= fileSize && atoms.length < 64) {
    const h = read(offset, 16);
    if (h.length < 8) break;
    let size = u32(h, 0);
    const type = type4(h, 4);
    if (size === 1) {
      if (h.length < 16) break;
      size = u32(h, 8) * 2 ** 32 + u32(h, 12); // 64-bit largesize
    } else if (size === 0) {
      size = fileSize - offset; // atom runs to end of file
    }
    if (size < 8 || !/^[\x20-\x7e]{4}$/.test(type)) break; // not a valid atom header: file is damaged
    atoms.push({ type, offset, size });
    offset += size;
  }
  return atoms;
}

export function isFinalizedMovie(read, fileSize) {
  return topLevelAtoms(read, fileSize).some((a) => a.type === 'moov');
}

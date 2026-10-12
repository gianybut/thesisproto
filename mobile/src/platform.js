// The few places where iOS and Android need different calls. Anything here is
// also listed under "Platform differences" in mobile/README.md.
import { Platform } from 'react-native';
import { Directory, File, FileMode, Paths } from 'expo-file-system';
import { getFreeDiskStorageAsync } from 'expo-file-system/legacy';
import { isFinalizedMovie } from './mp4';

export const IS_IOS = Platform.OS === 'ios';

/**
 * Free bytes on the data volume.
 * iOS: Paths.availableDiskSpace reads .systemFreeSize, which leaves out purgeable
 * space the system will free on demand, so it can be gigabytes below what
 * Settings shows. The legacy call reads volumeAvailableCapacityForImportantUsage,
 * Apple's figure for "can I write a user-requested file of this size".
 * Android: unchanged from the original build.
 */
export async function freeBytes() {
  if (IS_IOS) return getFreeDiskStorageAsync();
  return Paths.availableDiskSpace;
}

/** Recording options per platform (expo-camera recordAsync). */
export function recordingPlatformOptions() {
  // iOS: without a codec, AVCaptureMovieFileOutput picks HEVC on current iPhones
  // and ignores videoBitrate. Force H.264 so the bitrate applies and the file
  // decodes anywhere. Android's MediaRecorder already writes H.264.
  return IS_IOS ? { codec: 'avc1' } : {};
}

/** What the camera wrote: iOS writes QuickTime .mov, Android .mp4. */
export function videoTypeFor(uri) {
  const ext = (uri.split('?')[0].split('.').pop() || '').toLowerCase();
  if (ext === 'mov') return { ext: 'mov', mime: 'video/quicktime' };
  return { ext: 'mp4', mime: 'video/mp4' };
}

export function fileReader(file) {
  const handle = file.open(FileMode.ReadOnly);
  return {
    read(offset, length) {
      handle.offset = offset;
      return handle.readBytes(length);
    },
    close: () => handle.close(),
  };
}

/** True if the movie has its `moov` index, i.e. the camera finished writing it. */
export function movieIsFinalized(file) {
  const r = fileReader(file);
  try {
    return isFinalizedMovie(r.read, file.size);
  } finally {
    r.close();
  }
}

/**
 * iOS only. If the camera session is stopped mid-recording (screen lock, app
 * switch, phone call), AVFoundation usually finishes the file and expo-camera
 * resolves normally. When it reports the stop as a failure instead,
 * expo-camera rejects without telling us the file path, although the file is
 * often complete. Find the newest .mov the camera wrote since `sinceMs`.
 */
export function findOrphanedRecording(sinceMs) {
  if (!IS_IOS) return null;
  const dir = new Directory(Paths.cache, 'Camera');
  if (!dir.exists) return null;
  let best = null;
  for (const entry of dir.list()) {
    if (!(entry instanceof File) || !entry.name.toLowerCase().endsWith('.mov')) continue;
    const mtime = entry.modificationTime ?? 0;
    if (mtime >= sinceMs - 2000 && (!best || mtime > best.modificationTime)) best = entry;
  }
  return best;
}

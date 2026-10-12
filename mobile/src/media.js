// What the phone can do with a stored session's files besides uploading them:
// a thumbnail for the list, and copies out to Photos or the share sheet
// (Save to Files, AirDrop, Drive, ...). Files stay in the session folder after
// upload, so all of this works for uploaded sessions too.
import { File } from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library/legacy';
import * as Sharing from 'expo-sharing';
import { getThumbnailAsync } from 'expo-video-thumbnails';
import { sessionDir, updateSession } from './storage';

// Thumbnails are made one at a time: decoding a frame from several 1080p
// videos at once stalls the list on older phones.
let chain = Promise.resolve();
const inFlight = new Set();

/** Make thumb.jpg for a session that has a video and none yet. Fire and forget. */
export function ensureThumbnail(session) {
  if (!session.videoUri || session.thumbUri || session.thumbFailed || inFlight.has(session.id)) return;
  inFlight.add(session.id);
  chain = chain.then(async () => {
    try {
      // 1 s in skips the dark first frames while the camera adjusts exposure.
      const time = (session.durationS ?? 0) > 2 ? 1000 : 0;
      const { uri } = await getThumbnailAsync(session.videoUri, { time, quality: 0.6 });
      const thumb = new File(sessionDir(session.id), 'thumb.jpg');
      if (thumb.exists) thumb.delete();
      await new File(uri).move(thumb);
      updateSession(session.id, { thumbUri: thumb.uri });
    } catch (e) {
      console.warn(`[media] thumbnail for ${session.id} failed: ${e.message}`);
      updateSession(session.id, { thumbFailed: true });
    } finally {
      inFlight.delete(session.id);
    }
  });
}

/** Save the video to Photos. Asks for add-only access; never reads the library. */
export async function saveVideoToPhotos(session) {
  const perm = await MediaLibrary.requestPermissionsAsync(true, ['video']);
  if (!perm.granted) {
    throw new Error('Photos access was not allowed. Turn it on in Settings to save videos.');
  }
  await MediaLibrary.saveToLibraryAsync(session.videoUri);
}

/** Open the share sheet for the session's video or GPX ("Save to Files", AirDrop, ...). */
export async function shareSessionFile(session, kind) {
  if (!(await Sharing.isAvailableAsync())) throw new Error('Sharing is not available on this device.');
  if (kind === 'gpx') {
    await Sharing.shareAsync(session.gpxUri, {
      mimeType: 'application/gpx+xml', UTI: 'public.xml', dialogTitle: 'GPS track',
    });
  } else {
    const mov = session.videoExt === 'mov';
    await Sharing.shareAsync(session.videoUri, {
      mimeType: session.videoMime || 'video/mp4',
      UTI: mov ? 'com.apple.quicktime-movie' : 'public.mpeg-4',
      dialogTitle: 'Survey video',
    });
  }
}

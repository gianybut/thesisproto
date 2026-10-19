// Turning a finished recording into an upload-ready session: move the video out
// of the camera's cache, build the GPX from the logged fixes, and compute
// time_offset.
import { Platform } from 'react-native';
import { File } from 'expo-file-system';
import { buildGpx, cleanPoints, computeTimeOffset, dropStalePoints, findGaps } from './gpx';
import { movieIsFinalized, videoTypeFor } from './platform';
import { readPoints, stopLogging } from './locationTask';
import { sessionDir, updateSession } from './storage';

export function pointsFileFor(id) {
  return new File(sessionDir(id), 'points.jsonl');
}

/**
 * @param session       the session record created at record start
 * @param videoUri      what recordAsync resolved with (may be null if the camera failed)
 * @param videoStartMs  device clock immediately before recordAsync() was called
 * @param stopMs        device clock when recording ended
 * @param endReason     'stopped' | 'duration_cap' | 'size_cap' | 'camera_stopped' | 'app_left_foreground' | 'camera_error'
 * @param recovered     iOS: the camera reported a failure and the file was found in its cache instead
 */
export async function finalizeSession(session, { videoUri, videoStartMs, stopMs, endReason, cameraError, recovered }) {
  await stopLogging();
  const dir = sessionDir(session.id);

  if (!videoUri) {
    updateSession(session.id, {
      status: 'failed', broken: true, endReason,
      lastError: cameraError ? `The camera did not save a video: ${cameraError}` : 'The camera did not save a video.',
    });
    return;
  }

  // Keep the container the camera wrote (iOS .mov, Android .mp4); the backend
  // accepts both, and renaming a QuickTime file to .mp4 would mislabel it.
  const { ext, mime } = videoTypeFor(videoUri);
  const source = new File(videoUri);
  if (!source.exists) {
    updateSession(session.id, {
      status: 'failed', broken: true, endReason,
      lastError: `The camera reported a video (${source.name}) but the file is not on the phone.`,
    });
    return;
  }

  // Move the video out of the camera's cache, which iOS may purge. If the move
  // fails, copy instead; if that fails too, keep the video where the camera left
  // it rather than lose the survey. move() and copy() are async in this SDK
  // (delete/create/write are sync); without the await the file is read before
  // it has arrived.
  const warnings = [];
  // Named by session so copies saved to Files or Photos do not collide.
  let video = new File(dir, `${session.id}.${ext}`);
  try {
    if (!dir.exists) dir.create({ intermediates: true });
    if (video.exists) video.delete();
    try {
      await source.move(video);
    } catch (moveError) {
      console.warn(`[capture] move ${source.uri} -> ${video.uri} failed: ${moveError.message}`);
      await source.copy(video);
      source.delete();
    }
  } catch (e) {
    console.warn(`[capture] could not relocate ${source.uri}: ${e.message}`);
    video = new File(videoUri);
    warnings.push('The video could not be moved into app storage and is still in the camera cache. Upload it soon: iOS may delete that cache when storage runs low.');
  }

  if (!movieIsFinalized(video)) {
    // No `moov` index: the server would accept the upload and then fail to read it.
    updateSession(session.id, {
      status: 'failed', broken: true, endReason, videoUri: video.uri, videoBytes: video.size,
      lastError: 'The camera stopped before it finished writing the video, so the file cannot be played or processed.',
    });
    return;
  }

  const { points: logged, errors } = readPoints(pointsFileFor(session.id));
  const { points, dropped: stalePoints } = dropStalePoints(cleanPoints(logged));
  const { timeOffsetS, skewMs } = computeTimeOffset(points, videoStartMs);
  const gaps = findGaps(points);
  const durationS = (stopMs - videoStartMs) / 1000;
  const hz = points.length > 1 ? (points.length - 1) / ((points[points.length - 1].t - points[0].t) / 1000) : 0;

  let gpxUri = null;
  if (points.length) {
    const gpx = new File(dir, `${session.id}.gpx`);
    gpx.write(buildGpx({
      name: session.id,
      points,
      capture: {
        sessionId: session.id,
        videoStart: new Date(videoStartMs).toISOString(),
        videoStartSource: 'device_clock_at_record_call',
        timeOffsetS: timeOffsetS.toFixed(3),
        clockSkewMs: Math.round(skewMs),
        timeSource: 'location_fix_timestamp',
        points: points.length,
        achievedHz: hz.toFixed(2),
        gpsErrors: errors.length,
        mockedPoints: points.filter((p) => p.mocked).length,
        stalePointsDropped: stalePoints,
        platform: `${Platform.OS} ${Platform.Version}`,
        locationPermission: session.locationPermission || 'unknown',
        cameraPitchDegAtStart: session.cameraPitchDeg ?? 'unknown',
        cameraRollDegAtStart: session.cameraRollDeg ?? 'unknown',
        videoContainer: ext,
      },
    }));
    gpxUri = gpx.uri;
  }

  if (!points.length) warnings.push('No GPS fixes were logged. The survey will upload without a track and must be placed by hand on the web app.');
  if (errors.length) warnings.push(`GPS reported ${errors.length} error(s) during recording (${errors[0].error}).`);
  if (gaps.length) warnings.push(`${gaps.length} gap(s) in the GPS track, longest ${Math.max(...gaps.map((g) => g.seconds))} s.`);
  if (endReason === 'app_left_foreground') warnings.push('Recording stopped because the app left the screen. The video covers only the part before that.');
  if (recovered) warnings.push('The camera reported an error when it stopped; the video was recovered from its cache and checked as complete.');

  updateSession(session.id, {
    status: 'recorded',
    videoUri: video.uri,
    videoExt: ext,
    videoMime: mime,
    platform: Platform.OS,
    gpxUri,
    videoBytes: video.size,
    durationS,
    timeOffsetS,
    clockSkewMs: skewMs,
    pointCount: points.length,
    achievedHz: hz,
    gaps,
    gpsErrors: errors.length,
    stalePoints,
    endReason,
    warnings,
  });
}

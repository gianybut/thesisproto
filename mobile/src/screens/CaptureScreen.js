import { useEffect, useRef, useState } from 'react';
import { AppState, Linking, ScrollView, Text, useWindowDimensions, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Location from 'expo-location';
import { activateKeepAwakeAsync, deactivateKeepAwake } from 'expo-keep-awake';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  CLIP_HARD_STOP_S, CLIP_S, GPS_STALE_MS, MAX_VIDEO_BYTES, MIN_FIX_ACCURACY_M, MIN_FREE_BYTES, VIDEO_BITRATE, VIDEO_QUALITY,
} from '../config';
import { finalizeSession, runPointsFile } from '../capture';
import { onFix, startLogging, stopLogging } from '../locationTask';
import { findOrphanedRecording, freeBytes, IS_IOS, recordingPlatformOptions } from '../platform';
import { resetLines, setLine, useRoadBand } from '../roadBand';
import {
  addSession, deleteRunDir, getSession, getSessions, newSessionId, subscribe, updateSession,
} from '../storage';
import { enqueue, setPaused } from '../uploadQueue';
import AppBar from '../components/AppBar';
import Button from '../components/Button';
import Notice from '../components/Notice';
import PageHeader from '../components/PageHeader';
import StatusLabel from '../components/StatusLabel';
import Icon from '../icons';
import RoadBandOverlay from '../components/RoadBandOverlay';
import { formatClock } from '../labels';
import { horizonFromTilt, levelStatus, useLevel } from '../level';
import ReviewScreen from './ReviewScreen';
import { C, F, S, T, s } from '../theme';

const KEEP_AWAKE_TAG = 'bk-recording';
// A clip's GPS stretch runs a few seconds past its end (capture.js); wait for those fixes before
// cutting it out of the log, while the next clip is already recording.
const NEXT_CLIP_GPS_WAIT_MS = 4000;
const SIDE_PANEL_W = 260;   // landscape: controls beside the preview, never over it
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const notUploaded = (list) => list.filter((x) => !x.broken && ['recorded', 'queued', 'uploading', 'failed'].includes(x.status)).length;

export default function CaptureScreen({ onShowSessions }) {
  const insets = useSafeAreaInsets();
  const [camPerm, requestCamPerm, getCamPerm] = useCameraPermissions();
  const [locPerm, setLocPerm] = useState(null); // null | 'granted' | 'denied'
  const [locCanAsk, setLocCanAsk] = useState(true);
  const [iosAlways, setIosAlways] = useState(null); // iOS only: null | true | false
  const [cameraReady, setCameraReady] = useState(false);
  const [fix, setFix] = useState(null); // { acc, at }
  const [phase, setPhase] = useState('idle'); // idle | recording | finishing | review
  const [elapsed, setElapsed] = useState(0);       // whole recording
  const [clipElapsed, setClipElapsed] = useState(0);
  const [part, setPart] = useState(1);
  const [gpsError, setGpsError] = useState(null);
  const [message, setMessage] = useState(null);
  const [reviewIds, setReviewIds] = useState(null);
  const [now, setNow] = useState(() => Date.now());
  const [toUpload, setToUpload] = useState(() => notUploaded(getSessions()));
  const [area, setArea] = useState(null); // the space left for the preview, { w, h }
  const level = useLevel();
  const { width: winW, height: winH } = useWindowDimensions();
  const landscape = winW > winH;
  const band = useRoadBand(landscape, horizonFromTilt(level, landscape));

  const cameraRef = useRef(null);
  // The recording in progress, across its clips:
  // { runId, startMs, clipStartMs, part, clipReason, userStopped, timer, band, sessionIds }
  const rec = useRef(null);
  const appState = useRef(AppState.currentState);

  useEffect(() => subscribe((list) => setToUpload(notUploaded(list))), []);

  // Permissions. Camera through the hook; location asked once here.
  //
  // iOS: "While Using" is enough for a session. Updates are started from the
  // foreground with UIBackgroundModes=location, so iOS keeps delivering them if
  // the app is backgrounded (blue status-bar pill). "Always" additionally lets
  // iOS relaunch the app after terminating it, so it is asked for once, and a
  // refusal is shown rather than blocking recording. Android keeps the original
  // flow: the foreground service needs only the foreground permission.
  useEffect(() => {
    (async () => {
      const fg = await Location.requestForegroundPermissionsAsync();
      const granted = fg.status === 'granted';
      setLocPerm(granted ? 'granted' : 'denied');
      setLocCanAsk(fg.canAskAgain !== false);
      if (granted && IS_IOS) {
        const bg = await Location.requestBackgroundPermissionsAsync().catch(() => ({ status: 'denied' }));
        setIosAlways(bg.status === 'granted');
      }
    })();
  }, []);

  async function askLocation() {
    const fg = await Location.requestForegroundPermissionsAsync();
    setLocPerm(fg.status === 'granted' ? 'granted' : 'denied');
    setLocCanAsk(fg.canAskAgain !== false);
  }

  // Fix status before recording. Stops while recording (the background task
  // takes over and reports through onFix).
  useEffect(() => {
    if (locPerm !== 'granted' || phase !== 'idle') return undefined;
    let sub;
    let cancelled = false;
    Location.watchPositionAsync(
      { accuracy: Location.Accuracy.BestForNavigation, timeInterval: 1000, distanceInterval: 0 },
      (loc) => {
        // Ignore a cached last-known fix: its accuracy says nothing about now.
        if (Date.now() - loc.timestamp > GPS_STALE_MS) return;
        setFix({ acc: loc.coords.accuracy, at: Date.now() });
      },
    ).then((x) => {
      if (cancelled) x.remove();
      else sub = x;
    }).catch((e) => setGpsError(e.message));
    return () => {
      cancelled = true;
      sub?.remove();
    };
  }, [locPerm, phase]);

  useEffect(() => onFix((p) => {
    if (p.error) setGpsError(p.error);
    else {
      setGpsError(null);
      setFix({ acc: p.acc, at: Date.now() });
    }
  }), []);

  // One-second clock for elapsed time and fix age.
  useEffect(() => {
    const t = setInterval(() => {
      setNow(Date.now());
      if (rec.current) {
        setElapsed((Date.now() - rec.current.startMs) / 1000);
        setClipElapsed((Date.now() - rec.current.clipStartMs) / 1000);
      }
    }, 500);
    return () => clearInterval(t);
  }, []);

  // Android stops the camera when the app leaves the screen, which ends the
  // recording; note why so the session says so. Coming back also re-reads the
  // permissions, so turning them on in Settings unlocks the camera without a restart.
  useEffect(() => {
    const sub = AppState.addEventListener('change', (next) => {
      if (rec.current && appState.current === 'active' && next !== 'active' && !rec.current.clipReason) {
        rec.current.clipReason = 'app_left_foreground';
      }
      if (next === 'active' && appState.current !== 'active') {
        getCamPerm();
        Location.getForegroundPermissionsAsync().then((fg) => {
          setLocPerm(fg.status === 'granted' ? 'granted' : 'denied');
          setLocCanAsk(fg.canAskAgain !== false);
        }).catch(() => {});
      }
      appState.current = next;
    });
    return () => sub.remove();
  }, [getCamPerm]);

  const fixAge = fix ? now - fix.at : Infinity;
  const fixGood = fix && fixAge < GPS_STALE_MS && fix.acc != null && fix.acc <= MIN_FIX_ACCURACY_M;

  // A recording has no time limit. It is saved as clips of CLIP_S seconds: when a clip is due,
  // the camera stops and the next clip starts straight away (a gap of well under a second), and
  // the finished clip is saved while the next one records. Each clip is its own survey (session)
  // with its own GPX, so uploads and the server stay within the 10-minute limit. GPS is logged
  // once for the whole recording and cut per clip, so the track has no gaps between clips.
  async function start() {
    setMessage(null);
    const free = await freeBytes();
    if (free < MIN_FREE_BYTES) {
      setMessage(`Not enough free space to record: a survey needs ${Math.round(MIN_FREE_BYTES / 1048576)} MB and the phone has ${Math.round(free / 1048576)} MB. Delete surveys that are already uploaded, then try again.`);
      return;
    }
    setPaused(true);
    const runId = newSessionId();
    const pointsFile = runPointsFile(runId);
    try {
      await startLogging(runId, pointsFile);
    } catch (e) {
      deleteRunDir(runId);
      setMessage(`GPS logging could not start: ${e.message}`);
      setPaused(false);
      return;
    }
    await activateKeepAwakeAsync(KEEP_AWAKE_TAG);

    const run = {
      runId, startMs: Date.now(), clipStartMs: Date.now(), part: 0, clipReason: null, userStopped: false, timer: null,
      // The band is fixed for the whole recording, as the lines stood when it started.
      band: { top: band.top, bottom: band.bottom },
      tilt: level.available ? { pitch: level.pitch, roll: level.roll } : null,
      sessionIds: [],
    };
    rec.current = run;
    setElapsed(0);
    setClipElapsed(0);
    setPhase('recording');

    const saving = [];
    for (;;) {
      const clip = await recordClip(run);
      const more = clip.endReason === 'next_clip' && !run.userStopped;
      saving.push(saveClip(clip, pointsFile, more ? NEXT_CLIP_GPS_WAIT_MS : 0));
      if (!more) break;
    }

    rec.current = null;
    deactivateKeepAwake(KEEP_AWAKE_TAG);
    setPhase('finishing');
    await stopLogging();
    await Promise.all(saving);
    deleteRunDir(runId);
    // Each clip learns how many parts the recording has, for its title ("part 2 of 3").
    run.sessionIds.forEach((id) => updateSession(id, { parts: run.part }));
    setPaused(false);
    setReviewIds(run.sessionIds);
    setPhase('review');
  }

  /** Record one clip. Resolves when it stops, with what saveClip needs. */
  async function recordClip(run) {
    run.part += 1;
    run.clipReason = null;
    const id = newSessionId();
    const session = {
      id, runId: run.runId, part: run.part, createdAt: Date.now(), status: 'recording', roadName: '',
      // Recorded for the write-up; on iOS "while_using" still logs in the background (see effect above).
      locationPermission: IS_IOS ? (iosAlways ? 'always' : 'while_using') : 'foreground_service',
      // Camera tilt when recording started, for the write-up (src/level.js); null if no sensor.
      cameraPitchDeg: run.tilt?.pitch ?? null,
      cameraRollDeg: run.tilt?.roll ?? null,
      // Road band sent with the upload (src/roadBand.js).
      roadTop: run.band.top,
      roadBottom: run.band.bottom,
    };
    addSession(session);
    run.sessionIds.push(id);
    setPart(run.part);

    const startMs = Date.now();
    run.clipStartMs = startMs;
    setClipElapsed(0);
    // Cut the clip on time; stop the recording instead if the next clip would not fit on the phone.
    run.timer = setTimeout(async () => {
      if (run.clipReason) return;
      const free = await freeBytes().catch(() => Infinity);
      if (run.clipReason) return;
      run.clipReason = free < MIN_FREE_BYTES ? 'storage_full' : 'next_clip';
      cameraRef.current?.stopRecording();
    }, CLIP_S * 1000);

    let videoUri = null;
    let cameraError = null;
    try {
      const result = await cameraRef.current.recordAsync({
        maxDuration: CLIP_HARD_STOP_S,
        ...(MAX_VIDEO_BYTES ? { maxFileSize: MAX_VIDEO_BYTES } : {}),
        ...recordingPlatformOptions(),
      });
      videoUri = result?.uri ?? null;
    } catch (e) {
      cameraError = e.message;
    }
    clearTimeout(run.timer);
    let recovered = false;
    if (!videoUri && IS_IOS) {
      const orphan = findOrphanedRecording(startMs);
      if (orphan) {
        videoUri = orphan.uri;
        recovered = true; // finalizeSession still checks the file is complete
      }
    }

    const stopMs = Date.now();
    const reason = run.clipReason;
    let endReason;
    if (reason === 'app_left_foreground') endReason = reason;
    else if (!videoUri) endReason = cameraError ? 'camera_error' : 'camera_stopped';
    else if (reason) endReason = reason; // stopped | next_clip | storage_full
    // The camera's own limit came first (the timer ran late): carry on as if the timer had fired.
    else if ((stopMs - startMs) / 1000 >= CLIP_HARD_STOP_S - 2) endReason = 'next_clip';
    else if (cameraError) endReason = 'camera_error';
    else endReason = MAX_VIDEO_BYTES ? 'size_cap' : 'camera_stopped';
    return { session, videoUri, startMs, stopMs, endReason, cameraError, recovered };
  }

  async function saveClip(clip, pointsFile, gpsWaitMs) {
    if (gpsWaitMs) await wait(gpsWaitMs);
    try {
      await finalizeSession(clip.session, {
        videoUri: clip.videoUri, videoStartMs: clip.startMs, stopMs: clip.stopMs, endReason: clip.endReason,
        cameraError: clip.cameraError, recovered: clip.recovered, pointsFile,
      });
    } catch (e) {
      // Nothing upload-ready was stored, so there is nothing to retry.
      updateSession(clip.session.id, { status: 'failed', broken: true, lastError: `Could not save the survey: ${e.message}` });
    }
  }

  function stop() {
    const run = rec.current;
    if (!run) return;
    run.userStopped = true;
    if (!run.clipReason) run.clipReason = 'stopped';
    clearTimeout(run.timer);
    cameraRef.current?.stopRecording();
  }

  function finishReview({ upload, roadName }) {
    for (const id of reviewIds) {
      const sess = getSession(id);
      if (sess && roadName.trim()) updateSession(id, { roadName: roadName.trim() });
      if (upload && sess?.status === 'recorded') enqueue(id);
    }
    setReviewIds(null);
    setPhase('idle');
    if (upload) onShowSessions();
  }

  // ---- Permission gates ----
  if (!camPerm || locPerm === null) {
    return <View style={s.screen}><AppBar /></View>;
  }
  if (!camPerm.granted || locPerm !== 'granted') {
    const askCamera = !camPerm.granted && camPerm.canAskAgain;
    const askLoc = !askCamera && locPerm !== 'granted' && locCanAsk;
    return (
      <View style={s.screen}>
        <AppBar />
        <ScrollView contentContainerStyle={s.page}>
          <PageHeader title="Allow the camera and location" />
          <View style={s.stack}>
            <Text style={s.body}>
              Recording a survey needs the camera and this phone&apos;s location. The location places each damage
              found on the map. Video without it has to be placed by hand on the web app.
            </Text>
            <View style={{ gap: S[2] }}>
              <Need ok={camPerm.granted} label="Camera" />
              <Need ok={locPerm === 'granted'} label="Location" />
            </View>
            <View style={{ gap: S[3] }}>
              {askCamera && <Button label="Allow the camera" variant="primary" block onPress={requestCamPerm} />}
              {askLoc && <Button label="Allow location" variant="primary" block onPress={askLocation} />}
              <Button label="Open Settings" block onPress={() => Linking.openSettings()} />
              {!askCamera && !askLoc && (
                <Text style={s.fieldHint}>Turn on Camera and Location for OcuLubak in Settings, then come back here.</Text>
              )}
            </View>
            <Button label="See surveys on this phone" icon="video" variant="quiet" onPress={onShowSessions} />
          </View>
        </ScrollView>
      </View>
    );
  }

  // ---- Review after stop ----
  if (phase === 'review') {
    return <ReviewScreen sessionIds={reviewIds} onDone={finishReview} />;
  }

  // ---- Camera ----
  const recording = phase === 'recording';
  const idle = phase === 'idle';

  let gps;
  if (gpsError) gps = { icon: 'alert-circle', tone: 'failed', text: 'GPS error' };
  else if (!fix) gps = { icon: 'clock', tone: 'waiting', text: 'Waiting for GPS' };
  else if (fixAge >= GPS_STALE_MS) gps = { icon: 'alert-circle', tone: 'failed', text: `GPS lost ${Math.round(fixAge / 1000)} s ago` };
  else if (!fixGood) gps = { icon: 'alert-triangle', tone: recording ? 'running' : 'waiting', text: `GPS ±${fix.acc?.toFixed(0) ?? '?'} m, too weak` };
  else gps = { icon: 'check', tone: 'ready', text: `GPS ±${fix.acc.toFixed(0)} m` };

  const canStart = idle && cameraReady && fixGood;
  // While recording, the lines stay where they were when it started.
  const shownBand = recording && rec.current ? rec.current.band : band;
  // Advice only; recording is never blocked on the mount (it cannot always be adjusted).
  const tilt = levelStatus(level, band);
  // design.md §7: a disabled button always shows why.
  let hint = null;
  if (idle && !cameraReady) hint = 'Starting the camera…';
  else if (idle && gpsError) hint = `GPS error: ${gpsError}`;
  else if (idle && !fixGood) hint = `Recording can start once GPS is within ±${MIN_FIX_ACCURACY_M} m. Stay under open sky.`;
  else if (recording && gpsError) hint = `GPS error: ${gpsError}. The video keeps recording.`;

  // The preview gets its own box of the recording's shape (16:9, or 9:16 upright), fitted into
  // the space the controls leave. Nothing is drawn over it but the road lines, so the whole
  // recorded frame is visible and a line on screen is the same line in the video. Android's
  // camera shows the full frame in that box with ratio 16:9; iOS fills it, which for a box of
  // the same shape is the same thing.
  const aspect = landscape ? 16 / 9 : 9 / 16;
  let box = null;
  if (area) {
    const w = Math.min(area.w, area.h * aspect);
    box = { width: Math.floor(w), height: Math.floor(w / aspect) };
  }

  const clock = (
    <View style={{ gap: S[1] }}>
      <View style={[s.row, { gap: S[2] }]} accessibilityLabel={recording ? `Recording, ${formatClock(elapsed)}` : 'Not recording'}>
        {recording && <Icon name="record" size={16} color={C.danger} />}
        <Text style={{ fontFamily: F.bold, fontSize: 28, lineHeight: 34, color: '#FFFFFF', fontVariant: ['tabular-nums'] }}>
          {formatClock(elapsed)}
        </Text>
      </View>
      <Text style={{ fontFamily: F.regular, ...T.sm, color: C.headerMuted, fontVariant: ['tabular-nums'] }}>
        {recording
          ? `Part ${part} · ${formatClock(clipElapsed)} of ${formatClock(CLIP_S)}`
          : `No time limit. Saved in ${formatClock(CLIP_S)} parts.`}
      </Text>
    </View>
  );

  const statuses = (
    <View style={[s.row, { gap: S[2], flexWrap: 'wrap' }]}>
      <StatusLabel status={gps} />
      <StatusLabel status={tilt.status} />
    </View>
  );

  const notes = (
    <>
      {message && <Notice kind="error">{message}</Notice>}
      {hint && <Text style={{ fontFamily: F.regular, ...T.sm, color: '#FFFFFF' }}>{hint}</Text>}
      {tilt.advice && <Text style={{ fontFamily: F.regular, ...T.sm, color: '#FFFFFF' }}>{tilt.advice}</Text>}
      {idle && (
        <Text style={{ fontFamily: F.regular, ...T.sm, color: C.headerMuted }}>
          Drag Horizon to where the road ends and Bonnet to the top of the bonnet. Damage is looked for between the lines.
        </Text>
      )}
      {idle && band.manual && (
        <Button label="Reset the lines" icon="refresh" variant="onDark" onPress={() => resetLines(landscape)} />
      )}
    </>
  );

  const actions = (
    <View style={{ gap: S[3] }}>
      {phase === 'finishing' ? (
        <View style={{ minHeight: 64, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ fontFamily: F.semibold, ...T.base, color: '#FFFFFF', textAlign: 'center' }}>Saving the video and GPS track…</Text>
        </View>
      ) : recording ? (
        <Button label="Stop recording" icon="stop" iconColor={C.danger} size="large" block onPress={stop} />
      ) : (
        <Button label="Start recording" icon="record" variant="primary" size="large" block disabled={!canStart} onPress={start} />
      )}
      {idle && (
        <Button
          label={toUpload ? `Surveys · ${toUpload} to upload` : 'Surveys on this phone'}
          icon="video"
          variant="onDark"
          block
          onPress={onShowSessions}
        />
      )}
    </View>
  );

  // The preview stays the second child in both orientations, so turning the phone resizes the
  // camera instead of starting it again.
  return (
    <View style={{ flex: 1, backgroundColor: C.ink, flexDirection: landscape ? 'row' : 'column', paddingLeft: insets.left, paddingRight: insets.right }}>
      {landscape ? null : (
        <View style={{ paddingTop: insets.top + S[3], paddingBottom: S[3], paddingHorizontal: S.gutter, gap: S[2] }}>
          <View style={[s.row, { justifyContent: 'space-between', alignItems: 'flex-start', gap: S[3] }]}>
            {clock}
          </View>
          {statuses}
        </View>
      )}

      <View
        style={{
          flex: 1, alignItems: 'center', justifyContent: 'center',
          paddingTop: landscape ? insets.top : 0, paddingBottom: landscape ? insets.bottom : 0,
        }}
        onLayout={(e) => {
          const { width, height } = e.nativeEvent.layout;
          const h = height - (landscape ? insets.top + insets.bottom : 0);
          setArea((a) => (a && a.w === width && a.h === h ? a : { w: width, h }));
        }}
      >
        {box && (
          <View style={box}>
            <CameraView
              ref={cameraRef}
              style={{ flex: 1 }}
              facing="back"
              mode="video"
              mute
              ratio="16:9"
              videoQuality={VIDEO_QUALITY}
              videoBitrate={VIDEO_BITRATE}
              onCameraReady={() => setCameraReady(true)}
              onMountError={(e) => setMessage(`The camera could not start: ${e.message}. Close the app and open it again.`)}
            />
            <RoadBandOverlay
              band={shownBand}
              height={box.height}
              editable={idle}
              onMove={(which, y) => setLine(landscape, which, y, band.topSet ? undefined : band.top)}
            />
          </View>
        )}
      </View>

      {landscape ? (
        <View style={{ width: SIDE_PANEL_W, paddingTop: insets.top + S[3], paddingBottom: insets.bottom + S[3], paddingLeft: S[4], gap: S[3] }}>
          <ScrollView style={{ flex: 1 }} contentContainerStyle={{ gap: S[3] }}>
            {clock}
            {statuses}
            {notes}
          </ScrollView>
          {actions}
        </View>
      ) : (
        <View style={{ paddingTop: S[3], paddingBottom: insets.bottom + S[3], paddingHorizontal: S.gutter, gap: S[3] }}>
          <ScrollView style={{ maxHeight: 132 }} contentContainerStyle={{ gap: S[2] }}>
            {notes}
          </ScrollView>
          {actions}
        </View>
      )}
    </View>
  );
}

function Need({ ok, label }) {
  return (
    <StatusLabel status={ok
      ? { icon: 'check', tone: 'ready', text: `${label} allowed` }
      : { icon: 'alert-circle', tone: 'failed', text: `${label} not allowed` }}
    />
  );
}

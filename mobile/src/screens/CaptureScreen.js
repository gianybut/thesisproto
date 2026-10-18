import { useEffect, useRef, useState } from 'react';
import { AppState, Linking, ScrollView, Text, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Location from 'expo-location';
import { activateKeepAwakeAsync, deactivateKeepAwake } from 'expo-keep-awake';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  GPS_STALE_MS, MAX_RECORD_S, MAX_VIDEO_BYTES, MIN_FIX_ACCURACY_M, MIN_FREE_BYTES, VIDEO_BITRATE, VIDEO_QUALITY,
} from '../config';
import { finalizeSession, pointsFileFor } from '../capture';
import { onFix, startLogging } from '../locationTask';
import { findOrphanedRecording, freeBytes, IS_IOS, recordingPlatformOptions } from '../platform';
import { addSession, getSession, getSessions, newSessionId, subscribe, updateSession } from '../storage';
import { enqueue, setPaused } from '../uploadQueue';
import AppBar from '../components/AppBar';
import Button from '../components/Button';
import Notice from '../components/Notice';
import PageHeader from '../components/PageHeader';
import StatusLabel from '../components/StatusLabel';
import Icon from '../icons';
import { formatClock } from '../labels';
import ReviewScreen from './ReviewScreen';
import { C, F, S, T, s } from '../theme';

const KEEP_AWAKE_TAG = 'bk-recording';
const notUploaded = (list) => list.filter((x) => !x.broken && ['recorded', 'queued', 'uploading', 'failed'].includes(x.status)).length;

export default function CaptureScreen({ onShowSessions, onSignOut }) {
  const insets = useSafeAreaInsets();
  const [camPerm, requestCamPerm, getCamPerm] = useCameraPermissions();
  const [locPerm, setLocPerm] = useState(null); // null | 'granted' | 'denied'
  const [locCanAsk, setLocCanAsk] = useState(true);
  const [iosAlways, setIosAlways] = useState(null); // iOS only: null | true | false
  const [cameraReady, setCameraReady] = useState(false);
  const [fix, setFix] = useState(null); // { acc, at }
  const [phase, setPhase] = useState('idle'); // idle | recording | finishing | review
  const [elapsed, setElapsed] = useState(0);
  const [gpsError, setGpsError] = useState(null);
  const [message, setMessage] = useState(null);
  const [reviewId, setReviewId] = useState(null);
  const [now, setNow] = useState(() => Date.now());
  const [toUpload, setToUpload] = useState(() => notUploaded(getSessions()));

  const cameraRef = useRef(null);
  const rec = useRef(null); // { session, startMs, stopReason }
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
      if (rec.current) setElapsed((Date.now() - rec.current.startMs) / 1000);
    }, 500);
    return () => clearInterval(t);
  }, []);

  // Android stops the camera when the app leaves the screen, which ends the
  // recording; note why so the session says so. Coming back also re-reads the
  // permissions, so turning them on in Settings unlocks the camera without a restart.
  useEffect(() => {
    const sub = AppState.addEventListener('change', (next) => {
      if (rec.current && appState.current === 'active' && next !== 'active' && !rec.current.stopReason) {
        rec.current.stopReason = 'app_left_foreground';
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

  async function start() {
    setMessage(null);
    const free = await freeBytes();
    if (free < MIN_FREE_BYTES) {
      setMessage(`Not enough free space to record: a survey needs ${Math.round(MIN_FREE_BYTES / 1048576)} MB and the phone has ${Math.round(free / 1048576)} MB. Delete surveys that are already uploaded, then try again.`);
      return;
    }
    setPaused(true);
    const id = newSessionId();
    const session = {
      id, createdAt: Date.now(), status: 'recording', roadName: '',
      // Recorded for the write-up; on iOS "while_using" still logs in the background (see effect above).
      locationPermission: IS_IOS ? (iosAlways ? 'always' : 'while_using') : 'foreground_service',
    };
    addSession(session);

    try {
      await startLogging(id, pointsFileFor(id));
    } catch (e) {
      updateSession(id, { status: 'failed', broken: true, lastError: `GPS logging could not start: ${e.message}` });
      setMessage(`GPS logging could not start: ${e.message}`);
      setPaused(false);
      return;
    }
    await activateKeepAwakeAsync(KEEP_AWAKE_TAG);

    const startMs = Date.now();
    rec.current = { session, startMs, stopReason: null };
    setElapsed(0);
    setPhase('recording');

    let videoUri = null;
    let cameraError = null;
    try {
      const result = await cameraRef.current.recordAsync({
        maxDuration: MAX_RECORD_S,
        ...(MAX_VIDEO_BYTES ? { maxFileSize: MAX_VIDEO_BYTES } : {}),
        ...recordingPlatformOptions(),
      });
      videoUri = result?.uri ?? null;
    } catch (e) {
      cameraError = e.message;
    }
    let recovered = false;
    if (!videoUri && IS_IOS) {
      const orphan = findOrphanedRecording(startMs);
      if (orphan) {
        videoUri = orphan.uri;
        recovered = true; // finalizeSession still checks the file is complete
      }
    }

    const stopMs = Date.now();
    const recordedS = (stopMs - startMs) / 1000;
    const endReason = rec.current.stopReason === 'app_left_foreground' ? 'app_left_foreground'
      : cameraError ? 'camera_error'
      : rec.current.stopReason || (recordedS >= MAX_RECORD_S - 1 ? 'duration_cap'
        : MAX_VIDEO_BYTES ? 'size_cap' : 'camera_stopped');
    rec.current = null;
    deactivateKeepAwake(KEEP_AWAKE_TAG);
    setPhase('finishing');

    try {
      await finalizeSession(session, { videoUri, videoStartMs: startMs, stopMs, endReason, cameraError, recovered });
    } catch (e) {
      // Nothing upload-ready was stored, so there is nothing to retry.
      updateSession(id, { status: 'failed', broken: true, lastError: `Could not save the survey: ${e.message}` });
    }
    setPaused(false);
    setReviewId(id);
    setPhase('review');
  }

  function stop() {
    if (!rec.current) return;
    rec.current.stopReason = 'stopped';
    cameraRef.current?.stopRecording();
  }

  function finishReview({ upload, roadName }) {
    const sess = getSession(reviewId);
    if (sess && roadName.trim()) updateSession(reviewId, { roadName: roadName.trim() });
    if (upload && sess?.status === 'recorded') enqueue(reviewId);
    setReviewId(null);
    setPhase('idle');
    if (upload) onShowSessions();
  }

  // ---- Permission gates ----
  if (!camPerm || locPerm === null) {
    return <View style={s.screen}><AppBar onSignOut={onSignOut} /></View>;
  }
  if (!camPerm.granted || locPerm !== 'granted') {
    const askCamera = !camPerm.granted && camPerm.canAskAgain;
    const askLoc = !askCamera && locPerm !== 'granted' && locCanAsk;
    return (
      <View style={s.screen}>
        <AppBar onSignOut={onSignOut} />
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
    return <ReviewScreen sessionId={reviewId} onDone={finishReview} onSignOut={onSignOut} />;
  }

  // ---- Camera ----
  const recording = phase === 'recording';
  const remaining = Math.max(0, MAX_RECORD_S - elapsed);

  let gps;
  if (gpsError) gps = { icon: 'alert-circle', tone: 'failed', text: 'GPS error' };
  else if (!fix) gps = { icon: 'clock', tone: 'waiting', text: 'Waiting for GPS' };
  else if (fixAge >= GPS_STALE_MS) gps = { icon: 'alert-circle', tone: 'failed', text: `GPS lost ${Math.round(fixAge / 1000)} s ago` };
  else if (!fixGood) gps = { icon: 'alert-triangle', tone: recording ? 'running' : 'waiting', text: `GPS ±${fix.acc?.toFixed(0) ?? '?'} m, too weak` };
  else gps = { icon: 'check', tone: 'ready', text: `GPS ±${fix.acc.toFixed(0)} m` };

  const canStart = phase === 'idle' && cameraReady && fixGood;
  // design.md §7: a disabled button always shows why.
  let hint = null;
  if (phase === 'idle' && !cameraReady) hint = 'Starting the camera…';
  else if (phase === 'idle' && gpsError) hint = `GPS error: ${gpsError}`;
  else if (phase === 'idle' && !fixGood) hint = `Recording can start once GPS is within ±${MIN_FIX_ACCURACY_M} m. Stay under open sky.`;
  else if (recording && gpsError) hint = `GPS error: ${gpsError}. The video keeps recording.`;

  return (
    <View style={{ flex: 1, backgroundColor: C.ink }}>
      <CameraView
        ref={cameraRef}
        style={{ flex: 1 }}
        facing="back"
        mode="video"
        mute
        videoQuality={VIDEO_QUALITY}
        videoBitrate={VIDEO_BITRATE}
        onCameraReady={() => setCameraReady(true)}
        onMountError={(e) => setMessage(`The camera could not start: ${e.message}. Close the app and open it again.`)}
      />

      <View style={{
        position: 'absolute', top: 0, left: 0, right: 0, backgroundColor: C.scrim,
        paddingTop: insets.top + S[3], paddingBottom: S[3], paddingHorizontal: S.gutter, gap: S[2],
      }}
      >
        <View style={[s.row, { justifyContent: 'space-between' }]}>
          <View
            style={[s.row, { gap: S[2] }]}
            accessibilityLabel={recording ? `Recording, ${formatClock(elapsed)}` : 'Not recording'}
          >
            {recording && <Icon name="record" size={16} color={C.danger} />}
            <Text style={{ fontFamily: F.bold, fontSize: 28, lineHeight: 34, color: '#FFFFFF', fontVariant: ['tabular-nums'] }}>
              {formatClock(elapsed)}
            </Text>
          </View>
          {recording && remaining <= 60 ? (
            <StatusLabel status={{ icon: 'clock', tone: 'failed', text: `${formatClock(remaining)} left` }} />
          ) : (
            <Text style={{ fontFamily: F.regular, ...T.sm, color: C.headerMuted, fontVariant: ['tabular-nums'] }}>
              {formatClock(remaining)} left
            </Text>
          )}
        </View>
        <StatusLabel status={gps} />
      </View>

      <View style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: C.scrim,
        paddingTop: S[4], paddingBottom: insets.bottom + S[4], paddingHorizontal: S.gutter, gap: S[3],
      }}
      >
        {message && <Notice kind="error">{message}</Notice>}
        {hint && <Text style={{ fontFamily: F.regular, ...T.sm, color: '#FFFFFF' }}>{hint}</Text>}
        {phase === 'finishing' ? (
          <View style={{ minHeight: 64, alignItems: 'center', justifyContent: 'center' }}>
            <Text style={{ fontFamily: F.semibold, ...T.base, color: '#FFFFFF' }}>Saving the video and GPS track…</Text>
          </View>
        ) : recording ? (
          <Button label="Stop recording" icon="stop" iconColor={C.danger} size="large" block onPress={stop} />
        ) : (
          <Button label="Start recording" icon="record" variant="primary" size="large" block disabled={!canStart} onPress={start} />
        )}
        {phase === 'idle' && (
          <Button
            label={toUpload ? `Surveys · ${toUpload} to upload` : 'Surveys on this phone'}
            icon="video"
            variant="onDark"
            block
            onPress={onShowSessions}
          />
        )}
      </View>
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

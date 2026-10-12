import { useEffect, useRef, useState } from 'react';
import { AppState, Linking, Pressable, Text, TextInput, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Location from 'expo-location';
import { activateKeepAwakeAsync, deactivateKeepAwake } from 'expo-keep-awake';
import {
  GPS_STALE_MS, MAX_RECORD_S, MAX_VIDEO_BYTES, MIN_FIX_ACCURACY_M, MIN_FREE_BYTES, VIDEO_BITRATE, VIDEO_QUALITY,
} from '../config';
import { finalizeSession, pointsFileFor } from '../capture';
import { onFix, startLogging } from '../locationTask';
import { findOrphanedRecording, freeBytes, IS_IOS, recordingPlatformOptions } from '../platform';
import { addSession, getSession, newSessionId, updateSession } from '../storage';
import { enqueue, setPaused } from '../uploadQueue';
import { C, MONO, s } from '../theme';

const KEEP_AWAKE_TAG = 'bk-recording';
// Warnings over the camera: --card text on --alert, legible on any scene.
const warnBox = { color: C.card, backgroundColor: C.alert, paddingHorizontal: 6, paddingVertical: 2 };
const mmss = (sec) => `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(Math.floor(sec % 60)).padStart(2, '0')}`;

export default function CaptureScreen({ onShowSessions }) {
  const [camPerm, requestCamPerm] = useCameraPermissions();
  const [locPerm, setLocPerm] = useState(null); // null | 'granted' | 'denied'
  const [iosAlways, setIosAlways] = useState(null); // iOS only: null | true | false
  const [cameraReady, setCameraReady] = useState(false);
  const [fix, setFix] = useState(null); // { acc, at }
  const [phase, setPhase] = useState('idle'); // idle | recording | finishing | review
  const [elapsed, setElapsed] = useState(0);
  const [gpsError, setGpsError] = useState(null);
  const [message, setMessage] = useState(null);
  const [reviewId, setReviewId] = useState(null);
  const [roadName, setRoadName] = useState('');
  const [now, setNow] = useState(() => Date.now());

  const cameraRef = useRef(null);
  const rec = useRef(null); // { session, startMs, stopReason }
  const appState = useRef(AppState.currentState);

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
      if (granted && IS_IOS) {
        const bg = await Location.requestBackgroundPermissionsAsync().catch(() => ({ status: 'denied' }));
        setIosAlways(bg.status === 'granted');
      }
    })();
  }, []);

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
  // recording; note why so the session says so.
  useEffect(() => {
    const sub = AppState.addEventListener('change', (next) => {
      if (rec.current && appState.current === 'active' && next !== 'active' && !rec.current.stopReason) {
        rec.current.stopReason = 'app_left_foreground';
      }
      appState.current = next;
    });
    return () => sub.remove();
  }, []);

  const fixAge = fix ? now - fix.at : Infinity;
  const fixGood = fix && fixAge < GPS_STALE_MS && fix.acc != null && fix.acc <= MIN_FIX_ACCURACY_M;

  async function start() {
    setMessage(null);
    const free = await freeBytes();
    if (free < MIN_FREE_BYTES) {
      setMessage(`Not enough free space. Need ${Math.round(MIN_FREE_BYTES / 1048576)} MB, have ${Math.round(free / 1048576)} MB.`);
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
      updateSession(id, { status: 'failed', broken: true, lastError: `Could not save the session: ${e.message}` });
    }
    setPaused(false);
    setReviewId(id);
    setRoadName('');
    setPhase('review');
  }

  function stop() {
    if (!rec.current) return;
    rec.current.stopReason = 'stopped';
    cameraRef.current?.stopRecording();
  }

  function finishReview(queue) {
    const sess = getSession(reviewId);
    if (sess && roadName.trim()) updateSession(reviewId, { roadName: roadName.trim() });
    if (queue && sess?.status === 'recorded') enqueue(reviewId);
    setReviewId(null);
    setPhase('idle');
    if (queue) onShowSessions();
  }

  // ---- Permission gates ----
  if (!camPerm || locPerm === null) {
    return <View style={[s.screen, s.pad]}><Text style={s.soft}>Checking permissions…</Text></View>;
  }
  if (!camPerm.granted || locPerm !== 'granted') {
    return (
      <View style={[s.screen, s.pad]}>
        <Text style={s.h1}>Permissions needed</Text>
        <Text style={[s.body, { marginBottom: 16 }]}>
          Recording a survey needs the camera and your location. Video without a GPS track cannot be placed on the map
          automatically.
        </Text>
        {!camPerm.granted && camPerm.canAskAgain && (
          <Pressable style={[s.btn, s.btnPrimary, { marginBottom: 10 }]} onPress={requestCamPerm}>
            <Text style={s.btnPrimaryText}>Allow camera</Text>
          </Pressable>
        )}
        <Pressable style={[s.btn, s.btnGhost]} onPress={() => Linking.openSettings()}>
          <Text style={s.btnGhostText}>Open app settings</Text>
        </Pressable>
      </View>
    );
  }

  // ---- Review after stop ----
  if (phase === 'review') {
    const sess = getSession(reviewId);
    return (
      <View style={[s.screen, s.pad]}>
        <Text style={s.h1}>Survey recorded</Text>
        {sess && (
          <View style={[s.card, { marginBottom: 16 }]}>
            <Row k="Length" v={sess.durationS != null ? mmss(sess.durationS) : '—'} />
            <Row k="Size" v={sess.videoBytes != null ? `${(sess.videoBytes / 1048576).toFixed(1)} MB` : '—'} />
            <Row k="GPS points" v={String(sess.pointCount ?? 0)} />
            <Row k="Time offset" v={sess.timeOffsetS != null ? `${sess.timeOffsetS.toFixed(2)} s` : '—'} />
            {(sess.warnings || []).map((w) => <Text key={w} style={[s.alert, { marginTop: 8 }]}>{w}</Text>)}
            {sess.status === 'failed' && <Text style={[s.alert, { marginTop: 8 }]}>{sess.lastError}</Text>}
          </View>
        )}
        {sess?.status === 'recorded' && (
          <>
            <Text style={s.label}>Road name (optional)</Text>
            <TextInput style={s.input} value={roadName} onChangeText={setRoadName} placeholder="e.g. Mendez–Tagaytay Rd" placeholderTextColor={C.inkSoft} />
            <Pressable style={[s.btn, s.btnPrimary, { marginBottom: 10 }]} onPress={() => finishReview(true)}>
              <Text style={s.btnPrimaryText}>Queue for upload</Text>
            </Pressable>
          </>
        )}
        <Pressable style={[s.btn, s.btnGhost]} onPress={() => finishReview(false)}>
          <Text style={s.btnGhostText}>{sess?.status === 'recorded' ? 'Keep on phone for now' : 'Back to camera'}</Text>
        </Pressable>
      </View>
    );
  }

  // ---- Camera ----
  const recording = phase === 'recording';
  const remaining = Math.max(0, MAX_RECORD_S - elapsed);
  let gpsLine;
  if (gpsError) gpsLine = `GPS error: ${gpsError}`;
  else if (!fix) gpsLine = 'Waiting for GPS fix…';
  else if (fixAge >= GPS_STALE_MS) gpsLine = `GPS lost ${Math.round(fixAge / 1000)} s ago`;
  else gpsLine = `GPS ±${fix.acc?.toFixed(0) ?? '?'} m`;
  const gpsWarn = !!gpsError || !fix || fixAge >= GPS_STALE_MS || (!recording && !fixGood);

  const canStart = phase === 'idle' && cameraReady && fixGood;
  let hint = null;
  if (phase === 'idle' && !fixGood) {
    hint = `Recording starts once GPS is within ±${MIN_FIX_ACCURACY_M} m. Stay under open sky.`;
  }

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
        onMountError={(e) => setMessage(`Camera error: ${e.message}`)}
      />
      <View style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: 16, paddingTop: 48, backgroundColor: 'rgba(26,29,25,0.72)' }}>
        <View style={[s.row, { justifyContent: 'space-between' }]}>
          <Text style={{ fontFamily: MONO, fontSize: 22, color: C.card }}>{mmss(elapsed)}</Text>
          <Text style={[{ fontFamily: MONO, fontSize: 14, color: C.rule }, recording && remaining <= 60 && warnBox]}>
            {mmss(remaining)} left
          </Text>
        </View>
        <Text style={[{ fontFamily: MONO, fontSize: 13, marginTop: 6, color: C.rule, alignSelf: 'flex-start' }, gpsWarn && warnBox]}>{gpsLine}</Text>
      </View>
      <View style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: 16, paddingBottom: 32, backgroundColor: 'rgba(26,29,25,0.72)' }}>
        {message && <Text style={[{ fontSize: 13, marginBottom: 10 }, warnBox]}>{message}</Text>}
        {hint && <Text style={{ color: C.rule, fontSize: 13, marginBottom: 10 }}>{hint}</Text>}
        {phase === 'finishing' ? (
          <Text style={{ color: C.card, fontSize: 15, textAlign: 'center', paddingVertical: 20 }}>Saving video and GPS track…</Text>
        ) : (
          <Pressable
            onPress={recording ? stop : start}
            disabled={!recording && !canStart}
            style={{
              height: 72, borderRadius: 6, alignItems: 'center', justifyContent: 'center',
              backgroundColor: recording ? C.alert : canStart ? C.cyan : C.inkSoft,
            }}
          >
            <Text style={{ color: C.card, fontSize: 20, fontWeight: '600' }}>{recording ? 'Stop recording' : 'Start recording'}</Text>
          </Pressable>
        )}
        {!recording && phase === 'idle' && (
          <Pressable onPress={onShowSessions} style={{ paddingTop: 14, alignItems: 'center' }}>
            <Text style={{ color: C.rule, fontSize: 14 }}>Recorded sessions</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

function Row({ k, v }) {
  return (
    <View style={[s.row, { justifyContent: 'space-between', paddingVertical: 4 }]}>
      <Text style={s.soft}>{k}</Text>
      <Text style={s.data}>{v}</Text>
    </View>
  );
}

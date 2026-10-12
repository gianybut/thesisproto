import { useEffect, useState } from 'react';
import { Alert, Pressable, ScrollView, Text, View } from 'react-native';
import { useVideoPlayer, VideoView } from 'expo-video';
import { saveVideoToPhotos, shareSessionFile } from '../media';
import { getSession, subscribe } from '../storage';
import { C, s } from '../theme';

const mb = (b) => (b == null ? '—' : `${(b / 1048576).toFixed(1)} MB`);

export default function PreviewScreen({ sessionId, onBack }) {
  const [session, setSession] = useState(() => getSession(sessionId));
  const [busy, setBusy] = useState(null);

  useEffect(() => subscribe(() => setSession(getSession(sessionId))), [sessionId]);

  const player = useVideoPlayer(session?.videoUri ?? null, (p) => { p.muted = true; });

  async function act(label, fn, done) {
    setBusy(label);
    try {
      await fn();
      if (done) Alert.alert(done);
    } catch (e) {
      Alert.alert('Could not finish', e.message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <View style={s.screen}>
      <View style={[s.pad, { paddingTop: 56, borderBottomWidth: 1, borderColor: C.rule }]}>
        <Pressable onPress={onBack}><Text style={[s.body, { color: C.cyan }]}>‹ Sessions</Text></Pressable>
        <Text style={[s.h3, { marginTop: 12 }]}>{session?.roadName || session?.id || 'Session removed'}</Text>
      </View>
      {session && (
        <ScrollView contentContainerStyle={s.pad}>
          {session.videoUri ? (
            <VideoView
              player={player}
              nativeControls
              contentFit="contain"
              fullscreenOptions={{ enable: true }}
              style={{ width: '100%', aspectRatio: 16 / 9, backgroundColor: C.ink }}
            />
          ) : (
            <View style={[s.card, { alignItems: 'center' }]}><Text style={s.soft}>This session has no video.</Text></View>
          )}

          <Text style={[s.label, { marginTop: 20 }]}>Copy off this phone</Text>
          <Text style={[s.soft, { marginTop: 4 }]}>
            The files stay in the app after upload until you delete the session. Copies made here are separate and are not deleted with it.
          </Text>

          {session.videoUri && (
            <>
              <Action
                label={busy === 'photos' ? 'Saving…' : 'Save video to Photos'}
                hint={mb(session.videoBytes)}
                mono
                disabled={!!busy}
                onPress={() => act('photos', () => saveVideoToPhotos(session), 'Saved to Photos.')}
              />
              <Action
                label="Share video…"
                hint="Save to Files, AirDrop, Drive"
                disabled={!!busy}
                onPress={() => act('video', () => shareSessionFile(session, 'video'))}
              />
            </>
          )}
          {session.gpxUri ? (
            <Action
              label="Share GPS track (GPX)…"
              hint={`${session.pointCount ?? 0} pts`}
              mono
              disabled={!!busy}
              onPress={() => act('gpx', () => shareSessionFile(session, 'gpx'))}
            />
          ) : (
            <Text style={[s.soft, { marginTop: 12 }]}>No GPS track was logged for this session.</Text>
          )}
        </ScrollView>
      )}
    </View>
  );
}

function Action({ label, hint, mono, onPress, disabled }) {
  return (
    <Pressable
      style={[s.btn, s.btnGhost, s.row, { justifyContent: 'space-between', marginTop: 10 }, disabled && { opacity: 0.6 }]}
      onPress={onPress}
      disabled={disabled}
    >
      <Text style={s.btnGhostText}>{label}</Text>
      <Text style={mono ? s.data : s.soft}>{hint}</Text>
    </Pressable>
  );
}

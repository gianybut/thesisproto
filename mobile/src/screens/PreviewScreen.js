import { useEffect, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, Text, View } from 'react-native';
import { useVideoPlayer, VideoView } from 'expo-video';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { saveVideoToPhotos, shareSessionFile } from '../media';
import { getSession, subscribe, updateSession } from '../storage';
import { confirmDelete, runNextStep } from '../surveyActions';
import AppBar from '../components/AppBar';
import Button from '../components/Button';
import Disclosure from '../components/Disclosure';
import Facts from '../components/Facts';
import Field from '../components/Field';
import Notice from '../components/Notice';
import PageHeader from '../components/PageHeader';
import StatusLabel, { ProgressBar } from '../components/StatusLabel';
import Icon from '../icons';
import {
  END_REASONS, formatDateTime, formatDuration, formatSize, formatTime, nextStep, surveyNote, surveyStatus, surveyTitle,
} from '../labels';
import { C, R, S, s } from '../theme';

// One survey on this phone: the web's survey page, cut down to what a phone can do with it.
export default function PreviewScreen({ sessionId, onBack }) {
  const insets = useSafeAreaInsets();
  const [session, setSession] = useState(() => getSession(sessionId));
  const [busy, setBusy] = useState(null);
  const [copied, setCopied] = useState(null);
  const [editingName, setEditingName] = useState(false);
  const [roadName, setRoadName] = useState(session?.roadName || '');

  useEffect(() => subscribe(() => setSession(getSession(sessionId))), [sessionId]);

  const player = useVideoPlayer(session?.videoUri ?? null, (p) => { p.muted = true; });

  async function act(label, fn, done) {
    setBusy(label);
    setCopied(null);
    try {
      await fn();
      if (done) setCopied(done);
    } catch (e) {
      Alert.alert('Could not copy the file', e.message);
    } finally {
      setBusy(null);
    }
  }

  if (!session) {
    return (
      <View style={s.screen}>
        <AppBar />
        <View style={s.page}>
          <PageHeader title="Survey deleted" back={{ label: 'Surveys', onPress: onBack }} />
        </View>
      </View>
    );
  }

  const status = surveyStatus(session);
  const step = nextStep(session);
  const note = surveyNote(session);
  const title = surveyTitle(session);
  // The road name travels with the upload, so it can change only before that.
  const canRename = !session.broken && ['recorded', 'failed'].includes(session.status);

  function saveName() {
    updateSession(session.id, { roadName: roadName.trim() });
    setEditingName(false);
  }

  return (
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <AppBar />
      <ScrollView contentContainerStyle={[s.page, { paddingBottom: insets.bottom + S[7] }]} keyboardShouldPersistTaps="handled">
        <PageHeader
          title={title}
          back={{ label: 'Surveys', onPress: onBack }}
          meta={[session.roadName && formatDateTime(session.createdAt), formatDuration(session.durationS), formatSize(session.videoBytes)].filter(Boolean).join(' · ')}
        >
          {canRename && !editingName && (
            <Button
              label={session.roadName ? 'Change road name' : 'Add a road name'}
              icon="pencil"
              variant="quiet"
              onPress={() => setEditingName(true)}
              style={{ marginTop: S[2], marginLeft: -S[3] }}
            />
          )}
        </PageHeader>

        <View style={s.stack}>
          {editingName && (
            <View style={[s.panel, { gap: S[3] }]}>
              <Field
                label="Road name (optional)"
                hint="Sent with the upload. Helps you find this survey later."
                value={roadName}
                onChangeText={setRoadName}
                maxLength={200}
                autoFocus
                returnKeyType="done"
                onSubmitEditing={saveName}
              />
              <View style={s.wrapRow}>
                <Button label="Save road name" onPress={saveName} />
                <Button label="Cancel" variant="quiet" onPress={() => { setRoadName(session.roadName || ''); setEditingName(false); }} />
              </View>
            </View>
          )}

          <View style={{ gap: S[3] }}>
            <StatusLabel status={status} />
            {status.progress != null && <ProgressBar value={status.progress} label={status.text} />}
            {note && <Text style={[s.body, note.danger && { color: C.danger }]}>{note.text}</Text>}
            {session.status === 'uploaded' && session.uploadedAt && (
              <Text style={[s.muted, s.num]}>Uploaded at {formatTime(session.uploadedAt)}. Open the web app to see the damage on the map.</Text>
            )}
            {step && (
              <Button
                label={step.kind === 'upload' && session.status === 'recorded' ? 'Upload this survey' : step.label}
                icon={step.icon}
                variant={step.kind === 'cancel' ? 'secondary' : 'primary'}
                block
                onPress={() => runNextStep(session, step)}
              />
            )}
          </View>

          {session.warnings?.length > 0 && <Notice kind="info">{session.warnings}</Notice>}

          {session.videoUri ? (
            <VideoView
              player={player}
              nativeControls
              contentFit="contain"
              fullscreenOptions={{ enable: true }}
              style={{ width: '100%', aspectRatio: 16 / 9, backgroundColor: C.ink, borderRadius: R.md, overflow: 'hidden' }}
            />
          ) : (
            <View style={[s.panel, { alignItems: 'flex-start', gap: S[2], backgroundColor: C.subtle, borderColor: C.subtle }]}>
              <Icon name="video" color={C.muted} />
              <Text style={[s.body, { color: C.muted }]}>This survey has no video. Delete it, then record the road again.</Text>
            </View>
          )}

          {(session.videoUri || session.gpxUri) && (
            <View style={[s.panel, { gap: S[3] }]}>
              <Text style={s.panelTitle} accessibilityRole="header">Copy off this phone</Text>
              <Text style={s.fieldHint}>
                The files stay in the app, even after upload, until you delete the survey. Copies made here are separate and stay when you delete it.
              </Text>
              {copied && <Notice kind="success">{copied}</Notice>}
              {session.videoUri && (
                <>
                  <Button
                    label={busy === 'photos' ? 'Saving to Photos…' : 'Save video to Photos'}
                    icon="download"
                    block
                    disabled={!!busy}
                    onPress={() => act('photos', () => saveVideoToPhotos(session), 'Saved the video to Photos.')}
                  />
                  <Button label="Share video" icon="share" block disabled={!!busy} onPress={() => act('video', () => shareSessionFile(session, 'video'))} />
                </>
              )}
              {session.gpxUri ? (
                <Button label="Share GPS track (GPX)" icon="route" block disabled={!!busy} onPress={() => act('gpx', () => shareSessionFile(session, 'gpx'))} />
              ) : (
                <Text style={s.fieldHint}>No GPS track was logged for this survey. Place it by hand on the web app after upload.</Text>
              )}
            </View>
          )}

          <Disclosure title="Technical details">
            <Facts rows={[
              ['Recorded', formatDateTime(session.createdAt)],
              ['How it ended', session.endReason ? END_REASONS[session.endReason] || session.endReason : null],
              ['GPS points', session.pointCount != null ? String(session.pointCount) : null],
              ['GPS rate', session.achievedHz ? `${session.achievedHz.toFixed(2)} per second` : null],
              ['GPS gaps', session.gaps ? (session.gaps.length ? `${session.gaps.length}, longest ${Math.max(...session.gaps.map((g) => g.seconds))} s` : 'None') : null],
              ['Time offset', session.timeOffsetS != null ? `${session.timeOffsetS.toFixed(2)} s` : null],
              ['Video file', session.videoExt ? `.${session.videoExt}` : null],
              ['Web app survey', session.serverVideoId != null ? `#${session.serverVideoId}` : null],
            ]}
            />
            <Text style={s.code} selectable>{session.id}</Text>
          </Disclosure>

          {session.status !== 'uploading' && session.status !== 'recording' && (
            <Button label="Delete survey" icon="trash" variant="dangerQuiet" onPress={() => confirmDelete(session, onBack)} style={{ marginLeft: -S[3] }} />
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

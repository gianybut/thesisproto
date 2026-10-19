import { useEffect, useState } from 'react';
import { FlatList, Image, Pressable, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAccount } from '../account';
import { ensureThumbnail } from '../media';
import { checkNow } from '../serverStatus';
import { getSessions, subscribe } from '../storage';
import { confirmDelete, confirmReanalyse, confirmReupload, runNextStep } from '../surveyActions';
import {
  describeWait, getSettings, onSettings, run, setWifiOnly,
} from '../uploadQueue';
import AppBar from '../components/AppBar';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import Notice from '../components/Notice';
import PageHeader from '../components/PageHeader';
import { ActionMenu } from '../components/Sheet';
import StatusLabel, { ProgressBar } from '../components/StatusLabel';
import Icon from '../icons';
import {
  formatDateTime, formatDuration, formatSize, nextStep, surveyNote, surveyStatus, surveyTitle,
} from '../labels';
import { C, F, R, S, T, s } from '../theme';

export default function SessionsScreen({ onBack, onPreview }) {
  const insets = useSafeAreaInsets();
  const [sessions, setSessions] = useState(getSessions());
  const [settings, setSettingsState] = useState(getSettings());
  const [wait, setWait] = useState(null);
  const [menuFor, setMenuFor] = useState(null);
  const { signedIn, signIn } = useAccount();

  useEffect(() => subscribe(setSessions), []);
  useEffect(() => onSettings(setSettingsState), []);

  const pending = sessions.some((x) => x.status === 'queued');
  useEffect(() => {
    let alive = true;
    const check = () => describeWait().then((w) => alive && setWait(w));
    check();
    const t = setInterval(check, 5000);
    return () => { alive = false; clearInterval(t); };
  }, [settings.wifiOnly, pending]);

  const toUpload = sessions.filter((x) => !x.broken && ['recorded', 'queued', 'uploading', 'failed'].includes(x.status)).length;
  const meta = sessions.length
    ? `${sessions.length} ${sessions.length === 1 ? 'survey' : 'surveys'}${toUpload ? ` · ${toUpload} to upload` : ''}`
    : null;

  const header = (
    <>
      <PageHeader title="Surveys on this phone" back={{ label: 'Camera', onPress: onBack }} meta={meta} />
      {!signedIn && toUpload > 0 && (
        <Notice
          kind="info"
          style={{ marginBottom: S[5] }}
          action={<Button label="Sign in" icon="user-circle" variant="quiet" onPress={signIn} style={{ marginLeft: -S[3] }} />}
        >
          You are signed out. These surveys stay on this phone and upload after you sign in.
        </Notice>
      )}
      {signedIn && pending && wait && (
        <Notice
          kind="info"
          style={{ marginBottom: S[5] }}
          action={wait.kind === 'wifi'
            ? <Button label="Upload over mobile data" icon="wifi" variant="quiet" onPress={() => setWifiOnly(false)} style={{ marginLeft: -S[3] }} />
            : null}
        >
          {wait.text}
        </Notice>
      )}
    </>
  );

  const menuItem = menuFor && sessions.find((x) => x.id === menuFor);

  return (
    <View style={s.screen}>
      <AppBar />
      <FlatList
        data={sessions}
        keyExtractor={(x) => x.id}
        renderItem={({ item, index }) => (
          <SurveyRow item={item} first={index === 0} onOpen={() => onPreview(item.id)} onMore={() => setMenuFor(item.id)} />
        )}
        ListHeaderComponent={header}
        ListEmptyComponent={(
          <EmptyState
            icon="video"
            title="No surveys on this phone yet"
            action={<Button label="Record a survey" icon="record" iconColor={C.danger} onPress={onBack} />}
          >
            Record a road from the camera. It is kept here until you upload it.
          </EmptyState>
        )}
        contentContainerStyle={[s.page, { paddingBottom: insets.bottom + S[7] }]}
        onRefresh={() => { run(); checkNow(); }}
        refreshing={false}
      />
      <ActionMenu
        visible={!!menuItem}
        onClose={() => setMenuFor(null)}
        title={menuItem ? surveyTitle(menuItem) : ''}
        items={menuItem ? [
          { label: menuItem.videoUri ? 'Play and copy off the phone' : 'See details', icon: menuItem.videoUri ? 'play' : 'info-circle', onPress: () => onPreview(menuItem.id) },
          // Testing a changed model or setting: rerun on the server, or send the video again.
          menuItem.status === 'uploaded' && menuItem.serverVideoId != null && ['completed', 'failed'].includes(menuItem.serverStatus)
            && { label: 'Analyse again on the server', icon: 'refresh', onPress: () => confirmReanalyse(menuItem) },
          menuItem.status === 'uploaded' && menuItem.videoUri && !menuItem.broken
            && { label: 'Upload again as a new survey', icon: 'upload', onPress: () => confirmReupload(menuItem) },
          menuItem.status !== 'uploading' && menuItem.status !== 'recording'
            && { label: 'Delete survey', icon: 'trash', danger: true, onPress: () => confirmDelete(menuItem) },
        ] : []}
      />
    </View>
  );
}

function SurveyRow({ item, first, onOpen, onMore }) {
  const status = surveyStatus(item);
  const step = nextStep(item);
  const note = surveyNote(item);
  const title = surveyTitle(item);
  const facts = [
    item.roadName && formatDateTime(item.createdAt),
    formatDuration(item.durationS),
    formatSize(item.videoBytes),
    !item.broken && item.status !== 'recording' && !item.gpxUri && 'No GPS track',
  ].filter(Boolean).join(' · ');

  return (
    <View style={{ paddingVertical: S[4], gap: S[3], borderTopWidth: first ? 0 : 1, borderTopColor: C.border }}>
      <Pressable
        onPress={onOpen}
        accessibilityRole="button"
        accessibilityLabel={`${title}, ${status.text}`}
        style={({ pressed }) => [{ flexDirection: 'row', gap: S[3], alignItems: 'flex-start' }, pressed && { opacity: 0.7 }]}
      >
        <Thumb item={item} />
        <View style={{ flex: 1, gap: S[1] }}>
          <Text style={{ fontFamily: F.semibold, ...T.base, color: C.ink }} numberOfLines={2}>{title}</Text>
          <Text style={[s.muted, s.num]}>{facts}</Text>
          <StatusLabel status={status} style={{ marginTop: S[1] }} />
        </View>
      </Pressable>
      {status.progress != null && <ProgressBar value={status.progress} label={status.text} />}
      {note && <Text style={[s.small, note.danger && { color: C.danger }]}>{note.text}</Text>}
      <View style={[s.row, { justifyContent: 'space-between' }]}>
        {step ? (
          <Button label={step.label} icon={step.icon} variant={step.kind === 'cancel' ? 'quiet' : 'secondary'} onPress={() => runNextStep(item, step)} />
        ) : <View />}
        <Button iconOnly icon="dots" variant="quiet" accessibilityLabel={`More actions for ${title}`} onPress={onMore} />
      </View>
    </View>
  );
}

const THUMB_W = 96;
const THUMB_H = 54;

function Thumb({ item }) {
  useEffect(() => { ensureThumbnail(item); }, [item]);
  const box = { width: THUMB_W, height: THUMB_H, borderRadius: R.sm, overflow: 'hidden' };
  if (!item.videoUri) {
    return (
      <View style={[box, { alignItems: 'center', justifyContent: 'center', backgroundColor: C.subtle, borderWidth: 1, borderColor: C.border }]}>
        <Icon name="video" color={C.muted} />
      </View>
    );
  }
  return item.thumbUri
    ? <Image source={{ uri: item.thumbUri }} style={[box, { backgroundColor: C.ink }]} resizeMode="cover" accessibilityIgnoresInvertColors />
    : <View style={[box, { backgroundColor: C.subtle }]} />;
}

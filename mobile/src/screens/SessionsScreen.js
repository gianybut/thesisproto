import { useEffect, useState } from 'react';
import { Alert, FlatList, Image, Pressable, Switch, Text, View } from 'react-native';
import { getUser } from '../auth';
import { ensureThumbnail } from '../media';
import { deleteSession, getSessions, subscribe } from '../storage';
import {
  cancelUpload, describeWait, enqueue, getSettings, onSettings, run, setWifiOnly,
} from '../uploadQueue';
import { C, s } from '../theme';

const STATUS_LABEL = {
  recording: 'Recording',
  recorded: 'Recorded',
  queued: 'Queued',
  uploading: 'Uploading',
  uploaded: 'Uploaded',
  failed: 'Failed',
};

const mb = (b) => (b == null ? '—' : `${(b / 1048576).toFixed(1)} MB`);
const mmss = (sec) => (sec == null ? '—' : `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, '0')}`);
const when = (ms) => new Date(ms).toLocaleString();

export default function SessionsScreen({ onBack, onLogout, onPreview }) {
  const [sessions, setSessions] = useState(getSessions());
  const [settings, setSettingsState] = useState(getSettings());
  const [wait, setWait] = useState(null);

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

  function confirmDelete(item) {
    const unsent = item.status !== 'uploaded' && !item.broken;
    Alert.alert(
      'Delete this session?',
      unsent
        ? 'This survey has not been uploaded. The video and GPS track will be gone for good.'
        : 'The video and GPS track will be removed from this phone.',
      [
        { text: 'Keep', style: 'cancel' },
        {
          text: 'Delete', style: 'destructive',
          onPress: () => { cancelUpload(item.id); deleteSession(item.id); },
        },
      ],
    );
  }

  const renderItem = ({ item }) => (
    <View style={[s.card, { marginBottom: 10 }]}>
      <View style={[s.row, { alignItems: 'flex-start', gap: 12 }]}>
        <Thumb item={item} onPress={() => onPreview(item.id)} />
        <View style={{ flex: 1 }}>
          <View style={[s.row, { justifyContent: 'space-between', gap: 8 }]}>
            <Text style={[s.data, { flexShrink: 1 }]}>{item.roadName || item.id}</Text>
            <Text style={[s.label, item.status === 'failed' && { color: C.alert }]}>{STATUS_LABEL[item.status] || item.status}</Text>
          </View>
          <Text style={[s.soft, { marginTop: 4 }]}>{when(item.createdAt)}</Text>
          <Text style={[s.data, { marginTop: 2 }]}>{mmss(item.durationS)} · {mb(item.videoBytes)} · {item.pointCount ?? 0} pts</Text>
        </View>
      </View>
      {item.status === 'uploading' && (
        <View style={{ height: 4, backgroundColor: C.rule, marginTop: 10 }}>
          <View style={{ height: 4, width: `${Math.round((item.progress || 0) * 100)}%`, backgroundColor: C.cyan }} />
        </View>
      )}
      {item.status === 'uploaded' && item.serverVideoId != null && (
        <Text style={[s.soft, { marginTop: 6 }]}>Server video <Text style={s.data}>#{item.serverVideoId}</Text></Text>
      )}
      {(item.warnings || []).map((w) => <Text key={w} style={[s.soft, { marginTop: 6 }]}>{w}</Text>)}
      {item.lastError && item.status !== 'uploaded' && (
        <Text style={[s.alert, { marginTop: 6 }]}>
          {item.lastError}{item.status === 'queued' && item.attempts ? ` Retrying automatically (attempt ${item.attempts + 1}).` : ''}
        </Text>
      )}
      <View style={[s.row, { marginTop: 12, gap: 8, flexWrap: 'wrap' }]}>
        {item.videoUri && <Btn label="View" onPress={() => onPreview(item.id)} />}
        {item.status === 'recorded' && <Btn label="Upload" onPress={() => enqueue(item.id)} />}
        {item.status === 'failed' && !item.broken && item.videoUri && <Btn label="Retry upload" onPress={() => enqueue(item.id)} />}
        {item.status === 'queued' && <Btn label="Try now" onPress={() => enqueue(item.id)} />}
        {item.status === 'uploading' && <Btn label="Cancel upload" onPress={() => cancelUpload(item.id)} />}
        {item.status !== 'uploading' && item.status !== 'recording' && <Btn label="Delete" onPress={() => confirmDelete(item)} />}
      </View>
    </View>
  );

  return (
    <View style={s.screen}>
      <View style={[s.pad, { paddingTop: 56, borderBottomWidth: 1, borderColor: C.rule }]}>
        <View style={[s.row, { justifyContent: 'space-between' }]}>
          <Pressable onPress={onBack}><Text style={[s.body, { color: C.cyan }]}>‹ Camera</Text></Pressable>
          <Pressable onPress={onLogout}><Text style={s.soft}>Log out {getUser()?.username}</Text></Pressable>
        </View>
        <Text style={[s.h1, { marginTop: 12 }]}>Sessions</Text>
        <View style={[s.row, { justifyContent: 'space-between' }]}>
          <Text style={s.body}>Upload on Wi-Fi only</Text>
          <Switch value={settings.wifiOnly} onValueChange={setWifiOnly} trackColor={{ true: C.cyan, false: C.rule }} />
        </View>
        {pending && wait && <Text style={[s.soft, { marginTop: 8 }]}>{wait}</Text>}
      </View>
      <FlatList
        data={sessions}
        keyExtractor={(x) => x.id}
        renderItem={renderItem}
        contentContainerStyle={s.pad}
        onRefresh={run}
        refreshing={false}
        ListEmptyComponent={<Text style={s.soft}>No recordings yet.</Text>}
      />
    </View>
  );
}

function Btn({ label, onPress }) {
  return (
    <Pressable style={[s.btn, s.btnGhost, { paddingVertical: 8 }]} onPress={onPress}>
      <Text style={[s.btnGhostText, { fontSize: 14 }]}>{label}</Text>
    </Pressable>
  );
}

const THUMB_W = 96;
const THUMB_H = 54;

function Thumb({ item, onPress }) {
  useEffect(() => { ensureThumbnail(item); }, [item]);
  const box = { width: THUMB_W, height: THUMB_H, borderRadius: 4, borderWidth: 1, borderColor: C.rule };
  if (!item.videoUri) {
    return (
      <View style={[box, { alignItems: 'center', justifyContent: 'center', backgroundColor: C.paper }]}>
        <Text style={s.label}>No video</Text>
      </View>
    );
  }
  return (
    <Pressable onPress={onPress}>
      {item.thumbUri
        ? <Image source={{ uri: item.thumbUri }} style={[box, { backgroundColor: C.ink }]} resizeMode="cover" />
        : <View style={[box, { backgroundColor: C.ink }]} />}
    </Pressable>
  );
}

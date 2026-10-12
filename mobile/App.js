import { useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { loadAuth, logout, onUnauthorized, verifyToken } from './src/auth';
import { recoverAfterRestart } from './src/storage';
import { startQueue, stopQueue } from './src/uploadQueue';
import CaptureScreen from './src/screens/CaptureScreen';
import LoginScreen from './src/screens/LoginScreen';
import PreviewScreen from './src/screens/PreviewScreen';
import SessionsScreen from './src/screens/SessionsScreen';
import { s } from './src/theme';

export default function App() {
  const [ready, setReady] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [screen, setScreen] = useState('capture'); // capture | sessions | preview
  const [previewId, setPreviewId] = useState(null);
  const [notice, setNotice] = useState(null);

  useEffect(() => {
    (async () => {
      recoverAfterRestart();
      const { token } = await loadAuth();
      const ok = token ? await verifyToken() : false;
      if (token && !ok) {
        await logout();
        setNotice('Your session ended. Log in again.');
      }
      setLoggedIn(ok);
      setReady(true);
    })();
    return onUnauthorized(() => {
      setNotice('Your session ended. Log in again. Recordings on this phone are kept and will upload after you log in.');
      setLoggedIn(false);
    });
  }, []);

  // The queue runs only while logged in; a 401 stops it via onUnauthorized.
  useEffect(() => {
    if (!loggedIn) return undefined;
    startQueue();
    return stopQueue;
  }, [loggedIn]);

  if (!ready) {
    return <View style={[s.screen, s.pad]}><Text style={s.soft}>Loading…</Text></View>;
  }

  let body;
  if (!loggedIn) {
    body = <LoginScreen notice={notice} onLoggedIn={() => { setNotice(null); setLoggedIn(true); }} />;
  } else if (screen === 'preview') {
    body = <PreviewScreen sessionId={previewId} onBack={() => setScreen('sessions')} />;
  } else if (screen === 'sessions') {
    body = (
      <SessionsScreen
        onBack={() => setScreen('capture')}
        onPreview={(id) => { setPreviewId(id); setScreen('preview'); }}
        onLogout={async () => { await logout(); setLoggedIn(false); }}
      />
    );
  } else {
    body = <CaptureScreen onShowSessions={() => setScreen('sessions')} />;
  }

  return (
    <>
      <StatusBar style={loggedIn && screen === 'capture' ? 'light' : 'dark'} />
      {body}
    </>
  );
}

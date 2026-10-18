import { useEffect, useState } from 'react';
import { BackHandler, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import { PublicSans_400Regular } from '@expo-google-fonts/public-sans/400Regular';
import { PublicSans_600SemiBold } from '@expo-google-fonts/public-sans/600SemiBold';
import { PublicSans_700Bold } from '@expo-google-fonts/public-sans/700Bold';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { loadAuth, logout, onUnauthorized, verifyToken } from './src/auth';
import { startStatusPolling, stopStatusPolling } from './src/serverStatus';
import { recoverAfterRestart } from './src/storage';
import { startQueue, stopQueue } from './src/uploadQueue';
import CaptureScreen from './src/screens/CaptureScreen';
import LoginScreen from './src/screens/LoginScreen';
import PreviewScreen from './src/screens/PreviewScreen';
import SessionsScreen from './src/screens/SessionsScreen';
import { C } from './src/theme';

export default function App() {
  const [ready, setReady] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [screen, setScreen] = useState('capture'); // capture | sessions | preview
  const [previewId, setPreviewId] = useState(null);
  const [notice, setNotice] = useState(null);
  // A font that fails to load falls back to the system face rather than blocking the app.
  const [fontsLoaded, fontError] = useFonts({ PublicSans_400Regular, PublicSans_600SemiBold, PublicSans_700Bold });

  useEffect(() => {
    (async () => {
      recoverAfterRestart();
      const { token } = await loadAuth();
      const ok = token ? await verifyToken() : false;
      if (token && !ok) {
        await logout();
        setNotice('You were signed out. Sign in again.');
      }
      setLoggedIn(ok);
      setReady(true);
    })();
    return onUnauthorized(() => {
      setNotice('You were signed out. Sign in again. Surveys on this phone are kept and upload after you sign in.');
      setLoggedIn(false);
    });
  }, []);

  // The queue and the analysis check run only while signed in; a 401 stops both via onUnauthorized.
  useEffect(() => {
    if (!loggedIn) return undefined;
    startQueue();
    startStatusPolling();
    return () => { stopQueue(); stopStatusPolling(); };
  }, [loggedIn]);

  // Android back button: survey -> list -> camera, then the system default (leave the app).
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (!loggedIn) return false;
      if (screen === 'preview') { setScreen('sessions'); return true; }
      if (screen === 'sessions') { setScreen('capture'); return true; }
      return false;
    });
    return () => sub.remove();
  }, [loggedIn, screen]);

  const signOut = async () => {
    await logout();
    setScreen('capture');
    setLoggedIn(false);
  };

  // White, not a spinner (design.md §12): this lasts as long as reading the token and fonts.
  if (!ready || (!fontsLoaded && !fontError)) {
    return <View style={{ flex: 1, backgroundColor: C.bg }} />;
  }

  let body;
  if (!loggedIn) {
    body = <LoginScreen notice={notice} onLoggedIn={() => { setNotice(null); setLoggedIn(true); }} />;
  } else if (screen === 'preview') {
    body = <PreviewScreen sessionId={previewId} onBack={() => setScreen('sessions')} onSignOut={signOut} />;
  } else if (screen === 'sessions') {
    body = (
      <SessionsScreen
        onBack={() => setScreen('capture')}
        onPreview={(id) => { setPreviewId(id); setScreen('preview'); }}
        onSignOut={signOut}
      />
    );
  } else {
    body = <CaptureScreen onShowSessions={() => setScreen('sessions')} onSignOut={signOut} />;
  }

  return (
    <SafeAreaProvider>
      {/* Light text on the navy bar and over the camera; dark on the white sign-in page. */}
      <StatusBar style={loggedIn ? 'light' : 'dark'} />
      {body}
    </SafeAreaProvider>
  );
}

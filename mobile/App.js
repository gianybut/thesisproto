import { useEffect, useMemo, useState } from 'react';
import { BackHandler, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import { PublicSans_400Regular } from '@expo-google-fonts/public-sans/400Regular';
import { PublicSans_600SemiBold } from '@expo-google-fonts/public-sans/600SemiBold';
import { PublicSans_700Bold } from '@expo-google-fonts/public-sans/700Bold';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AccountContext } from './src/account';
import { hasSavedServer, loadAuth, logout, onUnauthorized, verifyToken } from './src/auth';
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
  const [screen, setScreen] = useState('capture'); // capture | sessions | preview | login
  const [previewId, setPreviewId] = useState(null);
  const [notice, setNotice] = useState(null);
  // A font that fails to load falls back to the system face rather than blocking the app.
  const [fontsLoaded, fontError] = useFonts({ PublicSans_400Regular, PublicSans_600SemiBold, PublicSans_700Bold });

  // An expired sign-in does not lock the app (see src/account.js): the screen stays where it
  // is, uploads wait, and the survey list offers "Sign in".
  useEffect(() => {
    (async () => {
      recoverAfterRestart();
      const { token } = await loadAuth();
      const ok = token ? await verifyToken() : false;
      if (token && !ok) {
        await logout();
        setNotice(SIGNED_OUT);
      }
      setLoggedIn(ok);
      setReady(true);
    })();
    return onUnauthorized(() => {
      setNotice(SIGNED_OUT);
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

  // Where "Back" goes from each screen; also Android's back button. null = leave the app.
  const back = { preview: 'sessions', sessions: 'capture', login: 'capture' }[screen] ?? null;
  // The first sign-in on a phone is required, because it is where the server address is set.
  const firstRun = !loggedIn && !hasSavedServer();

  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (firstRun || !back) return false;
      setScreen(back);
      return true;
    });
    return () => sub.remove();
  }, [firstRun, back]);

  const account = useMemo(() => ({
    signedIn: loggedIn,
    signIn: () => setScreen('login'),
    signOut: async () => {
      await logout();
      setNotice(null);
      setLoggedIn(false);
      setScreen('login');
    },
  }), [loggedIn]);

  // White, not a spinner (design.md §12): this lasts as long as reading the token and fonts.
  if (!ready || (!fontsLoaded && !fontError)) {
    return <View style={{ flex: 1, backgroundColor: C.bg }} />;
  }

  const onSignInPage = firstRun || (screen === 'login' && !loggedIn);
  let body;
  if (onSignInPage) {
    body = (
      <LoginScreen
        notice={notice}
        onLoggedIn={() => { setNotice(null); setLoggedIn(true); setScreen('capture'); }}
        onCancel={firstRun ? null : () => setScreen('capture')}
      />
    );
  } else if (screen === 'preview') {
    body = <PreviewScreen sessionId={previewId} onBack={() => setScreen('sessions')} />;
  } else if (screen === 'sessions') {
    body = <SessionsScreen onBack={() => setScreen('capture')} onPreview={(id) => { setPreviewId(id); setScreen('preview'); }} />;
  } else {
    body = <CaptureScreen onShowSessions={() => setScreen('sessions')} />;
  }

  return (
    <SafeAreaProvider>
      <AccountContext.Provider value={account}>
        {/* Light text on the navy bar and over the camera; dark on the white sign-in page. */}
        <StatusBar style={onSignInPage ? 'dark' : 'light'} />
        {body}
      </AccountContext.Provider>
    </SafeAreaProvider>
  );
}

const SIGNED_OUT = 'You were signed out. You can keep recording; surveys on this phone upload after you sign in again.';

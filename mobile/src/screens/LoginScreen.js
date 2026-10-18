import { useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getServerUrl, hasSavedServer, login, normalizeServerUrl, setServerUrl } from '../auth';
import Button from '../components/Button';
import Field from '../components/Field';
import Logo from '../components/Logo';
import Notice from '../components/Notice';
import { C, F, S, T, s } from '../theme';

// The web sign-in page (frontend/src/pages/LoginPage.jsx) plus the server address, which a
// phone has to be told. Once an address has been used it folds into one line with "Change".
export default function LoginScreen({ onLoggedIn, notice }) {
  const insets = useSafeAreaInsets();
  const [server, setServer] = useState(getServerUrl());
  const [editServer, setEditServer] = useState(!hasSavedServer());
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const passwordRef = useRef(null);

  async function submit() {
    setError(null);
    const missing = {};
    if (!normalizeServerUrl(server)) missing.server = 'Enter the server address, for example http://192.168.1.10:5000';
    if (!username.trim()) missing.username = 'Enter your username';
    if (!password) missing.password = 'Enter your password';
    setFieldErrors(missing);
    if (missing.server) setEditServer(true);
    if (Object.keys(missing).length) return;

    setBusy(true);
    try {
      await setServerUrl(server);
      setServer(getServerUrl());
      const user = await login(username.trim(), password);
      onLoggedIn(user);
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView
        contentContainerStyle={[s.page, { paddingTop: insets.top + S[7], paddingBottom: insets.bottom + S[7] }]}
        keyboardShouldPersistTaps="handled"
      >
        <View style={{ alignItems: 'center', gap: S[2], marginBottom: S[5] }}>
          <Logo width={100} />
          <Text style={{ fontFamily: F.bold, ...T.xl, color: C.ink, marginTop: S[2] }} accessibilityRole="header">OcuLubak</Text>
          <Text style={[s.body, { color: C.muted, textAlign: 'center' }]}>
            Record road surveys and send them for damage detection.
          </Text>
        </View>

        <View style={s.stack}>
          {notice && !error && <Notice kind="info">{notice}</Notice>}
          {error && <Notice kind="error">{error}</Notice>}

          {editServer ? (
            <Field
              label="Server address"
              hint="The computer running OcuLubak, on the same Wi-Fi as this phone"
              error={fieldErrors.server}
              value={server}
              onChangeText={setServer}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
              returnKeyType="next"
              placeholder="http://192.168.1.10:5000"
            />
          ) : (
            <View style={{ gap: S[1] }}>
              <Text style={s.fieldLabel}>Server address</Text>
              <View style={[s.row, { justifyContent: 'space-between', gap: S[3] }]}>
                <Text style={[s.body, s.num, { flexShrink: 1 }]} numberOfLines={1}>{server}</Text>
                <Button label="Change" variant="quiet" accessibilityLabel="Change server address" onPress={() => setEditServer(true)} />
              </View>
            </View>
          )}

          <Field
            label="Username"
            error={fieldErrors.username}
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete="username"
            textContentType="username"
            returnKeyType="next"
            onSubmitEditing={() => passwordRef.current?.focus()}
          />
          <Field
            ref={passwordRef}
            label="Password"
            error={fieldErrors.password}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoComplete="current-password"
            textContentType="password"
            returnKeyType="go"
            onSubmitEditing={submit}
          />

          <Button label={busy ? 'Signing in…' : 'Sign in'} variant="primary" block disabled={busy} onPress={submit} />
          <Text style={[s.muted, { textAlign: 'center' }]}>Accounts are set up by your system administrator.</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

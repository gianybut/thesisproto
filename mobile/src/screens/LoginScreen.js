import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput } from 'react-native';
import { getServerUrl, login, setServerUrl } from '../auth';
import { C, s } from '../theme';

export default function LoginScreen({ onLoggedIn, notice }) {
  const [server, setServer] = useState(getServerUrl());
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await setServerUrl(server);
      const user = await login(username.trim(), password);
      onLoggedIn(user);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={[s.pad, { paddingTop: 72 }]} keyboardShouldPersistTaps="handled">
        <Text style={s.label}>Bantay Kalsada</Text>
        <Text style={s.h1}>Survey capture</Text>
        <Text style={[s.soft, { marginBottom: 24 }]}>
          Records road video and GPS together, then uploads both to the web system for detection.
        </Text>
        {notice && <Text style={[s.alert, { marginBottom: 16 }]}>{notice}</Text>}

        <Text style={s.label}>Server address</Text>
        <TextInput
          style={[s.input, { fontFamily: Platform.select({ ios: 'Menlo', default: 'monospace' }) }]}
          value={server} onChangeText={setServer}
          autoCapitalize="none" autoCorrect={false} keyboardType="url"
          placeholder="http://192.168.1.10:5000" placeholderTextColor={C.inkSoft}
        />
        <Text style={s.label}>Username</Text>
        <TextInput style={s.input} value={username} onChangeText={setUsername} autoCapitalize="none" autoCorrect={false} />
        <Text style={s.label}>Password</Text>
        <TextInput style={s.input} value={password} onChangeText={setPassword} secureTextEntry onSubmitEditing={submit} />

        {error && <Text style={[s.alert, { marginBottom: 12 }]}>{error}</Text>}
        <Pressable style={[s.btn, s.btnPrimary, busy && { opacity: 0.6 }]} onPress={submit} disabled={busy || !username || !password}>
          <Text style={s.btnPrimaryText}>{busy ? 'Logging in…' : 'Log in'}</Text>
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

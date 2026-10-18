import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getSession } from '../storage';
import AppBar from '../components/AppBar';
import Button from '../components/Button';
import Facts from '../components/Facts';
import Field from '../components/Field';
import Notice from '../components/Notice';
import PageHeader from '../components/PageHeader';
import { formatDuration, formatSize } from '../labels';
import { S, s } from '../theme';

/**
 * Straight after a recording stops: what was saved, an optional road name, and one main action.
 * onDone({ upload, roadName }) hands back to the camera screen.
 */
export default function ReviewScreen({ sessionId, onDone }) {
  const insets = useSafeAreaInsets();
  const [roadName, setRoadName] = useState('');
  const sess = getSession(sessionId);
  const saved = sess?.status === 'recorded';

  return (
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <AppBar />
      <ScrollView contentContainerStyle={[s.page, { paddingBottom: insets.bottom + S[7] }]} keyboardShouldPersistTaps="handled">
        <PageHeader title={saved ? 'Survey recorded' : 'The survey was not saved'} />
        <View style={s.stack}>
          {!saved && sess?.lastError && <Notice kind="error">{sess.lastError}</Notice>}

          {sess && saved && (
            <View style={s.panel}>
              <Facts rows={[
                ['Length', formatDuration(sess.durationS)],
                ['Size', formatSize(sess.videoBytes)],
                ['GPS track', sess.pointCount ? `${sess.pointCount} points` : 'None'],
              ]}
              />
            </View>
          )}

          {sess?.warnings?.length > 0 && <Notice kind="info" title="Check before uploading">{sess.warnings}</Notice>}

          {saved ? (
            <>
              <Field
                label="Road name (optional)"
                hint="Helps you find this survey later"
                value={roadName}
                onChangeText={setRoadName}
                maxLength={200}
                placeholder="e.g. Mendez–Tagaytay Road"
                returnKeyType="done"
              />
              <View style={{ gap: S[3] }}>
                <Button label="Upload this survey" icon="upload" variant="primary" block onPress={() => onDone({ upload: true, roadName })} />
                <Button label="Keep on this phone for now" variant="quiet" block onPress={() => onDone({ upload: false, roadName })} />
              </View>
            </>
          ) : (
            <Button label="Back to the camera" variant="primary" block onPress={() => onDone({ upload: false, roadName: '' })} />
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

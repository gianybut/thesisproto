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

const sum = (list, key) => list.reduce((t, x) => t + (x[key] || 0), 0);

/**
 * Straight after a recording stops: what was saved, an optional road name, and one main action.
 * A long recording comes as several clips (parts); the road name and the upload apply to all.
 * onDone({ upload, roadName }) hands back to the camera screen.
 */
export default function ReviewScreen({ sessionIds, onDone }) {
  const insets = useSafeAreaInsets();
  const [roadName, setRoadName] = useState('');
  const clips = sessionIds.map(getSession).filter(Boolean);
  const saved = clips.filter((x) => x.status === 'recorded');
  const many = clips.length > 1;
  const label = (x) => (many ? `Part ${x.part}: ` : '');
  const errors = clips.filter((x) => x.status !== 'recorded' && x.lastError).map((x) => `${label(x)}${x.lastError}`);
  const warnings = clips.flatMap((x) => (x.warnings || []).map((w) => `${label(x)}${w}`));

  let title = 'The survey was not saved';
  if (saved.length) title = many ? `Survey recorded in ${clips.length} parts` : 'Survey recorded';

  return (
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <AppBar />
      <ScrollView contentContainerStyle={[s.page, { paddingBottom: insets.bottom + S[7] }]} keyboardShouldPersistTaps="handled">
        <PageHeader title={title} />
        <View style={s.stack}>
          {errors.length > 0 && <Notice kind="error">{errors}</Notice>}

          {saved.length > 0 && (
            <View style={s.panel}>
              <Facts rows={[
                many && ['Parts', saved.length === clips.length ? String(clips.length) : `${saved.length} of ${clips.length} saved`],
                ['Length', formatDuration(sum(saved, 'durationS'))],
                ['Size', formatSize(sum(saved, 'videoBytes'))],
                ['GPS track', sum(saved, 'pointCount') ? `${sum(saved, 'pointCount')} points` : 'None'],
              ].filter(Boolean)}
              />
            </View>
          )}

          {warnings.length > 0 && <Notice kind="info" title="Check before uploading">{warnings}</Notice>}

          {saved.length > 0 ? (
            <>
              <Field
                label="Road name (optional)"
                hint={many ? 'Given to every part. Helps you find this survey later' : 'Helps you find this survey later'}
                value={roadName}
                onChangeText={setRoadName}
                maxLength={200}
                placeholder="e.g. Mendez–Tagaytay Road"
                returnKeyType="done"
              />
              <View style={{ gap: S[3] }}>
                <Button
                  label={saved.length > 1 ? `Upload all ${saved.length} parts` : 'Upload this survey'}
                  icon="upload"
                  variant="primary"
                  block
                  onPress={() => onDone({ upload: true, roadName })}
                />
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

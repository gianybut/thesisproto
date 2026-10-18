import { Text, TextInput, View } from 'react-native';
import { C, S, s } from '../theme';

/**
 * Label, hint, error, input: the web's .field. An error puts a red bar on the left and is read
 * before the input, as in the GOV.UK pattern the web uses.
 */
export default function Field({ ref, label, hint, error, style, inputStyle, ...input }) {
  return (
    <View style={[{ gap: S[1] }, error && { paddingLeft: S[3], borderLeftWidth: 3, borderLeftColor: C.danger }, style]}>
      <Text style={s.fieldLabel}>{label}</Text>
      {hint ? <Text style={s.fieldHint}>{hint}</Text> : null}
      {error ? <Text style={s.fieldError} accessibilityLiveRegion="polite">{error}</Text> : null}
      <TextInput
        ref={ref}
        accessibilityLabel={label}
        accessibilityHint={error || hint}
        placeholderTextColor={C.muted}
        style={[s.input, error && { borderColor: C.danger }, inputStyle]}
        {...input}
      />
    </View>
  );
}

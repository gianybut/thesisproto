import { Text, View } from 'react-native';
import Icon from '../icons';
import { C, F, R, S, T } from '../theme';

const KINDS = {
  info: { icon: 'info-circle', bg: C.subtle, border: C.border, fg: C.ink },
  success: { icon: 'check', bg: C.primaryTint, border: C.primaryTint, fg: C.primaryStrong },
  error: { icon: 'alert-circle', bg: C.dangerTint, border: C.dangerTint, fg: C.dangerStrong },
};

/**
 * Inline notice, as the web's <Notice>: info, success or error, always icon plus words.
 * children may be a string, or an array of strings shown as separate lines.
 */
export default function Notice({ kind = 'info', title, children, action, style }) {
  const k = KINDS[kind];
  const lines = children == null ? [] : Array.isArray(children) ? children : [children];
  return (
    <View
      accessibilityRole={kind === 'error' ? 'alert' : undefined}
      accessibilityLiveRegion={kind === 'error' ? 'assertive' : 'polite'}
      style={[{
        flexDirection: 'row', gap: S[3], paddingVertical: S[3], paddingHorizontal: S[4],
        backgroundColor: k.bg, borderWidth: 1, borderColor: k.border, borderRadius: R.md,
      }, style]}
    >
      <Icon name={k.icon} color={k.fg} style={{ marginTop: 2 }} />
      <View style={{ flex: 1, gap: S[1] }}>
        {title && <Text style={{ fontFamily: F.semibold, ...T.base, color: k.fg }}>{title}</Text>}
        {lines.map((line, i) => (
          typeof line === 'string'
            ? <Text key={i} style={{ fontFamily: F.regular, ...T.base, color: k.fg }}>{line}</Text>
            : <View key={i}>{line}</View>
        ))}
        {action && <View style={{ marginTop: S[1] }}>{action}</View>}
      </View>
    </View>
  );
}

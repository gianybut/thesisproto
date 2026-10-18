import { Text, View } from 'react-native';
import Icon from '../icons';
import { C, F, R, S, T } from '../theme';

// The web's .status-* classes (design.md §4 "Survey status labels").
const TONES = {
  waiting: { fg: C.muted, bg: C.surface, border: C.border },
  running: { fg: C.ink, bg: C.subtle, border: C.subtle },
  ready: { fg: C.primaryStrong, bg: C.primaryTint, border: C.primaryTint },
  failed: { fg: C.dangerStrong, bg: C.dangerTint, border: C.dangerTint },
};

/** Status: always icon plus words, never colour alone. status = { icon, tone, text }. */
export default function StatusLabel({ status, style }) {
  const t = TONES[status.tone] || TONES.waiting;
  return (
    <View style={[{
      flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', gap: S[1],
      paddingVertical: 2, paddingHorizontal: S[2], borderRadius: R.sm,
      backgroundColor: t.bg, borderWidth: 1, borderColor: t.border,
    }, style]}
    >
      <Icon name={status.icon} size={16} color={t.fg} />
      <Text style={{ fontFamily: F.semibold, ...T.sm, color: t.fg, fontVariant: ['tabular-nums'] }}>{status.text}</Text>
    </View>
  );
}

export function ProgressBar({ value, label, style }) {
  const v = Math.max(0, Math.min(100, Math.round(value || 0)));
  return (
    <View
      accessibilityRole="progressbar"
      accessibilityLabel={label}
      accessibilityValue={{ min: 0, max: 100, now: v }}
      style={[{
        height: 8, borderRadius: 4, overflow: 'hidden',
        backgroundColor: C.subtle, borderWidth: 1, borderColor: C.border,
      }, style]}
    >
      <View style={{ height: '100%', width: `${v}%`, backgroundColor: C.primary }} />
    </View>
  );
}

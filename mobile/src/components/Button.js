import { Pressable, Text, View } from 'react-native';
import Icon from '../icons';
import { C, F, R, S, TAP } from '../theme';

// design.md §7, as .btn-* in the web stylesheet. At most one primary per screen.
const VARIANTS = {
  primary: { bg: C.primary, pressed: C.primaryHover, fg: '#FFFFFF', border: C.primary },
  secondary: { bg: C.surface, pressed: C.subtle, fg: C.ink, border: C.borderStrong },
  quiet: { bg: 'transparent', pressed: C.subtle, fg: C.primary, border: 'transparent' },
  danger: { bg: C.danger, pressed: C.dangerStrong, fg: '#FFFFFF', border: C.danger },
  // Red text with a bin icon: "Delete survey" outside the confirm dialog.
  dangerQuiet: { bg: 'transparent', pressed: C.dangerTint, fg: C.danger, border: 'transparent' },
  // On navy or over the camera.
  onDark: { bg: 'transparent', pressed: 'rgba(255,255,255,0.12)', fg: '#FFFFFF', border: C.headerMuted },
};

/**
 * @param icon        icon name, drawn before the label (design.md §8: icons sit next to words)
 * @param iconColor   overrides the icon colour only (the red stop square on the camera)
 * @param iconOnly    44x44 with no label; needs accessibilityLabel
 * @param size        'large' for the camera's record button
 */
export default function Button({
  label, onPress, variant = 'secondary', icon, iconColor, iconOnly, disabled, block, size,
  accessibilityLabel, accessibilityHint, style,
}) {
  const v = VARIANTS[variant];
  const large = size === 'large';
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || label}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ disabled: !!disabled }}
      style={({ pressed }) => [
        {
          minHeight: large ? 64 : TAP,
          minWidth: TAP,
          paddingHorizontal: iconOnly ? 0 : variant === 'quiet' || variant === 'dangerQuiet' ? S[3] : S[4],
          flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: S[2],
          backgroundColor: pressed ? v.pressed : v.bg,
          borderWidth: 1, borderColor: v.border, borderRadius: R.sm,
          opacity: disabled ? 0.55 : 1,
        },
        iconOnly && { width: TAP },
        block && { alignSelf: 'stretch' },
        !block && { alignSelf: 'flex-start' },
        style,
      ]}
    >
      {icon && <Icon name={icon} size={large ? 24 : 20} color={iconColor || v.fg} />}
      {!iconOnly && (
        <Text style={{ fontFamily: F.semibold, fontSize: large ? 18 : 16, lineHeight: large ? 22 : 19, color: v.fg }}>
          {label}
        </Text>
      )}
    </Pressable>
  );
}

/** Buttons side by side, wrapping onto the next line on a narrow phone. */
export function ButtonRow({ children, style }) {
  return <View style={[{ flexDirection: 'row', flexWrap: 'wrap', gap: S[3] }, style]}>{children}</View>;
}

import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import Icon from '../icons';
import { C, F, R, S, T } from '../theme';

/**
 * An optional section, closed until asked for: the web's native <details> (.details), with the
 * summary in green and a chevron that turns when open.
 */
export default function Disclosure({ title, icon, defaultOpen = false, children, style }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <View style={[{ borderWidth: 1, borderColor: C.border, borderRadius: R.md, backgroundColor: C.surface }, style]}>
      <Pressable
        onPress={() => setOpen((o) => !o)}
        accessibilityRole="button"
        accessibilityState={{ expanded: open }}
        style={({ pressed }) => [{
          flexDirection: 'row', alignItems: 'center', gap: S[2], minHeight: 48, paddingHorizontal: S[4],
          borderRadius: R.md,
        }, pressed && { backgroundColor: C.subtle }]}
      >
        {icon && <Icon name={icon} color={C.primary} />}
        <Text style={{ flex: 1, fontFamily: F.semibold, ...T.base, color: C.primary }}>{title}</Text>
        <Icon name="chevron-down" size={20} color={C.primary} style={open && { transform: [{ rotate: '180deg' }] }} />
      </Pressable>
      {open && <View style={{ paddingHorizontal: S[4], paddingBottom: S[4], gap: S[3] }}>{children}</View>}
    </View>
  );
}

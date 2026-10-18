import { Text, View } from 'react-native';
import Icon from '../icons';
import { C, S, s } from '../theme';

/** design.md §12: a 48px icon, a heading and one action. An invitation, not an apology. */
export default function EmptyState({ icon, title, children, action }) {
  return (
    <View style={{ alignItems: 'flex-start', gap: S[2], paddingVertical: S[7] }}>
      {icon && <Icon name={icon} size={48} color={C.muted} style={{ marginBottom: S[2] }} />}
      <Text style={s.h2} accessibilityRole="header">{title}</Text>
      {children && <Text style={[s.body, { color: C.muted }]}>{children}</Text>}
      {action && <View style={{ marginTop: S[3] }}>{action}</View>}
    </View>
  );
}

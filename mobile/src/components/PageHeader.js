import { Pressable, Text, View } from 'react-native';
import Icon from '../icons';
import { C, F, S, T, TAP, s } from '../theme';

/**
 * One-line page header, as the web's <PageHeader>: an optional back link, the title, one short
 * muted meta line, and actions. Explanations go into hints and empty states, not here.
 *
 * @param back  { label, onPress } for a single "‹ Surveys" link above the title
 */
export default function PageHeader({ title, back, meta, actions, children }) {
  return (
    <View style={{ marginBottom: S[5] }}>
      {back && (
        <Pressable
          onPress={back.onPress}
          accessibilityRole="link"
          accessibilityLabel={`Back to ${back.label}`}
          style={({ pressed }) => [{ flexDirection: 'row', alignItems: 'center', gap: S[1], minHeight: TAP, alignSelf: 'flex-start' }, pressed && { opacity: 0.7 }]}
        >
          <Icon name="chevron-left" size={16} color={C.primary} />
          <Text style={{ fontFamily: F.semibold, ...T.sm, color: C.primary, textDecorationLine: 'underline' }}>{back.label}</Text>
        </Pressable>
      )}
      <Text style={s.h1} accessibilityRole="header">{title}</Text>
      {meta ? <Text style={[s.muted, s.num, { ...T.base, marginTop: S[2] }]}>{meta}</Text> : null}
      {actions && <View style={{ marginTop: S[4], flexDirection: 'row', flexWrap: 'wrap', gap: S[3] }}>{actions}</View>}
      {children}
    </View>
  );
}

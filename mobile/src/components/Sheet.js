import { useEffect, useRef } from 'react';
import { Modal, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../icons';
import { C, ELEVATION, F, R, S, T, TAP, s } from '../theme';
import Button from './Button';

/**
 * A panel that rises from the bottom over a dimmed screen: the phone form of the web's menu
 * panel and account panel. The backdrop, the close button and Android's back button close it.
 * Fades rather than slides (design.md §13: transitions under 200 ms, no entrance motion).
 */
export default function Sheet({ visible, onClose, onDismiss, title, children }) {
  const insets = useSafeAreaInsets();
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose} onDismiss={onDismiss} statusBarTranslucent>
      <View style={{ flex: 1, justifyContent: 'flex-end' }}>
        <Pressable style={[StyleSheet.absoluteFill, { backgroundColor: C.backdrop }]} onPress={onClose} accessibilityLabel="Close" />
        <View style={[{
          backgroundColor: C.surface, borderTopLeftRadius: R.md, borderTopRightRadius: R.md,
          paddingHorizontal: S.gutter, paddingTop: S[2], paddingBottom: Math.max(insets.bottom, S[4]),
        }, ELEVATION]}
        >
          <View style={[s.row, { justifyContent: 'space-between', minHeight: TAP, marginBottom: S[2] }]}>
            <Text style={[s.h3, { flex: 1 }]} numberOfLines={2} accessibilityRole="header">{title}</Text>
            <Button iconOnly icon="x" variant="quiet" accessibilityLabel="Close" onPress={onClose} />
          </View>
          {children}
        </View>
      </View>
    </Modal>
  );
}

/**
 * The "More" menu: a list of actions in a sheet. A danger item is red text with its icon
 * (design.md §7: "Delete survey" is red text with a bin icon).
 * items: [{ label, icon, onPress, danger }]
 */
export function ActionMenu({ visible, onClose, title, items }) {
  // The chosen action runs once the sheet has gone: iOS will not present an Alert (the delete
  // confirmation) while a modal is still dismissing. onDismiss is iOS only; Android runs it
  // as soon as the sheet is hidden.
  const pending = useRef(null);
  const runPending = () => {
    const fn = pending.current;
    pending.current = null;
    fn?.();
  };
  useEffect(() => {
    if (!visible && Platform.OS !== 'ios') runPending();
  }, [visible]);

  return (
    <Sheet visible={visible} onClose={onClose} onDismiss={runPending} title={title}>
      {items.filter(Boolean).map((item, i) => (
        <Pressable
          key={item.label}
          accessibilityRole="button"
          onPress={() => { pending.current = item.onPress; onClose(); }}
          style={({ pressed }) => [{
            flexDirection: 'row', alignItems: 'center', gap: S[3], minHeight: 52, paddingHorizontal: S[2],
            borderTopWidth: i ? 1 : 0, borderTopColor: C.border, borderRadius: R.sm,
          }, pressed && { backgroundColor: C.subtle }]}
        >
          <Icon name={item.icon} color={item.danger ? C.danger : C.ink} />
          <Text style={{ fontFamily: F.regular, ...T.base, color: item.danger ? C.danger : C.ink }}>{item.label}</Text>
        </Pressable>
      ))}
    </Sheet>
  );
}

import { Platform, StyleSheet } from 'react-native';

// The seven tokens from frontend/design.md. Do not add an eighth.
export const C = {
  paper: '#F6F4EE',
  card: '#FFFDF8',
  ink: '#1A1D19',
  inkSoft: '#5C635A',
  cyan: '#0E5661',
  rule: '#DEDACE',
  alert: '#9C4A21',
};

// Mono carries anything a machine produced (design.md §4).
export const MONO = Platform.select({ ios: 'Menlo', default: 'monospace' });
export const SERIF = Platform.select({ ios: 'Georgia', default: 'serif' });

export const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.paper },
  pad: { padding: 16 },
  h1: { fontFamily: SERIF, fontSize: 30, color: C.ink, marginBottom: 8 },
  h3: { fontFamily: SERIF, fontSize: 19, color: C.ink },
  body: { fontSize: 15, lineHeight: 22, color: C.ink },
  soft: { fontSize: 13, lineHeight: 19, color: C.inkSoft },
  label: { fontFamily: MONO, fontSize: 11, letterSpacing: 1.1, textTransform: 'uppercase', color: C.inkSoft },
  data: { fontFamily: MONO, fontSize: 13, color: C.ink },
  alert: { fontSize: 13, lineHeight: 19, color: C.alert },
  input: {
    borderWidth: 1, borderColor: C.rule, borderRadius: 4, backgroundColor: C.card,
    paddingHorizontal: 12, paddingVertical: 10, fontSize: 15, color: C.ink, marginTop: 6, marginBottom: 14,
  },
  card: { borderWidth: 1, borderColor: C.rule, borderRadius: 6, backgroundColor: C.card, padding: 14 },
  btn: { borderRadius: 4, paddingVertical: 12, paddingHorizontal: 16, alignItems: 'center', borderWidth: 1 },
  btnPrimary: { backgroundColor: C.cyan, borderColor: C.cyan },
  btnPrimaryText: { color: C.card, fontSize: 15, fontWeight: '600' },
  btnGhost: { backgroundColor: C.card, borderColor: C.rule },
  btnGhostText: { color: C.ink, fontSize: 15, fontWeight: '500' },
  row: { flexDirection: 'row', alignItems: 'center' },
});

import { Platform, StyleSheet } from 'react-native';

// The web app's tokens (frontend/src/index.css :root, built against frontend/design.md),
// carried over value for value. design.md is the authority here too: change a value there
// first, then in both stylesheets. Screens use these and never their own values.
export const C = {
  header: '#13294B',        // navy: the top bar only
  headerMuted: '#C5D0E0',   // role and secondary text on navy (9.31:1)
  bg: '#FFFFFF',
  surface: '#FFFFFF',
  subtle: '#F5F6F3',        // tiles, skeletons, pressed fills
  ink: '#17201B',           // 16.68:1 on white
  muted: '#4A5550',         // 7.76:1 on white
  primary: '#046B3E',       // the logo green: primary buttons, links (6.61:1)
  primaryHover: '#03552F',  // pressed state of a primary button
  primaryTint: '#E5F1EA',
  primaryStrong: '#035230',
  danger: '#A1262B',
  dangerTint: '#FBECEC',
  dangerStrong: '#8E1F24',
  border: '#D3D9D4',        // decorative only: panel outlines, row dividers
  borderStrong: '#7A847E',  // inputs, secondary buttons (3.87:1)
  scrim: 'rgba(23, 32, 27, 0.72)',  // ink at 72%: chrome drawn over the camera
  backdrop: 'rgba(23, 32, 27, 0.45)', // behind a sheet, as the web dialog's ::backdrop
};

// Public Sans 400/600/700, loaded in App.js. Each weight is its own family because Android
// ignores fontWeight on a custom font. Never set fontWeight alongside these.
export const F = {
  regular: 'PublicSans_400Regular',
  semibold: 'PublicSans_600SemiBold',
  bold: 'PublicSans_700Bold',
};
// Code only (a raw error message, a file name); design.md §5.
export const MONO = Platform.select({ ios: 'Menlo', default: 'monospace' });

// --text-* at a 16px root; xl is the phone size of the page title.
export const T = {
  sm: { fontSize: 14, lineHeight: 20 },
  base: { fontSize: 16, lineHeight: 24 },
  md: { fontSize: 18, lineHeight: 25 },
  lg: { fontSize: 22, lineHeight: 29 },
  xl: { fontSize: 24, lineHeight: 30 },
  stat: { fontSize: 36, lineHeight: 40 },
};

// --space-1 … --space-8 (4px base). Gutter is the phone gutter.
export const S = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48, 8: 64, gutter: 16 };
export const R = { sm: 4, md: 8 };   // buttons, inputs, labels / panels, sheets
export const TAP = 44;               // minimum tap target

// --elevation-1: only for floating things (the sheet).
export const ELEVATION = Platform.select({
  ios: { shadowColor: C.ink, shadowOpacity: 0.12, shadowRadius: 12, shadowOffset: { width: 0, height: 4 } },
  default: { elevation: 4 },
});

// Tabular figures on times, sizes, counts and coordinates (.num on the web).
const NUM = { fontVariant: ['tabular-nums'] };

export const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  page: { paddingHorizontal: S.gutter, paddingTop: S[5], paddingBottom: S[7] },
  stack: { gap: S[5] },
  stackSm: { gap: S[3] },
  row: { flexDirection: 'row', alignItems: 'center' },
  wrapRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: S[3] },

  h1: { fontFamily: F.bold, ...T.xl, color: C.ink },
  h2: { fontFamily: F.bold, ...T.lg, color: C.ink },
  h3: { fontFamily: F.semibold, ...T.md, color: C.ink },
  body: { fontFamily: F.regular, ...T.base, color: C.ink },
  strong: { fontFamily: F.semibold },
  small: { fontFamily: F.regular, ...T.sm, color: C.ink },
  muted: { fontFamily: F.regular, ...T.sm, color: C.muted },
  num: NUM,
  code: { fontFamily: MONO, fontSize: 13, color: C.muted },
  link: { fontFamily: F.semibold, color: C.primary, textDecorationLine: 'underline' },

  panel: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: R.md, padding: S[4] },
  panelTitle: { fontFamily: F.semibold, ...T.md, color: C.ink },
  divider: { height: 1, backgroundColor: C.border },

  fieldLabel: { fontFamily: F.semibold, ...T.base, color: C.ink },
  fieldHint: { fontFamily: F.regular, ...T.sm, color: C.muted },
  fieldError: { fontFamily: F.semibold, ...T.sm, color: C.danger },
  input: {
    minHeight: TAP, paddingHorizontal: S[3], paddingVertical: S[2],
    backgroundColor: C.surface, borderWidth: 1, borderColor: C.borderStrong, borderRadius: R.sm,
    fontFamily: F.regular, fontSize: 16, color: C.ink,
  },
});

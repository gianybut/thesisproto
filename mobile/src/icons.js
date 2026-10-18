// The web app's hand-written outline icons (frontend/src/icons.jsx): 24px viewBox, 2px stroke,
// round caps and joins. Same paths, so a symbol means the same thing on both. The last group
// (share, wifi, record, stop) exists only here and is drawn the same way.
//
// design.md §8: always next to words, except the "More actions" and close buttons, which carry
// an accessibilityLabel. 20px in buttons, 16px in labels, 48px only in empty states. Never in
// a damage-class colour.
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import { C } from './theme';

const PATHS = {
  video: () => <><Rect x="2" y="6" width="14" height="12" rx="2" /><Path d="m16 10.5 6-3.5v10l-6-3.5" /></>,
  upload: () => <Path d="M12 16V4M7 9l5-5 5 5M4 20h16" />,
  'map-pin': () => <><Path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z" /><Circle cx="12" cy="9.5" r="2.5" /></>,
  route: () => <><Circle cx="6" cy="19" r="2" /><Circle cx="18" cy="5" r="2" /><Path d="M8 19h8.5a3.5 3.5 0 0 0 0-7h-9a3.5 3.5 0 0 1 0-7H16" /></>,
  play: () => <Path d="M7 4.5v15l12.5-7.5L7 4.5Z" />,
  pencil: () => <Path d="M4 20h4L19.5 8.5a2.1 2.1 0 0 0-3-3L5 17v3ZM14.5 7.5l2 2" />,
  dots: (c) => <><Circle cx="5" cy="12" r="1.2" fill={c} /><Circle cx="12" cy="12" r="1.2" fill={c} /><Circle cx="19" cy="12" r="1.2" fill={c} /></>,
  trash: () => <Path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" />,
  download: () => <Path d="M12 4v12M7 11l5 5 5-5M4 20h16" />,
  refresh: () => <Path d="M20 12a8 8 0 1 1-2.4-5.7M20 4v5h-5" />,
  check: () => <Path d="m5 12.5 4.5 4.5L19 7" />,
  clock: () => <><Circle cx="12" cy="12" r="9" /><Path d="M12 7v5l3.5 2" /></>,
  'half-circle': (c) => <><Circle cx="12" cy="12" r="9" /><Path d="M12 3a9 9 0 0 1 0 18V3Z" fill={c} /></>,
  'alert-circle': () => <><Circle cx="12" cy="12" r="9" /><Path d="M12 7.5v5.5M12 16.5v.01" /></>,
  'alert-triangle': () => <Path d="M12 4 2.5 20h19L12 4ZM12 10v4.5M12 17.5v.01" />,
  'info-circle': () => <><Circle cx="12" cy="12" r="9" /><Path d="M12 11v5.5M12 7.5v.01" /></>,
  x: () => <Path d="M6 6l12 12M18 6 6 18" />,
  logout: () => <Path d="M14 4h5v16h-5M10 8l-4 4 4 4M6 12h10" />,
  'chevron-down': () => <Path d="m6 9 6 6 6-6" />,
  'chevron-right': () => <Path d="m9 6 6 6-6 6" />,
  'chevron-left': () => <Path d="m15 6-6 6 6 6" />,
  'user-circle': () => <><Circle cx="12" cy="12" r="9" /><Circle cx="12" cy="10" r="3" /><Path d="M6.5 18.5a6.5 6.5 0 0 1 11 0" /></>,
  road: () => <Path d="M8 3 4 21M16 3l4 18M12 4v3M12 11v3M12 18v2" />,

  // Mobile only
  share: () => <Path d="M12 15V3M8 7l4-4 4 4M5 11v9h14v-9" />,
  wifi: () => <Path d="M2.5 8.5a14 14 0 0 1 19 0M5.5 12a9.5 9.5 0 0 1 13 0M8.5 15.5a5 5 0 0 1 7 0M12 19v.01" />,
  record: (c) => <Circle cx="12" cy="12" r="7" fill={c} stroke="none" />,
  stop: (c) => <Rect x="6" y="6" width="12" height="12" rx="2" fill={c} stroke="none" />,
};

export default function Icon({ name, size = 20, color = C.ink, style }) {
  const draw = PATHS[name];
  return (
    <Svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={style}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {draw ? draw(color) : null}
    </Svg>
  );
}

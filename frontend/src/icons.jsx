// Hand-written outline icons (24px viewBox, 2px round stroke, currentColor). No icon package.
// Icons always sit next to words; they are decorative (aria-hidden) unless the control is
// icon-only, in which case the control carries the aria-label. Damage classes never get icons.

const PATHS = {
  home: <path d="M3 10.5 12 3l9 7.5M5 9v12h5v-6h4v6h5V9" />,
  upload: <path d="M12 16V4M7 9l5-5 5 5M4 20h16" />,
  video: <><rect x="2" y="6" width="14" height="12" rx="2" /><path d="m16 10.5 6-3.5v10l-6-3.5" /></>,
  map: <path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2ZM9 4v14M15 6v14" />,
  table: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18M3 15h18M9 10v10" /></>,
  'map-pin': <><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z" /><circle cx="12" cy="9.5" r="2.5" /></>,
  'map-pin-plus': <><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z" /><path d="M12 7v5M9.5 9.5h5" /></>,
  route: <><circle cx="6" cy="19" r="2" /><circle cx="18" cy="5" r="2" /><path d="M8 19h8.5a3.5 3.5 0 0 0 0-7h-9a3.5 3.5 0 0 1 0-7H16" /></>,
  play: <path d="M7 4.5v15l12.5-7.5L7 4.5Z" />,
  pencil: <path d="M4 20h4L19.5 8.5a2.1 2.1 0 0 0-3-3L5 17v3ZM14.5 7.5l2 2" />,
  dots: <><circle cx="5" cy="12" r="1.2" fill="currentColor" /><circle cx="12" cy="12" r="1.2" fill="currentColor" /><circle cx="19" cy="12" r="1.2" fill="currentColor" /></>,
  trash: <path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" />,
  download: <path d="M12 4v12M7 11l5 5 5-5M4 20h16" />,
  refresh: <path d="M20 12a8 8 0 1 1-2.4-5.7M20 4v5h-5" />,
  filter: <path d="M3 5h18l-7 8.5V19l-4 2v-7.5L3 5Z" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
  check: <path d="m5 12.5 4.5 4.5L19 7" />,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3.5 2" /></>,
  'half-circle': <><circle cx="12" cy="12" r="9" /><path d="M12 3a9 9 0 0 1 0 18V3Z" fill="currentColor" /></>,
  hourglass: <path d="M6 3h12M6 21h12M7 3v3.5l5 5.5-5 5.5V21M17 3v3.5L12 12l5 5.5V21" />,
  'alert-circle': <><circle cx="12" cy="12" r="9" /><path d="M12 7.5v5.5M12 16.5v.01" /></>,
  'alert-triangle': <path d="M12 4 2.5 20h19L12 4ZM12 10v4.5M12 17.5v.01" />,
  'info-circle': <><circle cx="12" cy="12" r="9" /><path d="M12 11v5.5M12 7.5v.01" /></>,
  menu: <path d="M4 6h16M4 12h16M4 18h16" />,
  x: <path d="M6 6l12 12M18 6 6 18" />,
  logout: <path d="M14 4h5v16h-5M10 8l-4 4 4 4M6 12h10" />,
  'chevron-down': <path d="m6 9 6 6 6-6" />,
  'chevron-right': <path d="m9 6 6 6-6 6" />,
  'chevron-left': <path d="m15 6-6 6 6 6" />,
  'user-circle': <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="10" r="3" /><path d="M6.5 18.5a6.5 6.5 0 0 1 11 0" /></>,
  road: <path d="M8 3 4 21M16 3l4 18M12 4v3M12 11v3M12 18v2" />,
  plus: <path d="M12 5v14M5 12h14" />,
};

export default function Icon({ name, size = 20, className = '' }) {
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {PATHS[name]}
    </svg>
  );
}

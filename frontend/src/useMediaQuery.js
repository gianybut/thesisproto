import { useEffect, useState } from 'react';

// For layouts that must render different markup (not just different CSS) per screen size,
// e.g. filters that are a sidebar on desktop and a closed <details> on phones.
export const WIDE = '(min-width: 60rem)';

export default function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const onChange = () => setMatches(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, [query]);
  return matches;
}

// Single source of truth for what each role may open. App.jsx guards routes with it and
// Navbar.jsx builds the menu from it, so the two can no longer drift apart.
// Unknown roles fall back to barangay — the most restrictive set — so a stale role left in
// the database cannot widen access.
export const ROLE_ROUTE_ACCESS = {
  barangay:   ['/', '/upload', '/videos', '/map'],
  municipal:  ['/', '/upload', '/videos', '/map', '/database'],
  provincial: ['/', '/upload', '/videos', '/map', '/database'],
  admin:      ['/', '/upload', '/videos', '/map', '/database'],
};

export const ROLE_LABELS = {
  admin: 'Administrator',
  provincial: 'Provincial office',
  municipal: 'Municipal office',
  barangay: 'Barangay',
};

export const roleOf = (user) => (ROLE_ROUTE_ACCESS[user?.role] ? user.role : 'barangay');

export function canAccess(role, path) {
  const allowed = ROLE_ROUTE_ACCESS[role] || ROLE_ROUTE_ACCESS.barangay;
  // /videos/:id and /videos/:id/georeference ride on /videos
  if (path.startsWith('/videos/')) return allowed.includes('/videos');
  return allowed.includes(path);
}

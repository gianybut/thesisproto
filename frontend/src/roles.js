// The two system roles of the thesis (Chapter 3, Sec 3.5 and Fig. 3.5.1). A system
// administrator can do everything road maintenance personnel can, plus Administration
// (accounts and the activity log), correcting and deleting damage records, and seeing every
// survey. This file only decides what the web app shows: the server enforces the same rules
// (backend/auth_tokens.py admin_required and visible_videos), so hiding a page is a
// convenience, not the protection.
//
// Unknown roles fall back to personnel, the more limited set, so a stale role left in the
// database cannot widen access.
const PERSONNEL_PATHS = ['/', '/upload', '/videos', '/map', '/database'];

export const ROLE_ROUTE_ACCESS = {
  personnel: PERSONNEL_PATHS,
  admin: [...PERSONNEL_PATHS, '/admin'],
};

export const ROLE_LABELS = {
  personnel: 'Road maintenance personnel',
  admin: 'System administrator',
};

export const roleOf = (user) => (ROLE_ROUTE_ACCESS[user?.role] ? user.role : 'personnel');
export const isAdmin = (user) => roleOf(user) === 'admin';

export function canAccess(role, path) {
  const allowed = ROLE_ROUTE_ACCESS[role] || ROLE_ROUTE_ACCESS.personnel;
  // /videos/:id and /videos/:id/georeference ride on /videos; /admin/* on /admin
  if (path.startsWith('/videos/')) return allowed.includes('/videos');
  if (path.startsWith('/admin/')) return allowed.includes('/admin');
  return allowed.includes(path);
}

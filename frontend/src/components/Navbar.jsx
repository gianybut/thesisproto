import { NavLink, useNavigate } from 'react-router-dom';

const ROLE_LABELS = {
  admin: 'Admin',
  provincial: 'Provincial',
  municipal: 'Municipal',
  barangay: 'Barangay',
};

// Which nav items each role can see (must match ROLE_ROUTE_ACCESS in App.jsx)
const ROLE_NAV = {
  barangay:   ['/', '/upload', '/videos', '/map'],
  municipal:  ['/', '/upload', '/videos', '/map', '/database'],
  provincial: ['/', '/upload', '/videos', '/map', '/database'],
  admin:      ['/', '/upload', '/videos', '/map', '/database'],
};

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', end: true },
  { path: '/upload', label: 'Upload' },
  { path: '/videos', label: 'Videos' },
  { path: '/map', label: 'Map' },
  { path: '/database', label: 'Database' },
];

export default function Navbar({ user, onLogout }) {
  const navigate = useNavigate();
  const role = user.role || 'barangay';
  const allowedPaths = ROLE_NAV[role] || ROLE_NAV.barangay;

  const handleLogout = () => {
    onLogout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand">
        <div className="logo-icon">🛣️</div>
        <h1>Bantay Kalsada</h1>
      </NavLink>

      <div className="navbar-nav">
        {NAV_ITEMS.filter(item => allowedPaths.includes(item.path)).map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.end}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            {item.label}
          </NavLink>
        ))}
      </div>

      <div className="navbar-user">
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
          <span style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>{user.lgu_name}</span>
          <span className={`role-badge ${role}`}>{ROLE_LABELS[role] || role}</span>
        </div>
        <div className="user-avatar">{user.full_name?.[0] || 'U'}</div>
        <button className="btn btn-secondary btn-sm" onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  );
}

import { NavLink, useNavigate } from 'react-router-dom';

export default function Navbar({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand">
        <div className="logo-icon">🛣️</div>
        <h1>RoadScan AI</h1>
      </NavLink>

      <div className="navbar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          Dashboard
        </NavLink>
        <NavLink to="/upload" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          Upload
        </NavLink>
        <NavLink to="/videos" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          Videos
        </NavLink>
      </div>

      <div className="navbar-user">
        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{user.lgu_name}</span>
        <div className="user-avatar">{user.full_name?.[0] || 'U'}</div>
        <button className="btn btn-secondary btn-sm" onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  );
}

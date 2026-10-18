import { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import Icon from '../icons';
import Disclosure from './Disclosure';
import { ROLE_LABELS, ROLE_ROUTE_ACCESS, roleOf } from '../roles';


const NAV_ITEMS = [
  { path: '/', label: 'Overview', icon: 'home', end: true },
  { path: '/upload', label: 'Upload', icon: 'upload' },
  { path: '/videos', label: 'Surveys', icon: 'video' },
  { path: '/map', label: 'Damage map', icon: 'map' },
  { path: '/database', label: 'Damage records', icon: 'table' },
  { path: '/admin', label: 'Administration', icon: 'shield' },
];


/** One navy bar: brand, role-filtered navigation, account. Collapses to "Menu" below 64rem. */
export default function Header({ user, onLogout }) {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const role = roleOf(user);
  const items = NAV_ITEMS.filter(i => ROLE_ROUTE_ACCESS[role].includes(i.path));
  const name = user.full_name || user.username;

  const signOut = () => { setMenuOpen(false); onLogout(); navigate('/'); };
  const navClass = ({ isActive }) => `nav-link${isActive ? ' is-current' : ''}`;

  return (
    <header className="app-header">
      <div className="header-inner">
        <Link to="/" className="brand" onClick={() => setMenuOpen(false)}>
          <span className="brand-tile">
            <img src="/oculubak-icon-mono.svg" alt="" width="32" height="21" />
          </span>
          <span className="brand-name">OcuLubak</span>
        </Link>

        <nav className="main-nav" aria-label="Main">
          <ul>
            {items.map(i => (
              <li key={i.path}>
                <NavLink to={i.path} end={i.end} className={navClass}>
                  <Icon name={i.icon} />{i.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="account">
          <Disclosure
            align="end"
            panelClass="account-panel"
            renderButton={(props, open) => (
              <button className="account-button" {...props}>
                <Icon name="user-circle" />
                <span className="account-text">
                  <span className="account-name">{name}</span>
                  <span className="account-role">{ROLE_LABELS[role]}</span>
                </span>
                <Icon name="chevron-down" size={16} className={open ? 'flip' : ''} />
              </button>
            )}
          >
            {() => (
              <>
                <p className="account-panel-name">{name}</p>
                <p className="account-panel-meta">{ROLE_LABELS[role]}</p>
                <button type="button" className="btn btn-secondary btn-block" onClick={signOut}>
                  <Icon name="logout" />Sign out
                </button>
              </>
            )}
          </Disclosure>
        </div>

        <button type="button" className="menu-toggle" aria-expanded={menuOpen} aria-controls="phone-menu"
          onClick={() => setMenuOpen(o => !o)}>
          <Icon name={menuOpen ? 'x' : 'menu'} />{menuOpen ? 'Close' : 'Menu'}
        </button>
      </div>

      {menuOpen && (
        <div id="phone-menu" className="phone-menu">
          <nav aria-label="Main">
            <ul>
              {items.map(i => (
                <li key={i.path}>
                  <NavLink to={i.path} end={i.end} className={navClass} onClick={() => setMenuOpen(false)}>
                    <Icon name={i.icon} />{i.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <div className="phone-account">
            <p className="phone-account-name">{name}</p>
            <p className="phone-account-meta">{ROLE_LABELS[role]}</p>
            <button type="button" className="btn btn-on-dark" onClick={signOut}>
              <Icon name="logout" />Sign out
            </button>
          </div>
        </div>
      )}
    </header>
  );
}

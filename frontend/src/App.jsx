import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { AUTH_EXPIRED, TOKEN_KEY } from './api';
import { canAccess, roleOf } from './roles';
import LoginPage from './pages/LoginPage';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import VideoListPage from './pages/VideoListPage';
import SurveyPage from './pages/SurveyPage';
import DamageMapPage from './pages/DamageMapPage';
import DatabasePage from './pages/DatabasePage';
import Header from './components/Header';
import Footer from './components/Footer';

// Protected route wrapper — redirects to the overview if the role is not permitted.
// Route access per role lives in roles.js, shared with the header.
function ProtectedRoute({ user, path, children }) {
  if (!canAccess(roleOf(user), path)) {
    return <Navigate to="/" replace />;
  }
  return children;
}

// Logged out: any app URL goes to the login form, which returns there after signing in.
function ToLogin() {
  const { pathname, search } = useLocation();
  return <Navigate to="/login" replace state={{ from: pathname + search }} />;
}

function AfterLogin() {
  const { state } = useLocation();
  return <Navigate to={state?.from || '/'} replace />;
}

function App() {
  // A stored user without a token predates signed tokens; treat it as logged out.
  const [user, setUser] = useState(() =>
    localStorage.getItem(TOKEN_KEY) ? JSON.parse(localStorage.getItem('user') || 'null') : null);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    const onExpired = () => {
      setUser(null);
      setNotice('Your session has expired. Sign in again.');
    };
    window.addEventListener(AUTH_EXPIRED, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED, onExpired);
  }, []);

  const handleLogin = (userData, token) => {
    setUser(userData);
    setNotice('');
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem(TOKEN_KEY, token);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem(TOKEN_KEY);
  };

  // The landing page is "/" for visitors and "/about" for everyone (the account menu links there).
  return (
    <Router>
      <Routes>
        <Route path="/about" element={<LandingPage user={user} />} />
        {user ? (
          <Route path="*" element={<AppShell user={user} onLogout={handleLogout} />} />
        ) : (
          <>
            <Route path="/" element={<LandingPage user={null} />} />
            <Route path="/login" element={<LoginPage onLogin={handleLogin} notice={notice} />} />
            <Route path="*" element={<ToLogin />} />
          </>
        )}
      </Routes>
    </Router>
  );
}

function AppShell({ user, onLogout }) {
  return (
    <>
      <a className="skip-link" href="#main">Skip to main content</a>
      <Header user={user} onLogout={onLogout} />
      <main id="main" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<DashboardPage user={user} />} />
          <Route path="/login" element={<AfterLogin />} />

          <Route path="/upload" element={
            <ProtectedRoute user={user} path="/upload"><UploadPage /></ProtectedRoute>
          } />
          <Route path="/videos" element={
            <ProtectedRoute user={user} path="/videos"><VideoListPage /></ProtectedRoute>
          } />
          {/* Survey detail and "Place on the map" are two tabs of one page; both URLs stay. */}
          <Route path="/videos/:id" element={
            <ProtectedRoute user={user} path="/videos"><SurveyPage tab="damage" /></ProtectedRoute>
          } />
          <Route path="/videos/:id/georeference" element={
            <ProtectedRoute user={user} path="/videos"><SurveyPage tab="place" /></ProtectedRoute>
          } />
          <Route path="/map" element={
            <ProtectedRoute user={user} path="/map"><DamageMapPage /></ProtectedRoute>
          } />
          <Route path="/database" element={
            <ProtectedRoute user={user} path="/database"><DatabasePage /></ProtectedRoute>
          } />

          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
}

export default App;

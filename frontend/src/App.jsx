import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { AUTH_EXPIRED, TOKEN_KEY } from './api';
import { canAccess, roleOf } from './roles';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import VideoListPage from './pages/VideoListPage';
import SurveyPage from './pages/SurveyPage';
import DamageMapPage from './pages/DamageMapPage';
import DatabasePage from './pages/DatabasePage';
import AdminPage from './pages/AdminPage';
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

  if (!user) {
    return <LoginPage onLogin={handleLogin} notice={notice} />;
  }

  return (
    <Router>
      <a className="skip-link" href="#main">Skip to main content</a>
      <Header user={user} onLogout={handleLogout} />
      <main id="main" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<DashboardPage user={user} />} />

          <Route path="/upload" element={
            <ProtectedRoute user={user} path="/upload"><UploadPage /></ProtectedRoute>
          } />
          <Route path="/videos" element={
            <ProtectedRoute user={user} path="/videos"><VideoListPage user={user} /></ProtectedRoute>
          } />
          {/* Survey detail and "Place on the map" are two tabs of one page; both URLs stay. */}
          <Route path="/videos/:id" element={
            <ProtectedRoute user={user} path="/videos"><SurveyPage tab="damage" user={user} /></ProtectedRoute>
          } />
          <Route path="/videos/:id/georeference" element={
            <ProtectedRoute user={user} path="/videos"><SurveyPage tab="place" user={user} /></ProtectedRoute>
          } />
          <Route path="/map" element={
            <ProtectedRoute user={user} path="/map"><DamageMapPage /></ProtectedRoute>
          } />
          <Route path="/database" element={
            <ProtectedRoute user={user} path="/database"><DatabasePage user={user} /></ProtectedRoute>
          } />
          {/* Administration (system administrator only): two tabs of one page. */}
          <Route path="/admin" element={<Navigate to="/admin/accounts" replace />} />
          <Route path="/admin/accounts" element={
            <ProtectedRoute user={user} path="/admin"><AdminPage tab="accounts" user={user} /></ProtectedRoute>
          } />
          <Route path="/admin/activity" element={
            <ProtectedRoute user={user} path="/admin"><AdminPage tab="activity" user={user} /></ProtectedRoute>
          } />

          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
      <Footer />
    </Router>
  );
}

export default App;

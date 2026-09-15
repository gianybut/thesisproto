import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import VideoListPage from './pages/VideoListPage';
import DetectionViewerPage from './pages/DetectionViewerPage';
import GeoreferencePage from './pages/GeoreferencePage';
import DamageMapPage from './pages/DamageMapPage';
import DatabasePage from './pages/DatabasePage';
import Navbar from './components/Navbar';

// Role-based route access control
// Defines which routes each role is ALLOWED to access
const ROLE_ROUTE_ACCESS = {
  barangay:   ['/', '/upload', '/videos', '/map'],
  municipal:  ['/', '/upload', '/videos', '/map', '/database'],
  provincial: ['/', '/upload', '/videos', '/map', '/database'],
  admin:      ['/', '/upload', '/videos', '/map', '/database'],
};

// Helper: check if a user role can access a given path.
// Unknown roles fall back to barangay — the most restrictive set — so a stale
// role left in the database cannot widen access.
function canAccess(role, path) {
  const allowed = ROLE_ROUTE_ACCESS[role] || ROLE_ROUTE_ACCESS.barangay;
  // For /videos/:id, check if /videos is allowed
  if (path.startsWith('/videos/')) return allowed.includes('/videos');
  return allowed.includes(path);
}

// Protected route wrapper — redirects to dashboard if role is not permitted
function ProtectedRoute({ user, path, children }) {
  const role = user?.role || 'barangay';
  if (!canAccess(role, path)) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function App() {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('user') || 'null'));

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <Router>
      <Navbar user={user} onLogout={handleLogout} />
      <Routes>
        <Route path="/" element={<DashboardPage user={user} />} />

        <Route path="/upload" element={
          <ProtectedRoute user={user} path="/upload"><UploadPage /></ProtectedRoute>
        } />
        <Route path="/videos" element={
          <ProtectedRoute user={user} path="/videos"><VideoListPage /></ProtectedRoute>
        } />
        <Route path="/videos/:id" element={
          <ProtectedRoute user={user} path="/videos"><DetectionViewerPage /></ProtectedRoute>
        } />
        <Route path="/videos/:id/georeference" element={
          <ProtectedRoute user={user} path="/videos"><GeoreferencePage /></ProtectedRoute>
        } />
        <Route path="/map" element={
          <ProtectedRoute user={user} path="/map"><DamageMapPage /></ProtectedRoute>
        } />
        <Route path="/database" element={
          <ProtectedRoute user={user} path="/database"><DatabasePage /></ProtectedRoute>
        } />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;

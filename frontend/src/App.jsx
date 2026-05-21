import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import VideoListPage from './pages/VideoListPage';
import DetectionViewerPage from './pages/DetectionViewerPage';
import DamageMapPage from './pages/DamageMapPage';
import PublicReportPage from './pages/PublicReportPage';
import ReportsManagementPage from './pages/ReportsManagementPage';
import DatabasePage from './pages/DatabasePage';
import AccountsPage from './pages/AccountsPage';
import Navbar from './components/Navbar';

// Role-based route access control
// Defines which routes each role is ALLOWED to access
const ROLE_ROUTE_ACCESS = {
  public:     ['/', '/report', '/map'],
  barangay:   ['/', '/upload', '/videos', '/map', '/report', '/reports'],
  municipal:  ['/', '/upload', '/videos', '/map', '/report', '/reports', '/database'],
  provincial: ['/', '/upload', '/videos', '/map', '/report', '/reports', '/database'],
  dpwh:       ['/', '/upload', '/videos', '/map', '/report', '/reports', '/database'],
  admin:      ['/', '/upload', '/videos', '/map', '/report', '/reports', '/database', '/accounts'],
  inspector:  ['/', '/upload', '/videos', '/map', '/database'],
};

// Helper: check if a user role can access a given path
function canAccess(role, path) {
  const allowed = ROLE_ROUTE_ACCESS[role] || ROLE_ROUTE_ACCESS.public;
  // For /videos/:id, check if /videos is allowed
  if (path.startsWith('/videos/')) return allowed.includes('/videos');
  return allowed.includes(path);
}

// Protected route wrapper — redirects to dashboard if role is not permitted
function ProtectedRoute({ user, path, children }) {
  const role = user?.role || 'public';
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
        <Route path="/map" element={
          <ProtectedRoute user={user} path="/map"><DamageMapPage /></ProtectedRoute>
        } />
        <Route path="/report" element={
          <PublicReportPage user={user} />
        } />
        <Route path="/reports" element={
          <ProtectedRoute user={user} path="/reports"><ReportsManagementPage /></ProtectedRoute>
        } />
        <Route path="/database" element={
          <ProtectedRoute user={user} path="/database"><DatabasePage /></ProtectedRoute>
        } />
        <Route path="/accounts" element={
          <ProtectedRoute user={user} path="/accounts"><AccountsPage /></ProtectedRoute>
        } />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;

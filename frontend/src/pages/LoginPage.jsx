import { useState } from 'react';
import { authAPI } from '../api';

export default function LoginPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', full_name: '', lgu_name: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = isRegister
        ? await authAPI.register(form)
        : await authAPI.login(form.username, form.password);
      onLogin(res.data.user);
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <div className="login-page">
      <div className="glass-card login-card fade-in">
        <div className="login-brand">
          <div className="logo-icon">🛣️</div>
          <h2>RoadScan AI</h2>
          <p className="subtitle">Pothole Detection System for LGUs</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <div className="input-group">
                <label>Full Name</label>
                <input className="input-field" type="text" value={form.full_name}
                  onChange={updateField('full_name')} placeholder="Juan Dela Cruz" required />
              </div>
              <div className="input-group">
                <label>LGU Name</label>
                <input className="input-field" type="text" value={form.lgu_name}
                  onChange={updateField('lgu_name')} placeholder="Municipality of..." required />
              </div>
            </>
          )}
          <div className="input-group">
            <label>Username</label>
            <input className="input-field" type="text" value={form.username}
              onChange={updateField('username')} placeholder="Enter username" required />
          </div>
          <div className="input-group">
            <label>Password</label>
            <input className="input-field" type="password" value={form.password}
              onChange={updateField('password')} placeholder="Enter password" required />
          </div>
          <button className="btn btn-primary btn-lg" type="submit" disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}>
            {loading ? <span className="spinner" /> : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div className="login-footer">
          {isRegister ? (
            <p>Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(false); }}>Sign in</a></p>
          ) : (
            <p>Need an account? <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(true); }}>Register</a></p>
          )}
        </div>
      </div>
    </div>
  );
}

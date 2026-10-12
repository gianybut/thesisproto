import { useState } from 'react';
import { authAPI } from '../api';

export default function LoginPage({ onLogin, notice }) {
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await authAPI.login(form.username, form.password);
      onLogin(res.data.user, res.data.token);
    } catch (err) {
      setError(err.response?.data?.error || 'Could not sign in. Check your username and password.');
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <div className="login-page">
      <div className="panel login-card fade-in">
        <div className="login-brand">
          <div className="logo-icon">🛣️</div>
          <h2>Bantay Kalsada</h2>
          <p className="subtitle">Road damage detection for local government</p>
        </div>

        {notice && !error && <div className="alert alert-error">{notice}</div>}
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Username</label>
            <input className="input-field" type="text" value={form.username}
              onChange={updateField('username')} autoComplete="username" required />
          </div>
          <div className="input-group">
            <label>Password</label>
            <input className="input-field" type="password" value={form.password}
              onChange={updateField('password')} autoComplete="current-password" required />
          </div>
          <button className="btn btn-primary btn-lg" type="submit" disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}>
            {loading ? <span className="spinner" /> : 'Sign in'}
          </button>
        </form>

        <div className="login-footer">
          <p>Accounts are set up by your system administrator.</p>
        </div>
      </div>
    </div>
  );
}

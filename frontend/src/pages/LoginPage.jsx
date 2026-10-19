import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../api';
import { errorMessage } from '../labels';
import ErrorSummary from '../components/ErrorSummary';
import Notice from '../components/Notice';

export default function LoginPage({ onLogin, notice }) {
  const [form, setForm] = useState({ username: '', password: '' });
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const missing = {};
    if (!form.username.trim()) missing.username = 'Enter your username';
    if (!form.password) missing.password = 'Enter your password';
    setFieldErrors(missing);
    if (Object.keys(missing).length) return;

    setLoading(true);
    try {
      const res = await authAPI.login(form.username.trim(), form.password);
      onLogin(res.data.user, res.data.token);
    } catch (err) {
      setError(errorMessage(err, 'Could not sign in. Check your username and password.'));
      setLoading(false);
    }
  };

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });
  const summary = Object.entries(fieldErrors).map(([field, message]) => ({ field, message }));

  const field = (id, label, type, autoComplete) => (
    <div className={`field${fieldErrors[id] ? ' has-error' : ''}`}>
      <label className="field-label" htmlFor={id}>{label}</label>
      {fieldErrors[id] && <p className="field-error" id={`${id}-error`}>{fieldErrors[id]}</p>}
      <input id={id} className="input" type={type} value={form[id]} onChange={update(id)}
        autoComplete={autoComplete} aria-invalid={Boolean(fieldErrors[id])}
        aria-describedby={fieldErrors[id] ? `${id}-error` : undefined} />
    </div>
  );

  return (
    <div className="login-page">
      <main id="main" className="login-main">
        <div className="login-card">
          <img src="/oculubak-icon-mono.svg" alt="" className="login-logo" width="100" height="64" />
          <h1 className="login-title">OcuLubak</h1>
          <p className="login-tagline">Find and track road damage from road survey videos.</p>

          {notice && !error && <Notice kind="info">{notice}</Notice>}
          {error && <Notice kind="error">{error}</Notice>}
          <ErrorSummary errors={summary} />

          <form onSubmit={handleSubmit} noValidate className="stack">
            {field('username', 'Username', 'text', 'username')}
            {field('password', 'Password', 'password', 'current-password')}
            <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="login-note">Accounts are set up by your system administrator.</p>
          <p className="login-note"><Link to="/">What is OcuLubak?</Link></p>
        </div>
      </main>
    </div>
  );
}

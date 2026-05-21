import { useState } from 'react';
import { authAPI } from '../api';

// Only these roles are available for self-registration.
// Admin, DPWH, and Provincial roles must be assigned by an existing admin.
const SELF_REGISTER_ROLES = [
  { value: 'public', label: 'General Public' },
  { value: 'barangay', label: 'Barangay LGU' },
  { value: 'municipal', label: 'Municipal Government' },
  { value: 'inspector', label: 'Inspector' },
];

// Roles that require ID verification
const APPROVAL_ROLES = ['barangay', 'municipal', 'inspector'];

export default function LoginPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({
    username: '', password: '', full_name: '', lgu_name: '',
    role: 'public', agency: '', email: '',
  });
  const [idFile, setIdFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingMessage, setPendingMessage] = useState('');

  const needsApproval = APPROVAL_ROLES.includes(form.role);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setPendingMessage('');
    setLoading(true);

    try {
      if (isRegister) {
        // For government roles, require ID file and use FormData
        if (needsApproval) {
          if (!idFile) {
            setError('Please upload your government ID to verify your identity.');
            setLoading(false);
            return;
          }

          const formData = new FormData();
          formData.append('username', form.username);
          formData.append('password', form.password);
          formData.append('full_name', form.full_name);
          formData.append('lgu_name', form.lgu_name);
          formData.append('role', form.role);
          formData.append('agency', form.agency);
          formData.append('email', form.email);
          formData.append('id_photo', idFile);

          const res = await authAPI.register(formData);

          // Account is pending — show message instead of logging in
          if (res.data.account_status === 'pending') {
            setPendingMessage(res.data.message);
            setIsRegister(false);
            setForm({ username: '', password: '', full_name: '', lgu_name: '', role: 'public', agency: '', email: '' });
            setIdFile(null);
          } else {
            onLogin(res.data.user);
          }
        } else {
          // Public users — normal JSON registration, instant access
          const res = await authAPI.register(form);
          onLogin(res.data.user);
        }
      } else {
        const res = await authAPI.login(form.username, form.password);
        onLogin(res.data.user);
      }
    } catch (err) {
      const errData = err.response?.data;
      if (errData?.account_status === 'pending') {
        setPendingMessage(errData.error);
      } else if (errData?.account_status === 'rejected') {
        setError(errData.error);
      } else {
        setError(errData?.error || 'Something went wrong');
      }
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
          <p className="subtitle">Road Damage Detection & Infrastructure Monitoring</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {pendingMessage && (
          <div className="alert" style={{
            background: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            color: 'var(--text-primary)',
            borderRadius: '10px',
            padding: '16px',
            marginBottom: '16px',
            fontSize: '13px',
            lineHeight: '1.5',
          }}>
            <div style={{ fontSize: '20px', marginBottom: '8px' }}>📋</div>
            <strong>Registration Submitted!</strong>
            <p style={{ margin: '8px 0 0', color: 'var(--text-secondary)' }}>{pendingMessage}</p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <div className="input-group">
                <label>Full Name</label>
                <input className="input-field" type="text" value={form.full_name}
                  onChange={updateField('full_name')} placeholder="Juan Dela Cruz" required />
              </div>
              <div className="input-group">
                <label>Organization / LGU</label>
                <input className="input-field" type="text" value={form.lgu_name}
                  onChange={updateField('lgu_name')} placeholder="Municipality of..." required />
              </div>
              <div className="input-group">
                <label>Role</label>
                <select className="input-field" value={form.role} onChange={updateField('role')}>
                  {SELF_REGISTER_ROLES.map(r => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </div>

              {/* ID photo upload — required for government roles */}
              {needsApproval && (
                <div className="input-group">
                  <label>
                    Government ID Photo <span style={{ color: 'var(--severity-high)' }}>*</span>
                  </label>
                  <p style={{ fontSize: '11px', color: 'var(--text-secondary)', margin: '0 0 6px' }}>
                    Upload a valid government ID to verify your identity. Your account will be reviewed by an administrator.
                  </p>
                  <input
                    className="input-field"
                    type="file"
                    accept=".jpg,.jpeg,.png,.pdf"
                    onChange={(e) => setIdFile(e.target.files[0])}
                    style={{ padding: '8px' }}
                    required
                  />
                  {idFile && (
                    <div style={{ fontSize: '11px', color: 'var(--accent)', marginTop: '4px' }}>
                      ✅ {idFile.name} ({(idFile.size / 1024).toFixed(0)} KB)
                    </div>
                  )}
                </div>
              )}

              {needsApproval && (
                <div style={{
                  background: 'rgba(245, 158, 11, 0.1)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  borderRadius: '8px',
                  padding: '10px 12px',
                  marginBottom: '12px',
                  fontSize: '11px',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.5',
                }}>
                  ⚠️ <strong>Note:</strong> Accounts for government roles require administrator approval.
                  Your account will be reviewed before you can log in.
                </div>
              )}

              <div className="input-group">
                <label>Agency (optional)</label>
                <input className="input-field" type="text" value={form.agency}
                  onChange={updateField('agency')} placeholder="e.g., DPWH Region IV-A" />
              </div>
              <div className="input-group">
                <label>Email (optional)</label>
                <input className="input-field" type="email" value={form.email}
                  onChange={updateField('email')} placeholder="email@example.com" />
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
            {loading ? <span className="spinner" /> : (
              isRegister
                ? (needsApproval ? 'Submit for Verification' : 'Create Account')
                : 'Sign In'
            )}
          </button>
        </form>

        <div className="login-footer">
          {isRegister ? (
            <p>Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(false); setPendingMessage(''); setError(''); }}>Sign in</a></p>
          ) : (
            <p>Need an account? <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(true); setPendingMessage(''); setError(''); }}>Register</a></p>
          )}
        </div>
      </div>
    </div>
  );
}

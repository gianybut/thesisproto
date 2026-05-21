import { useState, useEffect } from 'react';
import { accountsAPI } from '../api';

const ROLE_LABELS = {
  admin: 'System Admin',
  dpwh: 'DPWH',
  provincial: 'Provincial',
  municipal: 'Municipal',
  barangay: 'Barangay',
  public: 'Public',
  inspector: 'Inspector',
};

const STATUS_STYLES = {
  active: { bg: 'rgba(34, 197, 94, 0.15)', color: '#22c55e', label: '✅ Active' },
  pending: { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', label: '⏳ Pending' },
  rejected: { bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', label: '❌ Rejected' },
};

export default function AccountsPage() {
  const [accounts, setAccounts] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');
  const [rejectDialog, setRejectDialog] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(null);
  const [previewImage, setPreviewImage] = useState(null);

  const fetchData = async () => {
    try {
      const [accountsRes, statsRes] = await Promise.all([
        accountsAPI.getAll(filter),
        accountsAPI.getStats(),
      ]);
      setAccounts(accountsRes.data.accounts || []);
      setStats(statsRes.data || {});
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [filter]);

  const handleApprove = async (userId) => {
    setActionLoading(userId);
    try {
      await accountsAPI.approve(userId);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to approve account');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async () => {
    if (!rejectDialog) return;
    setActionLoading(rejectDialog.id);
    try {
      await accountsAPI.reject(rejectDialog.id, rejectReason || 'Registration rejected by administrator');
      setRejectDialog(null);
      setRejectReason('');
      fetchData();
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to reject account');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>;

  return (
    <div className="page fade-in" style={{ padding: '16px 32px' }}>
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div>
          <h2>👤 Account Management</h2>
          <p>Review and approve account registrations</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
        {[
          { label: 'Pending', value: stats.pending || 0, color: '#f59e0b', filterVal: 'pending' },
          { label: 'Active', value: stats.active || 0, color: '#22c55e', filterVal: 'active' },
          { label: 'Rejected', value: stats.rejected || 0, color: '#ef4444', filterVal: 'rejected' },
          { label: 'Total', value: stats.total || 0, color: 'var(--accent)', filterVal: '' },
        ].map(s => (
          <div
            key={s.label}
            onClick={() => setFilter(s.filterVal)}
            className="glass-card"
            style={{
              padding: '16px', textAlign: 'center', cursor: 'pointer',
              border: filter === s.filterVal ? `2px solid ${s.color}` : '2px solid transparent',
              transition: 'border-color 0.2s',
            }}
          >
            <div style={{ fontSize: '28px', fontWeight: '800', color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '600' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Account List */}
      {accounts.length === 0 ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>
            {filter === 'pending' ? '✅' : '📋'}
          </div>
          <h3>No {filter || ''} accounts</h3>
          <p style={{ color: 'var(--text-secondary)' }}>
            {filter === 'pending'
              ? 'All registration requests have been processed.'
              : 'No accounts found with this status.'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '12px' }}>
          {accounts.map(account => {
            const statusStyle = STATUS_STYLES[account.account_status] || STATUS_STYLES.pending;
            return (
              <div key={account.id} className="glass-card" style={{ padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>

                  {/* Left: User Info */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                      <div style={{
                        width: '40px', height: '40px', borderRadius: '50%',
                        background: 'var(--accent)', color: '#fff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '16px', fontWeight: '700', flexShrink: 0,
                      }}>
                        {account.full_name?.[0] || 'U'}
                      </div>
                      <div>
                        <div style={{ fontWeight: '700', fontSize: '15px' }}>{account.full_name}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>@{account.username}</div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
                      <span className={`role-badge ${account.role}`}>
                        {ROLE_LABELS[account.role] || account.role}
                      </span>
                      <span style={{
                        padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '600',
                        background: statusStyle.bg, color: statusStyle.color,
                      }}>
                        {statusStyle.label}
                      </span>
                    </div>

                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      <span>🏢 {account.lgu_name}</span>
                      {account.agency && <span>🏛️ {account.agency}</span>}
                      {account.email && <span>📧 {account.email}</span>}
                      <span>📅 {new Date(account.created_at).toLocaleDateString('en-US', {
                        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                      })}</span>
                    </div>

                    {account.rejection_reason && (
                      <div style={{
                        marginTop: '8px', padding: '8px 10px', borderRadius: '6px',
                        background: 'rgba(239, 68, 68, 0.1)', fontSize: '12px',
                        color: '#ef4444', lineHeight: '1.4',
                      }}>
                        <strong>Rejection reason:</strong> {account.rejection_reason}
                      </div>
                    )}
                  </div>

                  {/* Right: ID Photo + Actions */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                    {account.id_photo && (
                      <div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px', textAlign: 'center' }}>
                          Government ID
                        </div>
                        {account.id_photo.endsWith('.pdf') ? (
                          <a
                            href={accountsAPI.idPhotoUrl(account.id_photo)}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              display: 'block', width: '120px', height: '80px', borderRadius: '8px',
                              background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: '12px', color: 'var(--accent)', textDecoration: 'none',
                            }}
                          >
                            📄 View PDF
                          </a>
                        ) : (
                          <img
                            src={accountsAPI.idPhotoUrl(account.id_photo)}
                            alt="Government ID"
                            onClick={() => setPreviewImage(accountsAPI.idPhotoUrl(account.id_photo))}
                            style={{
                              width: '120px', height: '80px', objectFit: 'cover', borderRadius: '8px',
                              border: '1px solid var(--border)', cursor: 'pointer',
                              transition: 'transform 0.2s',
                            }}
                            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
                            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
                          />
                        )}
                      </div>
                    )}

                    {account.account_status === 'pending' && (
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => handleApprove(account.id)}
                          disabled={actionLoading === account.id}
                          style={{ padding: '4px 12px', fontSize: '11px' }}
                        >
                          {actionLoading === account.id ? '...' : '✅ Approve'}
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => setRejectDialog(account)}
                          disabled={actionLoading === account.id}
                          style={{ padding: '4px 12px', fontSize: '11px', color: '#ef4444' }}
                        >
                          ❌ Reject
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Reject Dialog */}
      {rejectDialog && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }} onClick={() => setRejectDialog(null)}>
          <div className="glass-card" style={{ padding: '24px', width: '400px', maxWidth: '90vw' }}
            onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: '12px' }}>Reject Account</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              Rejecting registration for <strong>{rejectDialog.full_name}</strong> ({ROLE_LABELS[rejectDialog.role]}).
            </p>
            <div className="input-group">
              <label>Reason for Rejection</label>
              <textarea
                className="input-field"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="e.g., Invalid ID, unverifiable identity..."
                rows={3}
                style={{ resize: 'vertical' }}
              />
            </div>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '12px' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setRejectDialog(null)}>Cancel</button>
              <button className="btn btn-primary btn-sm" onClick={handleReject}
                style={{ background: '#ef4444' }}>
                Reject Account
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Image Preview Modal */}
      {previewImage && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1001,
          cursor: 'pointer',
        }} onClick={() => setPreviewImage(null)}>
          <img
            src={previewImage}
            alt="ID Photo Preview"
            style={{ maxWidth: '90vw', maxHeight: '90vh', borderRadius: '12px', boxShadow: '0 20px 60px rgba(0,0,0,0.5)' }}
          />
        </div>
      )}
    </div>
  );
}

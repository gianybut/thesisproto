import { useState, useEffect } from 'react';
import { reportsAPI } from '../api';

export default function ReportsManagementPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pending');

  const fetchReports = (status) => {
    setLoading(true);
    reportsAPI.list(status || '').then(res => {
      setReports(res.data.reports || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => { fetchReports(activeTab === 'all' ? '' : activeTab); }, [activeTab]);

  const handleValidate = async (id) => {
    if (!confirm('Validate this report and add it to the damage database?')) return;
    await reportsAPI.validate(id);
    fetchReports(activeTab === 'all' ? '' : activeTab);
  };

  const handleReject = async (id) => {
    const reason = prompt('Enter rejection reason (optional):');
    if (reason === null) return;
    await reportsAPI.reject(id, reason);
    fetchReports(activeTab === 'all' ? '' : activeTab);
  };

  const TABS = [
    { key: 'pending', label: 'Pending', icon: '⏳' },
    { key: 'validated', label: 'Validated', icon: '✅' },
    { key: 'rejected', label: 'Rejected', icon: '❌' },
    { key: 'all', label: 'All', icon: '📋' },
  ];

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h2>📋 Public Reports Management</h2>
        <p>Review and validate citizen-submitted road damage reports</p>
      </div>

      <div className="tabs">
        {TABS.map(tab => (
          <div key={tab.key} className={`tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}>
            {tab.icon} {tab.label}
          </div>
        ))}
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px' }}><div className="spinner" /></div>
      ) : reports.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>No {activeTab} reports</h3>
          <p>Public reports will appear here when citizens submit damage sightings</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>
          {reports.map(r => (
            <div key={r.id} className="glass-card" style={{ padding: '20px' }}>
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span className={`badge badge-${r.status}`}>{r.status}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  #{r.id} • {new Date(r.created_at).toLocaleDateString()}
                </span>
              </div>

              {/* Image */}
              {r.image_filename && (
                <div style={{ marginBottom: '12px', borderRadius: '8px', overflow: 'hidden', height: '150px', background: 'var(--bg-secondary)' }}>
                  <img
                    src={reportsAPI.imageUrl(r.image_filename)}
                    alt="Damage"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                </div>
              )}

              {/* Details */}
              <div style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
                  <span className={`damage-badge damage-${r.damage_type}`}>{r.damage_type}</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{r.damage_label}</span>
                </div>

                {r.reporter_name && (
                  <div style={{ fontSize: '13px', marginBottom: '4px' }}>
                    👤 {r.reporter_name}
                  </div>
                )}

                {r.description && (
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px', lineHeight: '1.4' }}>
                    {r.description}
                  </p>
                )}

                {r.latitude && r.longitude && (
                  <div style={{ fontSize: '12px', color: 'var(--teal)' }}>
                    📍 {r.latitude.toFixed(6)}, {r.longitude.toFixed(6)}
                  </div>
                )}
                {r.manual_location && (
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    📍 {r.manual_location}
                  </div>
                )}
              </div>

              {/* Actions */}
              {r.status === 'pending' && (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-success btn-sm" style={{ flex: 1 }}
                    onClick={() => handleValidate(r.id)}>
                    ✅ Validate
                  </button>
                  <button className="btn btn-danger btn-sm" style={{ flex: 1 }}
                    onClick={() => handleReject(r.id)}>
                    ❌ Reject
                  </button>
                </div>
              )}

              {r.status === 'rejected' && r.rejection_reason && (
                <div className="alert alert-error" style={{ marginTop: '8px', padding: '8px 12px', fontSize: '12px' }}>
                  Reason: {r.rejection_reason}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

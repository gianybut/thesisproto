import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboardAPI } from '../api';

const DAMAGE_COLORS = {
  D10: '#ffa500', D20: '#eab308', D30: '#ef4444', D40: '#ff8c00',
};

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    dashboardAPI.stats().then(res => { setStats(res.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="page" style={{display:'flex',alignItems:'center',justifyContent:'center'}}><div className="spinner" /></div>;

  const s = stats || {};
  const maxTypeCount = Math.max(...(s.by_damage_type || []).map(d => d.count), 1);
  const totalSeverity = (s.by_severity?.high || 0) + (s.by_severity?.medium || 0) + (s.by_severity?.low || 0);

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Road damage detection overview and infrastructure monitoring</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📹</div>
          <div className="stat-value">{s.total_videos || 0}</div>
          <div className="stat-label">Total Videos</div>
        </div>
        <div className="stat-card success">
          <div className="stat-icon">⚠️</div>
          <div className="stat-value">{s.total_detections || 0}</div>
          <div className="stat-label">Damages Detected</div>
        </div>
        <div className="stat-card warning">
          <div className="stat-icon">🎯</div>
          <div className="stat-value">{s.avg_confidence ? (s.avg_confidence * 100).toFixed(1) + '%' : '—'}</div>
          <div className="stat-label">Avg Confidence</div>
        </div>
        <div className="stat-card purple">
          <div className="stat-icon">📍</div>
          <div className="stat-value">{s.geolocated_count || 0}</div>
          <div className="stat-label">Geo-located</div>
        </div>
        <div className="stat-card danger">
          <div className="stat-icon">📱</div>
          <div className="stat-value">{s.pending_reports || 0}</div>
          <div className="stat-label">Pending Reports</div>
        </div>
      </div>

      <div className="two-col">
        {/* Left column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Damage Type Distribution */}
          <div className="glass-card">
            <h3 style={{ fontSize: '16px', marginBottom: '16px' }}>Damage Type Distribution</h3>
            {(s.by_damage_type && s.by_damage_type.length > 0) ? (
              s.by_damage_type.map(d => (
                <div className="dist-bar" key={d.type}>
                  <span className={`damage-badge damage-${d.type}`}>{d.type}</span>
                  <span className="dist-bar-label">{d.label}</span>
                  <div className="dist-bar-track">
                    <div className="dist-bar-fill" style={{
                      width: `${(d.count / maxTypeCount) * 100}%`,
                      background: DAMAGE_COLORS[d.type] || 'var(--accent)',
                    }} />
                  </div>
                  <span className="dist-bar-value">{d.count}</span>
                </div>
              ))
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No detections yet</p>
            )}
          </div>

          {/* Severity Overview */}
          <div className="glass-card">
            <h3 style={{ fontSize: '16px', marginBottom: '16px' }}>Severity Distribution</h3>
            {totalSeverity > 0 ? (
              <>
                {['high', 'medium', 'low'].map(level => {
                  const count = s.by_severity?.[level] || 0;
                  const pct = totalSeverity > 0 ? (count / totalSeverity) * 100 : 0;
                  const colors = { high: 'var(--severity-high)', medium: 'var(--severity-medium)', low: 'var(--severity-low)' };
                  return (
                    <div className="dist-bar" key={level}>
                      <span className={`severity-badge severity-${level}`}>{level}</span>
                      <div className="dist-bar-track">
                        <div className="dist-bar-fill" style={{ width: `${pct}%`, background: colors[level] }} />
                      </div>
                      <span className="dist-bar-value">{count}</span>
                    </div>
                  );
                })}
              </>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No severity data available</p>
            )}
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Quick Actions */}
          <div className="glass-card">
            <h3 style={{ fontSize: '16px', marginBottom: '16px' }}>Quick Actions</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button className="btn btn-primary" onClick={() => navigate('/upload')}>📤 Upload Road Survey</button>
              <button className="btn btn-secondary" onClick={() => navigate('/map')}>🗺️ View Damage Map</button>
              <button className="btn btn-secondary" onClick={() => navigate('/database')}>🗃️ Damage Database</button>
              <button className="btn btn-secondary" onClick={() => navigate('/videos')}>📂 Video Library</button>
            </div>
          </div>

          {/* Status Overview */}
          <div className="glass-card">
            <h3 style={{ fontSize: '16px', marginBottom: '16px' }}>Maintenance Status</h3>
            {s.by_status && Object.keys(s.by_status).length > 0 ? (
              Object.entries(s.by_status).map(([status, count]) => (
                <div key={status} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '13px', textTransform: 'capitalize' }}>{status.replace('_', ' ')}</span>
                  <span style={{ fontSize: '13px', fontWeight: '600' }}>{count}</span>
                </div>
              ))
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No status data</p>
            )}
          </div>

          {/* Recent Videos */}
          <div className="glass-card">
            <h3 style={{ fontSize: '16px', marginBottom: '16px' }}>Recent Videos</h3>
            {s.recent_videos?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {s.recent_videos.map(v => (
                  <div key={v.id} onClick={() => navigate(`/videos/${v.id}`)}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: '8px', background: 'var(--bg-glass)', cursor: 'pointer', border: '1px solid var(--border-glass)' }}>
                    <span style={{ fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>
                      {v.has_gps && '📍 '}{v.original_filename}
                    </span>
                    <span className={`badge badge-${v.status}`}>{v.status}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No videos uploaded yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

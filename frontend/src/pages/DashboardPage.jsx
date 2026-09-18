import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboardAPI } from '../api';

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
      </div>

      <div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Quick Actions */}
          <div className="panel">
            <h3 style={{ fontSize: '16px', marginBottom: '16px' }}>Quick Actions</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button className="btn btn-primary" onClick={() => navigate('/upload')}>Upload Road Survey</button>
              <button className="btn btn-secondary" onClick={() => navigate('/map')}>View Damage Map</button>
              <button className="btn btn-secondary" onClick={() => navigate('/database')}>Damage Database</button>
              <button className="btn btn-secondary" onClick={() => navigate('/videos')}>Video Library</button>
            </div>
          </div>

          {/* Status Overview */}
          <div className="panel">
            <h3 style={{ fontSize: '16px', marginBottom: '16px' }}>Maintenance Status</h3>
            {s.by_status && Object.keys(s.by_status).length > 0 ? (
              Object.entries(s.by_status).map(([status, count]) => (
                <div key={status} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--rule)' }}>
                  <span style={{ fontSize: '13px', textTransform: 'capitalize' }}>{status.replace('_', ' ')}</span>
                  <span style={{ fontSize: '13px', fontWeight: '600' }}>{count}</span>
                </div>
              ))
            ) : (
              <p style={{ color: 'var(--ink-soft)', fontSize: '14px' }}>No status data</p>
            )}
          </div>

          {/* Recent Videos */}
          <div className="panel">
            <h3 style={{ fontSize: '16px', marginBottom: '16px' }}>Recent Videos</h3>
            {s.recent_videos?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {s.recent_videos.map(v => (
                  <div key={v.id} onClick={() => navigate(`/videos/${v.id}`)}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: '8px', background: 'var(--card)', cursor: 'pointer', border: '1px solid var(--rule)' }}>
                    <span style={{ fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>
                      {v.name || v.original_filename}
                    </span>
                    <span className={`badge badge-${v.status}`}>{v.status}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--ink-soft)', fontSize: '14px' }}>No videos uploaded yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

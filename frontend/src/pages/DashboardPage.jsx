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
        <p>Overview of road inspection activities and pothole detections</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📹</div>
          <div className="stat-value">{s.total_videos || 0}</div>
          <div className="stat-label">Total Videos</div>
        </div>
        <div className="stat-card success">
          <div className="stat-icon">🕳️</div>
          <div className="stat-value">{s.total_detections || 0}</div>
          <div className="stat-label">Potholes Detected</div>
        </div>
        <div className="stat-card warning">
          <div className="stat-icon">🎯</div>
          <div className="stat-value">{s.avg_confidence ? (s.avg_confidence * 100).toFixed(1) + '%' : '—'}</div>
          <div className="stat-label">Avg Confidence</div>
        </div>
        <div className="stat-card purple">
          <div className="stat-icon">⏱️</div>
          <div className="stat-value">{s.total_duration ? (s.total_duration / 60).toFixed(1) + 'm' : '0m'}</div>
          <div className="stat-label">Video Processed</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="glass-card">
          <h3 style={{ marginBottom: '16px', fontSize: '16px' }}>Quick Actions</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button className="btn btn-primary" onClick={() => navigate('/upload')}>📤 Upload New Video</button>
            <button className="btn btn-secondary" onClick={() => navigate('/videos')}>📂 View All Videos</button>
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ marginBottom: '16px', fontSize: '16px' }}>Recent Videos</h3>
          {s.recent_videos?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {s.recent_videos.map(v => (
                <div key={v.id} onClick={() => navigate(`/videos/${v.id}`)}
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: '8px', background: 'var(--bg-glass)', cursor: 'pointer', border: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>{v.original_filename}</span>
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
  );
}

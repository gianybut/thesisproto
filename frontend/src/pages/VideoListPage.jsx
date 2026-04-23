import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { videosAPI } from '../api';

export default function VideoListPage() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchVideos = () => {
    videosAPI.list().then(res => { setVideos(res.data.videos); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchVideos();
    const interval = setInterval(fetchVideos, 5000); // Poll for status updates
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!confirm('Delete this video and all detections?')) return;
    await videosAPI.delete(id);
    fetchVideos();
  };

  const formatDuration = (s) => {
    if (!s) return '—';
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, '0')}`;
  };

  const formatSize = (bytes) => {
    if (!bytes) return '—';
    if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  };

  if (loading) return <div className="page" style={{display:'flex',alignItems:'center',justifyContent:'center'}}><div className="spinner" /></div>;

  return (
    <div className="page fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Video Library</h2>
          <p>{videos.length} video{videos.length !== 1 ? 's' : ''} uploaded</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/upload')}>📤 Upload New</button>
      </div>

      {videos.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📹</div>
          <h3>No videos yet</h3>
          <p>Upload your first road survey video to get started</p>
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>Upload Video</button>
        </div>
      ) : (
        <div className="video-grid">
          {videos.map((v, i) => (
            <div key={v.id} className="video-card fade-in" style={{ animationDelay: `${i * 0.05}s` }}
              onClick={() => navigate(`/videos/${v.id}`)}>
              <div className="video-thumb">
                🎬
                {v.status === 'processing' && (
                  <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0 }}>
                    <div className="progress-bar" style={{ borderRadius: 0 }}>
                      <div className="progress-fill" style={{ width: `${v.processing_progress}%` }} />
                    </div>
                  </div>
                )}
                <div className="play-overlay"><span style={{ fontSize: '36px' }}>▶</span></div>
              </div>
              <div className="video-info">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h3>{v.original_filename}</h3>
                  <span className={`badge badge-${v.status}`}>{v.status}</span>
                </div>
                <div className="video-meta">
                  <span>⏱ {formatDuration(v.duration)}</span>
                  <span>📦 {formatSize(v.file_size)}</span>
                  {v.total_detections > 0 && <span>🕳️ {v.total_detections} potholes</span>}
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
                  <button className="btn btn-danger btn-sm" onClick={(e) => handleDelete(e, v.id)}>🗑 Delete</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

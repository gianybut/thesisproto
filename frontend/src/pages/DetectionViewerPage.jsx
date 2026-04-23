import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { videosAPI, detectionsAPI } from '../api';

export default function DetectionViewerPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef();
  const [video, setVideo] = useState(null);
  const [detections, setDetections] = useState([]);
  const [activeDetection, setActiveDetection] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    videosAPI.get(id).then(res => {
      setVideo(res.data.video);
      setDetections(res.data.detections || []);
      setLoading(false);
    }).catch(() => { setLoading(false); navigate('/videos'); });
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [id]);

  const jumpToTimestamp = (detection) => {
    setActiveDetection(detection.id);
    if (videoRef.current) {
      videoRef.current.currentTime = detection.timestamp;
      videoRef.current.play();
    }
  };

  if (loading) return <div className="page" style={{display:'flex',alignItems:'center',justifyContent:'center'}}><div className="spinner" /></div>;
  if (!video) return null;

  const isProcessing = video.status === 'processing';
  const isCompleted = video.status === 'completed';
  const videoSrc = isCompleted ? videosAPI.processedUrl(video.id) : videosAPI.streamUrl(video.id);

  return (
    <div className="page fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '22px' }}>{video.original_filename}</h2>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginTop: '4px' }}>
            <span className={`badge badge-${video.status}`}>{video.status}</span>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{video.resolution} • {video.fps?.toFixed(0)} fps</span>
          </div>
        </div>
        <button className="btn btn-secondary" onClick={() => navigate('/videos')}>← Back</button>
      </div>

      {isProcessing && (
        <div className="glass-card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span>🔄 Processing video... Detecting potholes</span>
            <span style={{ color: 'var(--accent)' }}>{video.processing_progress?.toFixed(0)}%</span>
          </div>
          <div className="progress-bar"><div className="progress-fill" style={{ width: `${video.processing_progress}%` }} /></div>
        </div>
      )}

      <div className="viewer-layout">
        <div className="viewer-video glass-card" style={{ padding: 0 }}>
          <video ref={videoRef} src={videoSrc} controls style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
        </div>

        <div className="detection-panel">
          <div className="glass-card" style={{ padding: '16px' }}>
            <h3 style={{ fontSize: '16px', marginBottom: '4px' }}>Detection Log</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              {detections.length} pothole{detections.length !== 1 ? 's' : ''} found
            </p>
          </div>

          <div className="detection-list">
            {detections.length === 0 ? (
              <div className="empty-state" style={{ padding: '40px 20px' }}>
                <div className="empty-icon" style={{ fontSize: '40px' }}>
                  {isProcessing ? '⏳' : '✨'}
                </div>
                <h3 style={{ fontSize: '15px' }}>
                  {isProcessing ? 'Processing...' : 'No detections'}
                </h3>
                <p style={{ fontSize: '13px' }}>
                  {isProcessing ? 'Detections will appear here as the video is analyzed' : 'No potholes were found in this video'}
                </p>
              </div>
            ) : (
              detections.map((d, i) => (
                <div key={d.id}
                  className={`detection-item fade-in ${activeDetection === d.id ? 'active' : ''}`}
                  style={{ animationDelay: `${i * 0.03}s` }}
                  onClick={() => jumpToTimestamp(d)}>
                  <div>
                    <div className="detection-time">{d.timestamp_formatted}</div>
                    <div className="detection-conf">
                      Confidence: {(d.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div style={{ flex: 1 }} />
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Frame #{d.frame_number}</span>
                    <div className="detection-conf-bar">
                      <div className="detection-conf-fill" style={{
                        width: `${d.confidence * 100}%`,
                        background: d.confidence > 0.7 ? 'var(--success)' : d.confidence > 0.5 ? 'var(--warning)' : 'var(--danger)'
                      }} />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

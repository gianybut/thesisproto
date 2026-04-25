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
  const [videoError, setVideoError] = useState(null);

  const fetchData = () => {
    videosAPI.get(id).then(res => {
      console.log('Video data:', res.data.video);
      setVideo(res.data.video);
      setDetections(res.data.detections || []);
      setLoading(false);
    }).catch((err) => { 
      console.error('Failed to fetch video:', err);
      setLoading(false); 
      navigate('/videos'); 
    });
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      fetchData();
    }, 2000); // Poll every 2 seconds while processing
    return () => clearInterval(interval);
  }, [id]);

  const jumpToTimestamp = (detection) => {
    console.log(`🎯 Clicking detection: ${detection.timestamp_formatted} (${detection.timestamp}s), Frame ${detection.frame_number}`);
    setActiveDetection(detection.id);
    
    if (!videoRef.current) {
      console.error('❌ Video ref not available');
      return;
    }

    // Pause the video first
    videoRef.current.pause();
    
    // Set the current time to seek to the frame with the bounding box
    videoRef.current.currentTime = detection.timestamp;
    console.log(`⏸️  Paused at ${detection.timestamp}s with bounding box visible`);
  };

  const handleVideoError = (e) => {
    console.error('Video error:', e);
    setVideoError(`Video error: ${e.target.error?.message || 'Unknown error'}`);
  };

  const handleVideoLoadStart = () => {
    console.log('Video loading started');
    setVideoError(null);
  };

  const handleVideoCanPlay = () => {
    console.log('Video can play');
  };

  if (loading) return <div className="page" style={{display:'flex',alignItems:'center',justifyContent:'center'}}><div className="spinner" /></div>;
  if (!video) return null;

  const isProcessing = video.status === 'processing';
  const isCompleted = video.status === 'completed';
  const videoSrc = isCompleted ? videosAPI.processedUrl(video.id) : videosAPI.streamUrl(video.id);
  
  console.log('Rendering with status:', video.status, 'Video src:', videoSrc);

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

      {videoError && (
        <div className="glass-card" style={{ marginBottom: '24px', padding: '16px', background: 'rgba(255, 0, 0, 0.1)', borderLeft: '4px solid var(--danger)' }}>
          <p style={{ color: 'var(--danger)' }}>❌ {videoError}</p>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Video URL: {videoSrc}</p>
        </div>
      )}

      <div className="viewer-layout">
        <div className="viewer-video glass-card" style={{ padding: 0, minHeight: '400px' }}>
          {videoSrc ? (
            <video 
              key={videoSrc}
              ref={videoRef} 
              src={videoSrc}
              controls
              preload="metadata"
              crossOrigin="anonymous"
              onError={handleVideoError}
              onLoadStart={handleVideoLoadStart}
              onCanPlay={handleVideoCanPlay}
              style={{ width: '100%', height: '100%', objectFit: 'contain' }} 
            />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
              <p style={{ color: 'var(--text-muted)' }}>No video source available</p>
            </div>
          )}
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
                  style={{ animationDelay: `${i * 0.03}s`, cursor: 'pointer' }}
                  onClick={() => jumpToTimestamp(d)}
                  title={`Click to jump to ${d.timestamp_formatted}`}>
                  <div>
                    <div className="detection-time" style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                      ⏱️ {d.timestamp_formatted}
                    </div>
                    <div className="detection-conf" style={{ fontSize: '12px', marginTop: '4px' }}>
                      {(d.confidence * 100).toFixed(1)}% confidence
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Frame #{d.frame_number}
                    </div>
                  </div>
                  <div style={{ flex: 1 }} />
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                    <div className="detection-conf-bar" style={{ width: '60px' }}>
                      <div className="detection-conf-fill" style={{
                        width: `${d.confidence * 100}%`,
                        background: d.confidence > 0.7 ? 'var(--success)' : d.confidence > 0.5 ? 'var(--warning)' : 'var(--danger)',
                        height: '4px',
                        borderRadius: '2px'
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

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { videosAPI } from '../api';
import RenameVideo from '../components/RenameVideo';

export default function DetectionViewerPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const videoRef = useRef();
  const [video, setVideo] = useState(null);
  const [detections, setDetections] = useState([]);
  const [activeDetection, setActiveDetection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [videoError, setVideoError] = useState(null);
  const [filterType, setFilterType] = useState('');
  const [hasSeeked, setHasSeeked] = useState(false);

  const fetchData = () => {
    videosAPI.get(id).then(res => {
      setVideo(res.data.video);
      setDetections(res.data.detections || []);
      setLoading(false);
    }).catch(() => { setLoading(false); navigate('/videos'); });
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [id]);

  // Auto-seek to timestamp from URL (?t=seconds) when video is loaded
  const handleVideoLoaded = useCallback(() => {
    if (hasSeeked) return;
    const seekTime = searchParams.get('t');
    if (seekTime && videoRef.current) {
      const time = parseFloat(seekTime);
      if (!isNaN(time)) {
        videoRef.current.currentTime = time;
        videoRef.current.pause();
        setHasSeeked(true);
        // Find and highlight the matching detection
        const closest = detections.reduce((best, d) =>
          !best || Math.abs(d.timestamp - time) < Math.abs(best.timestamp - time) ? d : best,
          null
        );
        if (closest) setActiveDetection(closest.id);
      }
    }
  }, [searchParams, detections, hasSeeked]);

  const jumpToTimestamp = (detection) => {
    setActiveDetection(detection.id);
    if (!videoRef.current) return;
    videoRef.current.pause();
    videoRef.current.currentTime = detection.timestamp;
  };

  const handleVideoError = (e) => {
    setVideoError(`Video error: ${e.target.error?.message || 'Unknown error'}`);
  };

  if (loading) return <div className="page" style={{display:'flex',alignItems:'center',justifyContent:'center'}}><div className="spinner" /></div>;
  if (!video) return null;

  const isProcessing = video.status === 'processing';
  const isCompleted = video.status === 'completed';
  const videoSrc = isCompleted ? videosAPI.processedUrl(video.id) : videosAPI.streamUrl(video.id);

  // Filter detections
  let filtered = detections;
  if (filterType) filtered = filtered.filter(d => d.damage_type === filterType);

  // Stats
  const typeSet = [...new Set(detections.map(d => d.damage_type))];
  const gpsCount = detections.filter(d => d.latitude).length;

  return (
    <div className="page fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ minWidth: 0 }}>
          <RenameVideo video={video} as="h2" onRenamed={(updated) => setVideo(v => ({ ...v, ...updated }))} />
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: '4px', flexWrap: 'wrap' }}>
            <span className={`badge badge-${video.status}`}>{video.status}</span>
            <span style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>{video.resolution} • {video.fps?.toFixed(0)} fps</span>
            {video.has_gps && <span style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>🛰️ GPS synced</span>}
            {video.position_source === 'georeferenced' && <span style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>📍 Manually georeferenced ({video.control_point_count} points)</span>}
            {video.road_name && <span style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>📍 {video.road_name}</span>}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {!video.has_gps && (
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/videos/${video.id}/georeference`)}>📍 Georeference</button>
          )}
          {gpsCount > 0 && (
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/map?video=${video.id}`)}>View this survey on the map</button>
          )}
          <button className="btn btn-secondary" onClick={() => navigate('/videos')}>← Back</button>
        </div>
      </div>

      {isProcessing && (
        <div className="panel" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span>🔄 Processing video... Detecting road damages</span>
            <span style={{ color: 'var(--cyan)' }}>{video.processing_progress?.toFixed(0)}%</span>
          </div>
          <div className="progress-bar"><div className="progress-fill" style={{ width: `${video.processing_progress}%` }} /></div>
        </div>
      )}

      {videoError && (
        <div className="panel" style={{ marginBottom: '24px', padding: '16px', background: 'rgba(255, 0, 0, 0.1)', borderLeft: '4px solid var(--alert)' }}>
          <p style={{ color: 'var(--alert)' }}>❌ {videoError}</p>
        </div>
      )}

      <div className="viewer-layout">
        <div className="viewer-video panel" style={{ padding: 0, minHeight: '400px' }}>
          {videoSrc ? (
            <video
              key={videoSrc}
              ref={videoRef}
              src={videoSrc}
              controls
              preload="metadata"
              crossOrigin="anonymous"
              onError={handleVideoError}
              onLoadStart={() => setVideoError(null)}
              onLoadedMetadata={handleVideoLoaded}
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
              <p style={{ color: 'var(--ink-soft)' }}>No video source available</p>
            </div>
          )}
        </div>

        <div className="detection-panel">
          <div className="panel" style={{ padding: '16px' }}>
            <h3 style={{ fontSize: '16px', marginBottom: '8px' }}>Detection Log</h3>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', color: 'var(--ink-soft)' }}>
                {detections.length} damage{detections.length !== 1 ? 's' : ''} found
                {gpsCount > 0 &&<span style={{ color: 'var(--ink-soft)', marginLeft: '6px' }}>📍 {gpsCount} geo-located</span>}
              </span>
            </div>

            {/* Mini filters */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              <select className="input-field" style={{ padding: '4px 8px', fontSize: '11px', minWidth: '100px' }}
                value={filterType} onChange={e => setFilterType(e.target.value)}>
                <option value="">All Types</option>
                {typeSet.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <div className="detection-list">
            {filtered.length === 0 ? (
              <div className="empty-state" style={{ padding: '40px 20px' }}>
                <div className="empty-icon" style={{ fontSize: '40px' }}>
                  {isProcessing ? '⏳' : '✨'}
                </div>
                <h3 style={{ fontSize: '15px' }}>
                  {isProcessing ? 'Processing...' : 'No detections'}
                </h3>
                <p style={{ fontSize: '13px' }}>
                  {isProcessing ? 'Detections will appear as the video is analyzed' : 'No damages match the current filter'}
                </p>
              </div>
            ) : (
              filtered.map((d, i) => (
                <div key={d.id}
                  className={`detection-item fade-in ${activeDetection === d.id ? 'active' : ''}`}
                  style={{ animationDelay: `${i * 0.03}s`, cursor: 'pointer' }}
                  onClick={() => jumpToTimestamp(d)}
                  title={`Click to jump to ${d.timestamp_formatted}`}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                      <span className={`damage-badge damage-${d.damage_type}`}>{d.damage_type}</span>
                      <span style={{ fontSize: '12px', color: 'var(--ink-soft)' }}>{d.damage_label}</span>
                    </div>
                    <div className="detection-time">
                      ⏱️ {d.timestamp_formatted}
                    </div>
                    <div className="detection-conf" style={{ marginTop: '2px' }}>
                      {(d.confidence * 100).toFixed(1)}% confidence
                      {d.latitude && <span style={{ color: 'var(--ink-soft)', marginLeft: '6px' }}>📍</span>}
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                    <div className="detection-conf-bar" style={{ width: '60px' }}>
                      <div className="detection-conf-fill" style={{
                        width: `${d.confidence * 100}%`,
                        background: d.confidence > 0.7 ? 'var(--ink-soft)' : d.confidence > 0.5 ? 'var(--alert)' : 'var(--alert)',
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

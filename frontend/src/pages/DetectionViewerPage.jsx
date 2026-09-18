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
    setVideoError(e.target.error?.message || 'the browser could not decode the file');
  };

  // §9: skeleton rows at real row height, not a full-screen spinner.
  if (loading) {
    return (
      <div className="page">
        <div className="page-header"><h2>Survey</h2></div>
        <div className="viewer-layout">
          <div className="viewer-video panel skeleton" />
          <div className="detection-panel">
            {Array.from({ length: 8 }, (_, i) => (
              <div className="skeleton-row" key={i}>
                <div className="skeleton" style={{ width: '62px' }} />
                <div className="skeleton" style={{ flex: 1 }} />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }
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
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 'var(--s2)' }}>
        <div style={{ minWidth: 0 }}>
          <RenameVideo video={video} as="h2" onRenamed={(updated) => setVideo(v => ({ ...v, ...updated }))} />
          <div className="viewer-meta">
            <span className={`badge badge-${video.status}`}>{video.status}</span>
            <span className="mono">{video.resolution}</span>
            <span className="mono">{video.fps?.toFixed(0)} fps</span>
            {video.has_gps && <span className="mono">GPS synced</span>}
            {video.position_source === 'georeferenced' && (
              <span className="mono">Georeferenced from {video.control_point_count} points</span>
            )}
            {video.road_name && <span className="secondary">{video.road_name}</span>}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 'var(--s2)', flexShrink: 0 }}>
          {!video.has_gps && (
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/videos/${video.id}/georeference`)}>Georeference</button>
          )}
          {gpsCount > 0 && (
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/map?video=${video.id}`)}>View on the map</button>
          )}
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/videos')}>Back to surveys</button>
        </div>
      </div>

      {isProcessing && (
        <div className="panel" style={{ marginBottom: 'var(--s3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 'var(--s1)' }}>
            <span>Analysing the survey for road damage.</span>
            <span className="mono">{video.processing_progress?.toFixed(0)}%</span>
          </div>
          <div className="progress-bar"><div className="progress-fill" style={{ width: `${video.processing_progress}%` }} /></div>
        </div>
      )}

      {/* §9: name what failed and what to do about it. */}
      {videoError && (
        <div className="alert alert-error">
          <strong>This survey will not play.</strong>{' '}
          If processing has just finished the file may still be encoding — reload in a moment. If it
          keeps failing, the server may have kept the AVI because ffmpeg was not on its PATH.
          <div className="mono" style={{ marginTop: '6px' }}>{videoError}</div>
        </div>
      )}

      <div className="viewer-layout">
        <div className="viewer-video panel" style={{ padding: 0 }}>
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
            />
          ) : (
            <div className="viewer-video-empty">
              <p>This survey has no playable video yet.</p>
            </div>
          )}
        </div>

        <div className="detection-panel">
          <div className="panel detection-panel-head">
            <h3>Detection log</h3>
            <p className="secondary" style={{ margin: 0 }}>
              <span className="mono">{detections.length}</span>
              {detections.length === 1 ? ' detection' : ' detections'}
              {gpsCount > 0 && <>, <span className="mono">{gpsCount}</span> geo-located</>}
            </p>
            <div className="input-group" style={{ margin: 0 }}>
              <label htmlFor="damage-filter">Kind of damage</label>
              <select id="damage-filter" className="input-field"
                value={filterType} onChange={e => setFilterType(e.target.value)}>
                <option value="">All kinds</option>
                {typeSet.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          {filtered.length === 0 ? (
            /* §9: an invitation to act, not an apology. */
            <div className="empty-state">
              <h3>{isProcessing ? 'Nothing found yet' : filterType ? 'None of this kind' : 'No damage found'}</h3>
              <p>
                {isProcessing
                  ? 'Rows appear here as the video is analysed.'
                  : filterType
                    ? 'This survey has damage of other kinds.'
                    : 'The model found no road damage in this survey. Check the video plays, then try a survey with clearer road surface.'}
              </p>
              {filterType && !isProcessing && (
                <button className="btn btn-secondary" onClick={() => setFilterType('')}>Show all kinds</button>
              )}
            </div>
          ) : (
            <ul className="detection-list">
              {filtered.map(d => (
                <li key={d.id}>
                  <button
                    type="button"
                    className={`detection-item ${activeDetection === d.id ? 'active' : ''}`}
                    onClick={() => jumpToTimestamp(d)}
                    aria-current={activeDetection === d.id}
                    title={`Jump to ${d.timestamp_formatted}`}>
                    <span className="detection-time">{d.timestamp_formatted}</span>
                    <span className="damage-badge">{d.damage_type}</span>
                    <span className="detection-item-label">{d.damage_label}</span>
                    {d.latitude && <span className="eyebrow">GPS</span>}
                    <span className="detection-conf">{(d.confidence * 100).toFixed(1)}%</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

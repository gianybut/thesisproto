import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { videosAPI } from '../api';

// Must match backend/services/georeference_service.py
const PH_BOUNDS = { latMin: 4.5, latMax: 21.5, lonMin: 116.0, lonMax: 127.0 };
const MIN_POINTS = 2;
const DEFAULT_CENTER = [14.5995, 120.9842]; // Manila

const formatTime = (s, decimals = 1) => {
  if (s == null || isNaN(s)) return '—';
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(decimals);
  return `${m.toString().padStart(2, '0')}:${sec.padStart(decimals ? 3 + decimals : 2, '0')}`;
};

// Numbered teal pin so control points read differently from the damage dots on the damage map
const createNumberedIcon = (n) => L.divIcon({
  html: `<div style="width:26px;height:26px;border-radius:50%;background:#14b8a6;border:2px solid #fff;color:#fff;font:700 12px Inter,sans-serif;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,.4)">${n}</div>`,
  className: '',
  iconSize: [26, 26],
  iconAnchor: [13, 13],
});

// Mirrors validate_control_points() so the Save button can be disabled before hitting the API
function validatePoints(points, duration) {
  if (points.length < MIN_POINTS) return `Add at least ${MIN_POINTS} control points`;
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (i > 0 && p.video_time_s <= points[i - 1].video_time_s) {
      return `Point ${i + 1} (${formatTime(p.video_time_s)}) must be later than point ${i} (${formatTime(points[i - 1].video_time_s)})`;
    }
    if (duration && p.video_time_s > duration) return `Point ${i + 1} is past the end of the video`;
    if (p.latitude < PH_BOUNDS.latMin || p.latitude > PH_BOUNDS.latMax ||
        p.longitude < PH_BOUNDS.lonMin || p.longitude > PH_BOUNDS.lonMax) {
      return `Point ${i + 1} is outside the Philippines`;
    }
  }
  return null;
}

// Forward map clicks only while a control point is waiting for its coordinate
function ClickCapture({ active, onPick }) {
  useMapEvents({ click: (e) => { if (active) onPick(e.latlng); } });
  return null;
}

// Fit to the saved points once when they first arrive; don't re-fit on every add
function FitOnce({ points }) {
  const map = useMap();
  const done = useRef(false);
  useEffect(() => {
    if (done.current || points.length === 0) return;
    done.current = true;
    if (points.length === 1) map.setView([points[0].latitude, points[0].longitude], 16);
    else map.fitBounds(L.latLngBounds(points.map(p => [p.latitude, p.longitude])), { padding: [40, 40], maxZoom: 17 });
  }, [points, map]);
  return null;
}

export default function GeoreferencePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef();

  const [video, setVideo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [points, setPoints] = useState([]);        // sorted by video_time_s; saved ones carry an id
  const [pendingTime, setPendingTime] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [mediaDuration, setMediaDuration] = useState(0); // from the <video> element, fallback when metadata lacks duration
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState(null);
  const [error, setError] = useState('');
  const [videoError, setVideoError] = useState(null);

  const fetchAll = () => Promise.all([videosAPI.get(id), videosAPI.getControlPoints(id)])
    .then(([vRes, cpRes]) => {
      setVideo(vRes.data.video);
      setPoints(cpRes.data.control_points || []);
      setLoading(false);
    })
    .catch(() => { setLoading(false); navigate('/videos'); });

  useEffect(() => { fetchAll(); }, [id]);

  // Keep the status badge live while the pipeline is still running (Save is blocked until it finishes)
  useEffect(() => {
    if (video?.status !== 'processing') return;
    const interval = setInterval(() => videosAPI.get(id).then(r => setVideo(r.data.video)).catch(() => {}), 3000);
    return () => clearInterval(interval);
  }, [video?.status, id]);

  const isProcessing = video?.status === 'processing';
  const duration = video?.duration || mediaDuration || 0;
  const validationError = validatePoints(points, duration);
  const canSave = !validationError && !isProcessing && !saving && dirty;

  const startAddPoint = () => {
    const el = videoRef.current;
    if (!el) return;
    el.pause();
    const t = el.currentTime;
    if (points.some(p => Math.abs(p.video_time_s - t) < 0.05)) {
      setError(`A control point already exists at ${formatTime(t)}`);
      return;
    }
    setError('');
    setSaveResult(null);
    setPendingTime(t);
  };

  const placePoint = (latlng) => {
    const next = [...points, { video_time_s: pendingTime, latitude: latlng.lat, longitude: latlng.lng }]
      .sort((a, b) => a.video_time_s - b.video_time_s);
    setPoints(next);
    setPendingTime(null);
    setDirty(true);
  };

  const removePoint = async (p) => {
    setError('');
    setSaveResult(null);
    if (!p.id) {
      setPoints(prev => prev.filter(x => x !== p));
      return;
    }
    try {
      const res = await videosAPI.deleteControlPoint(id, p.id);
      // Keep any unsaved local additions; replace the saved set with what the server now holds
      const unsaved = points.filter(x => !x.id);
      setPoints([...(res.data.control_points || []), ...unsaved].sort((a, b) => a.video_time_s - b.video_time_s));
      setVideo(res.data.video);
      setDirty(unsaved.length > 0);
    } catch (err) {
      setError(err.response?.data?.error || 'Delete failed');
    }
  };

  const handleSave = async () => {
    setSaving(true); setError(''); setSaveResult(null);
    try {
      const payload = points.map(({ video_time_s, latitude, longitude }) => ({ video_time_s, latitude, longitude }));
      const res = await videosAPI.saveControlPoints(id, payload);
      setPoints(res.data.control_points || []);
      setVideo(res.data.video);
      setSaveResult(res.data.applied);
      setDirty(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const seekTo = (t) => {
    if (!videoRef.current) return;
    videoRef.current.pause();
    videoRef.current.currentTime = t;
  };

  if (loading) return <div className="page" style={{display:'flex',alignItems:'center',justifyContent:'center'}}><div className="spinner" /></div>;
  if (!video) return null;

  const polyline = points.map(p => [p.latitude, p.longitude]);

  return (
    <div className="page fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '22px' }}>Place {video.name || video.original_filename} on the map</h2>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginTop: '4px', flexWrap: 'wrap' }}>
            <span className={`badge badge-${video.status}`}>{video.status}</span>
            <span style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>⏱ {formatTime(video.duration, 0)}</span>
            {video.position_source === 'georeferenced' && <span style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>📍 Georeferenced ({video.control_point_count} points)</span>}
            {video.road_name && <span style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>📍 {video.road_name}</span>}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary" onClick={() => navigate(`/videos/${id}`)}>← Back to Video</button>
        </div>
      </div>

      {video.has_gps ? (
        <div className="alert alert-warning">
          🛰️ This video already has a GPS track file — its detections are positioned from measured GPS data and cannot be manually georeferenced.
        </div>
      ) : (
        <>
          <div className="alert alert-info">
            💡 Scrub the video to a frame with a recognizable landmark (an intersection, a church, a bridge), press
            <strong> Add control point</strong>, then click that exact spot on the map. Repeat for {MIN_POINTS}–10 points spread across the
            drive. Detections are positioned <strong>between</strong> the two nearest control points, so add one wherever the vehicle
            stopped or turned. Detections before the first or after the last point will not be placed.
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {saveResult && (
            <div className="alert alert-success" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>✅ Saved — positioned {saveResult.positioned} of {saveResult.positioned + saveResult.unpositioned} detections
                {saveResult.unpositioned > 0 && ` (${saveResult.unpositioned} fall outside the control-point range)`}</span>
              {saveResult.positioned > 0 && <button className="btn btn-secondary btn-sm" onClick={() => navigate('/map')}>🗺️ View on Map</button>}
            </div>
          )}
          {isProcessing && (
            <div className="alert alert-warning">⏳ Detection is still running ({video.processing_progress?.toFixed(0)}%). You can place control points now; saving is enabled once processing completes.</div>
          )}

          <div className="two-col" style={{ marginBottom: '24px' }}>
            {/* Video */}
            <div className="panel" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <div style={{ background: '#000', height: '360px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {videoError ? (
                  <p style={{ color: 'var(--alert)', padding: '16px', textAlign: 'center' }}>❌ {videoError}</p>
                ) : (
                  <video
                    ref={videoRef}
                    src={videosAPI.streamUrl(video.id)}
                    controls
                    preload="metadata"
                    crossOrigin="anonymous"
                    onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
                    onSeeked={(e) => setCurrentTime(e.target.currentTime)}
                    onLoadedMetadata={(e) => setMediaDuration(e.target.duration || 0)}
                    onError={(e) => setVideoError(e.target.error?.message || 'This browser cannot play the original file format')}
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                )}
              </div>
              <div style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--ink-soft)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Current time</div>
                  <div className="detection-time" style={{ fontSize: '20px' }}>{formatTime(currentTime)}</div>
                </div>
                {pendingTime == null ? (
                  <button className="btn btn-primary" onClick={startAddPoint} disabled={!!videoError}>
                    📍 Add control point at current time
                  </button>
                ) : (
                  <button className="btn btn-secondary" onClick={() => setPendingTime(null)}>✕ Cancel</button>
                )}
              </div>
            </div>

            {/* Map */}
            <div className="map-container" style={{ height: '440px', cursor: pendingTime != null ? 'crosshair' : undefined }}>
              {pendingTime != null && (
                <div className="alert alert-info" style={{ position: 'absolute', top: '12px', left: '50%', transform: 'translateX(-50%)', zIndex: 1000, margin: 0, whiteSpace: 'nowrap' }}>
                  🎯 Click the map where the vehicle was at <strong>{formatTime(pendingTime)}</strong>
                </div>
              )}
              <MapContainer center={DEFAULT_CENTER} zoom={12} style={{ height: '100%', width: '100%' }} zoomControl={true}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <ClickCapture active={pendingTime != null} onPick={placePoint} />
                <FitOnce points={points} />
                {polyline.length >= 2 && <Polyline positions={polyline} color="#14b8a6" weight={3} opacity={0.8} />}
                {points.map((p, i) => (
                  <Marker key={p.id ?? `new-${p.video_time_s}`} position={[p.latitude, p.longitude]} icon={createNumberedIcon(i + 1)}
                    eventHandlers={{ click: () => seekTo(p.video_time_s) }} />
                ))}
              </MapContainer>
            </div>
          </div>

          {/* Control point table */}
          <div className="panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '16px' }}>Control Points</h3>
                <p style={{ fontSize: '12px', color: 'var(--ink-soft)', marginTop: '2px' }}>
                  {points.length} point{points.length !== 1 ? 's' : ''}{dirty && ' — unsaved changes'}
                  {validationError && points.length > 0 && <span style={{ color: 'var(--alert)', marginLeft: '8px' }}>⚠️ {validationError}</span>}
                </p>
              </div>
              <button className="btn btn-primary" onClick={handleSave} disabled={!canSave}
                title={validationError || (isProcessing ? 'Wait for processing to finish' : '')}>
                {saving ? 'Saving…' : '💾 Save & apply to detections'}
              </button>
            </div>

            {points.length === 0 ? (
              <div className="empty-state" style={{ padding: '32px 20px' }}>
                <div className="empty-icon" style={{ fontSize: '36px' }}>🎯</div>
                <h3 style={{ fontSize: '15px' }}>No control points yet</h3>
                <p style={{ fontSize: '13px' }}>Scrub to a landmark and press “Add control point at current time”</p>
              </div>
            ) : (
              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>#</th><th>Video time</th><th>Latitude</th><th>Longitude</th><th>Status</th><th></th></tr>
                  </thead>
                  <tbody>
                    {points.map((p, i) => (
                      <tr key={p.id ?? `new-${p.video_time_s}`} className="clickable" onClick={() => seekTo(p.video_time_s)} title="Click to jump the video to this time">
                        <td>{i + 1}</td>
                        <td className="detection-time">{formatTime(p.video_time_s)}</td>
                        <td>{p.latitude.toFixed(6)}</td>
                        <td>{p.longitude.toFixed(6)}</td>
                        <td>{p.id ? <span className="badge badge-completed">saved</span> : <span className="badge badge-pending">unsaved</span>}</td>
                        <td style={{ textAlign: 'right' }}>
                          <button className="btn btn-danger btn-sm" onClick={(e) => { e.stopPropagation(); removePoint(p); }}>🗑</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

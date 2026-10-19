import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { videosAPI } from '../api';
import { errorMessage, isRunning } from '../labels';
import Icon from '../icons';
import Notice from '../components/Notice';
import SkeletonRows from '../components/SkeletonRows';
import { cssVar } from '../theme';

// Must match backend/services/georeference_service.py
const PH_BOUNDS = { latMin: 4.5, latMax: 21.5, lonMin: 116.0, lonMax: 127.0 };
const MIN_POINTS = 2;
const DEFAULT_CENTER = [14.1294, 120.9056]; // Mendez-Nuñez, Cavite — same as the damage map

const formatTime = (s) => {
  if (s == null || isNaN(s)) return '—';
  const m = Math.floor(s / 60);
  return `${m}:${(s % 60).toFixed(2).padStart(5, '0')}`;
};

// Numbered pin, styled by .control-pin in index.css.
const numberedIcon = (n) => L.divIcon({
  html: `<div class="control-pin">${n}</div>`,
  className: '',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

// Mirrors validate_control_points() so Save can explain itself before calling the API.
function validatePoints(points, duration) {
  if (points.length < MIN_POINTS) return `Add at least ${MIN_POINTS} points to save.`;
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (i > 0 && p.video_time_s <= points[i - 1].video_time_s) {
      return `Point ${i + 1} (${formatTime(p.video_time_s)}) must be later than point ${i} (${formatTime(points[i - 1].video_time_s)}).`;
    }
    if (duration && p.video_time_s > duration) return `Point ${i + 1} is past the end of the video.`;
    if (p.latitude < PH_BOUNDS.latMin || p.latitude > PH_BOUNDS.latMax ||
        p.longitude < PH_BOUNDS.lonMin || p.longitude > PH_BOUNDS.lonMax) {
      return `Point ${i + 1} is outside the Philippines.`;
    }
  }
  return null;
}

// Forward map clicks only while a point is waiting for its position
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

/** "Place on the map" tab: match moments in the video to where the vehicle was. */
export default function SurveyPlaceTab({ video, detections, onSaved }) {
  const videoRef = useRef();
  const [points, setPoints] = useState(null);      // sorted by video_time_s; saved ones carry an id
  const [pendingTime, setPendingTime] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [mediaDuration, setMediaDuration] = useState(0);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState(null);
  const [error, setError] = useState('');
  const [videoError, setVideoError] = useState(null);

  useEffect(() => {
    videosAPI.getControlPoints(video.id)
      .then(res => setPoints(res.data.control_points || []))
      .catch(err => { setPoints([]); setError(errorMessage(err, 'Could not load the saved points. Reload the page to try again.')); });
  }, [video.id]);

  const running = isRunning(video);
  const list = points || [];
  const duration = video.duration || mediaDuration || 0;
  const validationError = validatePoints(list, duration);
  const saveReason = running
    ? 'Saving is possible once the analysis is done.'
    : validationError || (!dirty ? 'No changes to save.' : null);

  const startAddPoint = () => {
    const el = videoRef.current;
    if (!el) return;
    el.pause();
    const t = el.currentTime;
    if (list.some(p => Math.abs(p.video_time_s - t) < 0.05)) {
      setError(`There is already a point at ${formatTime(t)}. Move the video to a different moment first.`);
      return;
    }
    setError('');
    setSaveResult(null);
    setPendingTime(t);
  };

  const placePoint = (latlng) => {
    setPoints([...list, { video_time_s: pendingTime, latitude: latlng.lat, longitude: latlng.lng }]
      .sort((a, b) => a.video_time_s - b.video_time_s));
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
      const res = await videosAPI.deleteControlPoint(video.id, p.id);
      // Keep any unsaved local additions; replace the saved set with what the server now holds
      const unsaved = list.filter(x => !x.id);
      setPoints([...(res.data.control_points || []), ...unsaved].sort((a, b) => a.video_time_s - b.video_time_s));
      setDirty(unsaved.length > 0);
      onSaved?.(res.data.video);
    } catch (err) {
      setError(errorMessage(err, 'Could not remove that point. Try again.'));
    }
  };

  const save = async () => {
    setSaving(true); setError(''); setSaveResult(null);
    try {
      const payload = list.map(({ video_time_s, latitude, longitude }) => ({ video_time_s, latitude, longitude }));
      const res = await videosAPI.saveControlPoints(video.id, payload);
      setPoints(res.data.control_points || []);
      setSaveResult(res.data.applied);
      setDirty(false);
      onSaved?.(res.data.video);
    } catch (err) {
      setError(errorMessage(err, 'Could not save the points. Check your connection and try again.'));
    } finally {
      setSaving(false);
    }
  };

  const seekTo = (t) => {
    if (!videoRef.current) return;
    videoRef.current.pause();
    videoRef.current.currentTime = t;
  };

  const nextNumber = list.filter(p => p.video_time_s < (pendingTime ?? 0)).length + 1;
  const total = saveResult ? saveResult.positioned + saveResult.unpositioned : detections.length;

  return (
    <div className="stack">
      {saveResult ? (
        <Notice kind="success"
          action={saveResult.positioned > 0 && (
            <Link to={`/map?video=${video.id}`} className="link-arrow">See on the map<Icon name="chevron-right" size={16} /></Link>
          )}>
          <span className="num">{saveResult.positioned}</span> of <span className="num">{total}</span>
          {total === 1 ? ' damage is' : ' damages are'} now on the map
          {saveResult.unpositioned > 0 && <> (<span className="num">{saveResult.unpositioned}</span> fall outside your points)</>}.
        </Notice>
      ) : (
        <div>
          <p>Match moments in the video to where the vehicle was. Use 2 to 10 points along the drive.</p>
          <details className="details details-inline">
            <summary><Icon name="info-circle" />How this works</summary>
            <div className="details-body">
              <ol className="numbered">
                <li>Play or drag the video to a moment that shows a landmark you can find on the map: an intersection, a church, a bridge.</li>
                <li>Press <strong>Add a point at this moment</strong>.</li>
                <li>Click that spot on the map.</li>
                <li>Repeat for 2 to 10 points spread along the drive. Add one wherever the vehicle stopped or turned.</li>
                <li>Press <strong>Save points and place damage</strong>.</li>
              </ol>
              <ul className="rules">
                <li>Each point must be later in the video than the one before it.</li>
                <li>Points must be inside the Philippines.</li>
                <li>Damage seen before the first point or after the last one is not placed.</li>
                <li>You can add points while the video is being analysed, but saving waits until it is done.</li>
              </ul>
            </div>
          </details>
        </div>
      )}

      {error && <Notice kind="error">{error}</Notice>}

      <div className="place-grid">
        <div className="panel place-panel">
          <div className="video-frame video-frame-compact">
            {videoError ? (
              <div className="video-error">
                <Notice kind="error" title="This video can't play in this browser">
                  <p>Try Chrome or Edge, or convert the video to MP4 and upload it again.</p>
                  <p className="muted">Browser message: <code>{videoError}</code></p>
                </Notice>
              </div>
            ) : (
              <video ref={videoRef} src={videosAPI.streamUrl(video.id)} controls preload="metadata" crossOrigin="anonymous"
                aria-label="Survey video"
                onTimeUpdate={(e) => setCurrentTime(e.target.currentTime)}
                onSeeked={(e) => setCurrentTime(e.target.currentTime)}
                onLoadedMetadata={(e) => setMediaDuration(e.target.duration || 0)}
                onError={(e) => setVideoError(e.target.error?.message || 'Format error')} />
            )}
          </div>

          <div className="inline-row">
            <button type="button" className="btn btn-secondary" onClick={startAddPoint}
              disabled={Boolean(videoError) || pendingTime != null}>
              <Icon name="plus" />Add a point at this moment
            </button>
            <span className="muted">at <span className="num">{formatTime(currentTime)}</span></span>
          </div>

          <h2 className="panel-subtitle">Points (<span className="num">{list.length}</span>)</h2>
          {points === null ? <SkeletonRows rows={2} label="Loading points" /> : list.length === 0 ? (
            <p className="muted">No points yet. Move the video to a landmark and add the first one.</p>
          ) : (
            <table className="table points-table">
              <caption className="visually-hidden">Points matching video moments to map positions</caption>
              <thead>
                <tr><th scope="col">#</th><th scope="col">Time</th><th scope="col">Position</th><th scope="col">Status</th>
                  <th scope="col"><span className="visually-hidden">Remove</span></th></tr>
              </thead>
              <tbody>
                {list.map((p, i) => (
                  <tr key={p.id ?? `new-${p.video_time_s}`}>
                    <td className="num">{i + 1}</td>
                    <td>
                      <button type="button" className="btn btn-quiet btn-compact num" onClick={() => seekTo(p.video_time_s)}
                        aria-label={`Jump the video to point ${i + 1} at ${formatTime(p.video_time_s)}`}>
                        {formatTime(p.video_time_s)}
                      </button>
                    </td>
                    <td className="num">{p.latitude.toFixed(5)}, {p.longitude.toFixed(5)}</td>
                    <td>{p.id ? 'Saved' : <span className="text-danger">Not saved</span>}</td>
                    <td className="cell-end">
                      <button type="button" className="btn btn-icon" onClick={() => removePoint(p)} aria-label={`Remove point ${i + 1}`}>
                        <Icon name="x" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="save-row">
            <button type="button" className="btn btn-primary" onClick={save} disabled={Boolean(saveReason) || saving}
              aria-describedby={saveReason ? 'save-reason' : undefined}>
              {saving ? 'Saving…' : 'Save points and place damage'}
            </button>
            {saveReason && <p className="muted" id="save-reason">{saveReason}</p>}
          </div>
        </div>

        <div className={`map-frame place-map${pendingTime != null ? ' is-picking' : ''}`} role="region" aria-label="Map for placing points">
          {pendingTime != null && (
            <div className="map-prompt" role="status">
              <span>Click the spot on the map for point <span className="num">{nextNumber}</span> (<span className="num">{formatTime(pendingTime)}</span>).</span>
              <button type="button" className="btn btn-quiet btn-compact" onClick={() => setPendingTime(null)}>Cancel</button>
            </div>
          )}
          <MapContainer center={DEFAULT_CENTER} zoom={14} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ClickCapture active={pendingTime != null} onPick={placePoint} />
            <FitOnce points={list} />
            {list.length >= 2 && <Polyline positions={list.map(p => [p.latitude, p.longitude])} pathOptions={{ color: cssVar('--map-route'), weight: 3, opacity: 0.8 }} />}
            {list.map((p, i) => (
              <Marker key={p.id ?? `new-${p.video_time_s}`} position={[p.latitude, p.longitude]} icon={numberedIcon(i + 1)}
                eventHandlers={{ click: () => seekTo(p.video_time_s) }} />
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}

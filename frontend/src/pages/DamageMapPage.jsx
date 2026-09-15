import { Fragment, useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { mapAPI } from '../api';

// Map data palette. These four hues encode the RDD2022 damage classes on the map and are used
// nowhere else in the interface (the seven design tokens cover everything that is not data).
// Okabe–Ito hues: distinct from each other, from the OpenStreetMap base, and under common
// colour-vision deficiency.
const DAMAGE_CLASSES = [
  { code: 'D00', label: 'Longitudinal crack', color: '#009E73' },
  { code: 'D10', label: 'Transverse crack',   color: '#0072B2' },
  { code: 'D20', label: 'Alligator crack',    color: '#CC79A7' },
  { code: 'D40', label: 'Pothole',            color: '#D55E00' },
];
const CLASS_BY_CODE = Object.fromEntries(DAMAGE_CLASSES.map(c => [c.code, c]));
const UNKNOWN_CLASS = { code: '', label: 'Unclassified damage', color: '#5C635A' }; // --ink-soft

const INK = '#1A1D19';           // --ink: dot outline
const ROUTE_COLOR = '#0E5661';   // --cyan: the route is the focus of the map
const ROUTE_CASING = '#FFFDF8';  // --card: light casing so the route reads over dark roads
const DOT_RADIUS = 9;

const classFor = (d) => CLASS_BY_CODE[d.damage_type] || UNKNOWN_CLASS;

// Solid dot for GPS-measured positions; dashed, lighter dot for positions placed by hand.
const dotStyle = (d) => {
  const color = classFor(d).color;
  return d.position_source === 'georeferenced'
    ? { color, weight: 2.5, dashArray: '3 3', fillColor: color, fillOpacity: 0.4 }
    : { color: INK, weight: 1.5, fillColor: color, fillOpacity: 1 };
};

// Fit the view to everything drawn (route + dots). Re-fits when the survey changes so
// switching maps actually moves the view.
function FitBounds({ points, fitKey }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 0) {
      map.fitBounds(L.latLngBounds(points), { padding: [50, 50], maxZoom: 16 });
    }
  }, [fitKey, points, map]);
  return null;
}

function Route({ track, label }) {
  const start = track.points[0];
  const end = track.points[track.points.length - 1];
  const line = { lineCap: 'round', lineJoin: 'round', opacity: 1 };
  return (
    <>
      <Polyline positions={track.points} pathOptions={{ ...line, color: ROUTE_CASING, weight: 9 }} />
      <Polyline positions={track.points} pathOptions={{ ...line, color: ROUTE_COLOR, weight: 5 }} />
      <CircleMarker center={start} radius={7}
        pathOptions={{ color: ROUTE_COLOR, weight: 3, fillColor: ROUTE_CASING, fillOpacity: 1 }}>
        <Tooltip permanent direction="top" offset={[0, -8]} className="route-label">Start{label}</Tooltip>
      </CircleMarker>
      <CircleMarker center={end} radius={7}
        pathOptions={{ color: ROUTE_CASING, weight: 2, fillColor: ROUTE_COLOR, fillOpacity: 1 }}>
        <Tooltip permanent direction="top" offset={[0, -8]} className="route-label">End{label}</Tooltip>
      </CircleMarker>
    </>
  );
}

export default function DamageMapPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const videoId = searchParams.get('video') || '';   // '' means every survey

  const [detections, setDetections] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ damage_type: '', status: '' });

  // One key per (survey, filters, reload) combination. The page is loading whenever the last
  // completed request was for a different key, so nothing is set synchronously in the effect.
  const [reloadTick, setReloadTick] = useState(0);
  const requestKey = `${videoId}|${filters.damage_type}|${filters.status}|${reloadTick}`;
  const [loadedKey, setLoadedKey] = useState(null);
  const loading = loadedKey !== requestKey;

  useEffect(() => {
    let cancelled = false;   // a newer request supersedes this one
    Promise.all([
      mapAPI.getDetections({ damage_type: filters.damage_type, status: filters.status }, videoId),
      mapAPI.getGpsTracks(videoId),
      mapAPI.getMappedVideos(),
    ]).then(([detRes, trackRes, vidRes]) => {
      if (cancelled) return;
      setDetections(detRes.data.detections || []);
      setTracks(trackRes.data.tracks || []);
      setVideos(vidRes.data.videos || []);
      setError('');
      setLoadedKey(requestKey);
    }).catch((err) => {
      if (cancelled) return;
      setError(
        err.response?.status === 401
          ? 'Your session has expired. Sign in again to see the map.'
          : 'Could not load the map. Check that the server is running, then choose Reload.'
      );
      setLoadedKey(requestKey);
    });
    return () => { cancelled = true; };
  }, [requestKey, videoId, filters.damage_type, filters.status]);

  const reload = () => { setLoadedKey(null); setReloadTick(t => t + 1); };

  // Switching survey resets the view; keeping filters would hide markers for no visible reason.
  const selectVideo = (id) => {
    setFilters({ damage_type: '', status: '' });
    setSearchParams(id ? { video: id } : {}, { replace: false });
  };

  const selected = videos.find(v => String(v.id) === String(videoId));
  const anyFilter = Boolean(filters.damage_type || filters.status);

  // Count of dots on the map per class, after filters.
  const counts = useMemo(() => {
    const c = {};
    for (const d of detections) c[d.damage_type] = (c[d.damage_type] || 0) + 1;
    return c;
  }, [detections]);
  const hasHandPlaced = detections.some(d => d.position_source === 'georeferenced');
  const routeFromPoints = tracks.some(t => t.source === 'control_points');

  const boundsPoints = useMemo(() => [
    ...detections.map(d => [d.latitude, d.longitude]),
    ...tracks.flatMap(t => t.points),
  ], [detections, tracks]);

  const defaultCenter = [14.1294, 120.9056]; // Mendez-Nuñez, Cavite
  const center = boundsPoints[0] || defaultCenter;

  return (
    <div className="page">
      <div className="page-header" style={{ marginBottom: 'var(--s3)', paddingBottom: 'var(--s3)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 'var(--s3)', flexWrap: 'wrap' }}>
          <div>
            <h2>{selected ? selected.name : 'Damage map'}</h2>
            <p>
              {selected
                ? 'The road driven in this survey, and every pothole and crack found along it.'
                : 'Every road surveyed so far and every pothole and crack found along them. Each dot is one damage; its colour is the kind of damage.'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 'var(--s3)', alignItems: 'center' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowFilters(!showFilters)}>
              {showFilters ? 'Hide filters' : 'Filter by type'}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={reload}>Reload</button>
          </div>
        </div>

        {/* Survey switcher — one map per survey, or all of them together */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--s2)', marginTop: 'var(--s3)', flexWrap: 'wrap' }}>
          <label htmlFor="map-survey" style={{ marginBottom: 0 }}>Showing</label>
          <select id="map-survey" className="input-field" value={videoId}
            onChange={(e) => selectVideo(e.target.value)} style={{ minWidth: '260px' }}>
            <option value="">All surveys{videos.length ? ` (${videos.length})` : ''}</option>
            {videos.map(v => (
              <option key={v.id} value={v.id}>
                {v.name}{v.road_name ? ` — ${v.road_name}` : ''} ({v.detection_count})
              </option>
            ))}
          </select>
          {selected && (
            <>
              <span className="secondary">
                <span className="mono">{selected.detection_count}</span> damage{selected.detection_count === 1 ? '' : 's'} on this survey
              </span>
              <button className="btn btn-secondary btn-sm" onClick={() => selectVideo('')}>Show all surveys</button>
              <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/videos/${selected.id}`)}>Open the video</button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error} <button className="btn btn-secondary btn-sm" onClick={reload}>Try again</button>
        </div>
      )}

      {loading && (
        <div className="list" aria-busy="true" aria-label="Loading the map">
          {[0, 1, 2, 3].map(i => (
            <div className="skeleton-row" key={i}>
              <div className="skeleton" style={{ width: '92px' }} />
              <div className="skeleton" style={{ flex: 1, maxWidth: '320px' }} />
            </div>
          ))}
        </div>
      )}

      {showFilters && !loading && (
        <div className="filter-bar">
          <select className="input-field" value={filters.damage_type} aria-label="Kind of damage"
            onChange={e => setFilters({ ...filters, damage_type: e.target.value })}>
            <option value="">All kinds of damage</option>
            {DAMAGE_CLASSES.map(c => <option key={c.code} value={c.code}>{c.label}s</option>)}
          </select>
          <select className="input-field" value={filters.status} aria-label="Repair stage"
            onChange={e => setFilters({ ...filters, status: e.target.value })}>
            <option value="">Any repair stage</option>
            <option value="pending_validation">Not yet checked</option>
            <option value="inspected">Checked on site</option>
            <option value="scheduled">Repair scheduled</option>
            <option value="ongoing_repair">Repair under way</option>
            <option value="resolved">Repaired</option>
          </select>
          {anyFilter && (
            <button className="btn btn-secondary btn-sm" onClick={() => setFilters({ damage_type: '', status: '' })}>
              Clear filters
            </button>
          )}
        </div>
      )}

      {!loading && !error && (
      <div className="map-container">
        {detections.length === 0 && tracks.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 'var(--s3)' }}>
            <div className="empty-state">
              {selected ? (
                <>
                  <h3>This survey has no locations yet</h3>
                  <p>
                    Damage was found in this video, but none of it has a place on the map yet. Add a GPS
                    file when you upload, or match a few points in the video to the map by hand.
                  </p>
                  <button className="btn btn-primary" onClick={() => navigate(`/videos/${selected.id}/georeference`)}>
                    Place this survey on the map
                  </button>
                  <p style={{ marginTop: 'var(--s2)' }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => selectVideo('')}>Show all surveys instead</button>
                  </p>
                </>
              ) : anyFilter ? (
                <>
                  <h3>Nothing matches these filters</h3>
                  <p>No located damage matches the kind and repair stage you picked.</p>
                  <button className="btn btn-secondary" onClick={() => setFilters({ damage_type: '', status: '' })}>Clear filters</button>
                </>
              ) : (
                <>
                  <h3>Start with one road survey</h3>
                  <p>
                    Upload a dashcam video of a road and the system will find the damage in it. Add a GPS
                    file from your phone or dashcam and every pothole it finds lands on this map.
                  </p>
                  <button className="btn btn-primary" onClick={() => navigate('/upload')}>Upload a video</button>
                </>
              )}
            </div>
          </div>
        ) : (
          <MapContainer center={center} zoom={14} style={{ height: '100%', width: '100%' }} zoomControl={true}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <FitBounds points={boundsPoints} fitKey={videoId} />

            {/* Route driven, drawn under the dots. Start and end are labelled; when several
                surveys share the map the label also names the survey. */}
            {tracks.map(t => (
              <Route key={t.video_id} track={t} label={videoId ? '' : ` · ${t.video_name}`} />
            ))}

            {detections.map(d => {
              const cls = classFor(d);
              return (
                <CircleMarker key={d.id} center={[d.latitude, d.longitude]} radius={DOT_RADIUS} pathOptions={dotStyle(d)}>
                  <Tooltip direction="top" offset={[0, -DOT_RADIUS]}>{cls.label}</Tooltip>
                  <Popup>
                    <div className="map-popup">
                      <div className="map-popup-type">
                        <span className="map-legend-dot" style={{ background: cls.color }} />
                        {cls.label}
                      </div>
                      <div className="mono">{d.damage_type || '—'} · {(d.confidence * 100).toFixed(1)}% confidence</div>
                      {d.road_name && <div className="secondary">{d.road_name}</div>}
                      <div className="mono">{d.latitude.toFixed(6)}, {d.longitude.toFixed(6)}</div>
                      {d.position_source === 'georeferenced' && (
                        <div className="secondary">Placed by hand between control points, not measured by GPS.</div>
                      )}
                      {d.video_id > 0 && (
                        <button className="btn btn-secondary btn-sm" style={{ marginRight: 0, alignSelf: 'flex-start' }}
                          onClick={() => navigate(`/videos/${d.video_id}?t=${d.timestamp}`)}>
                          Open in the video
                        </button>
                      )}
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>
        )}

        {(detections.length > 0 || tracks.length > 0) && (
          <div className="map-legend" aria-label="Map legend">
            <div className="map-legend-title">Kind of damage</div>
            {DAMAGE_CLASSES.map(c => (
              <div className="map-legend-item" key={c.code}>
                <span className="map-legend-dot" style={{ background: c.color }} />
                <span>{c.label}</span>
                <span className="mono map-legend-count">{counts[c.code] || 0}</span>
              </div>
            ))}
            {hasHandPlaced && (
              <div className="map-legend-item">
                <span className="map-legend-dot map-legend-dot-hand" />
                <span>Placed by hand</span>
              </div>
            )}
            {tracks.length > 0 && (
              <Fragment>
                <div className="map-legend-title" style={{ marginTop: 'var(--s1)' }}>Route</div>
                <div className="map-legend-item"><span className="map-legend-line" /><span>Road driven</span></div>
                <div className="map-legend-item">
                  <span className="map-legend-end map-legend-end-start" /><span>Start</span>
                  <span className="map-legend-end" style={{ marginLeft: 'var(--s1)' }} /><span>End</span>
                </div>
                {routeFromPoints && (
                  <div className="secondary" style={{ marginTop: '4px', maxWidth: '200px' }}>
                    Drawn straight between the points you placed; no GPS log was uploaded.
                  </div>
                )}
              </Fragment>
            )}
          </div>
        )}
      </div>
      )}
    </div>
  );
}

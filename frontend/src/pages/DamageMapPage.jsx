import { useState, useEffect, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip, useMap, useMapEvents } from 'react-leaflet';
import MapResizeFix, { OSM_ATTRIBUTION, OSM_TILES } from '../components/MapResizeFix';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { mapAPI } from '../api';
import { STATUSES, STATUS_LABELS, errorMessage } from '../labels';
import Icon from '../icons';
import Notice from '../components/Notice';
import DamagePreview from '../components/DamagePreview';
import { AiCheck } from '../components/StatusLabel';
import EmptyState from '../components/EmptyState';
import SkeletonRows from '../components/SkeletonRows';
import useMediaQuery, { WIDE } from '../useMediaQuery';

// Map data palette. These four hues encode the RDD2022 damage classes and are used only on the
// map (dots, legend, popup swatch). Okabe–Ito: distinct from each other, from the OpenStreetMap
// base, and under common colour-vision deficiency.
const DAMAGE_CLASSES = [
  { code: 'D00', label: 'Longitudinal crack', color: '#009E73' },
  { code: 'D10', label: 'Transverse crack',   color: '#0072B2' },
  { code: 'D20', label: 'Alligator crack',    color: '#CC79A7' },
  { code: 'D40', label: 'Pothole',            color: '#D55E00' },
];
const CLASS_BY_CODE = Object.fromEntries(DAMAGE_CLASSES.map(c => [c.code, c]));
const UNKNOWN_CLASS = { code: '', label: 'Unclassified damage', color: '#5C635A' };

const ROUTE_COLOR = '#13294B';   // --color-header: the route is chrome, not data
const ROUTE_CASING = '#FFFFFF';  // light casing so the route reads over dark roads
const DOT_RADIUS = 8;
const DOT_RADIUS_SELECTED = 11;

const classFor = (d) => CLASS_BY_CODE[d.damage_type] || UNKNOWN_CLASS;

// GPS-measured: solid dot with a 2px white halo. Placed by hand: dashed class-colour stroke over a
// 35% fill. The dot whose close-up is open is larger with an ink ring. Clicks on a dot do not
// reach the map, where a click closes the close-up.
const dotStyle = (d, selected) => {
  const color = classFor(d).color;
  const base = d.position_source === 'georeferenced'
    ? { color, weight: 2.5, dashArray: '3 3', fillColor: color, fillOpacity: 0.35 }
    : { color: '#FFFFFF', weight: 2, fillColor: color, fillOpacity: 1 };
  return { ...base, ...(selected ? { color: '#17201B', weight: 3, dashArray: null } : {}), bubblingMouseEvents: false };
};

// A click on the map itself (not on a dot) closes the close-up.
function MapClick({ onClick }) {
  useMapEvents({ click: onClick });
  return null;
}

/**
 * The close-up of one damage on the map, with what the old popup said. `pinned` is false while it
 * only follows the pointer over a dot; clicking the dot keeps it open.
 */
function MapPreview({ d, pinned, inline, onClose }) {
  const cls = classFor(d);
  const fromVideo = d.source_type !== 'public_report';
  return (
    <div className={`map-preview${inline ? ' map-preview-inline panel' : ''}`}>
      <DamagePreview
        key={d.id}
        detection={d}
        onClose={pinned ? onClose : null}
        title={<><span className="legend-dot" style={{ background: cls.color }} />{cls.label} <span className="code">{d.damage_type || '—'}</span></>}
      >
        <div className="damage-preview-facts">
          <p className="num">
            {fromVideo ? `${Math.round(d.confidence * 100)}% confidence` : 'Resident report'}
            {fromVideo && d.timestamp_formatted ? ` · ${d.timestamp_formatted} into the video` : ''}
          </p>
          <p>{STATUS_LABELS[d.inspection_status] || STATUS_LABELS.pending_validation}{d.road_name ? ` · ${d.road_name}` : ''}</p>
          <p className="num muted">{d.latitude.toFixed(6)}, {d.longitude.toFixed(6)}</p>
          {d.position_source === 'georeferenced' && <p className="muted">Placed by hand between control points.</p>}
          {fromVideo && <div><AiCheck detection={d} withScore /></div>}
          {d.video_id > 0 && d.can_open_video && (
            <p>
              <Link to={`/videos/${d.video_id}?t=${d.timestamp}`} className="link-arrow">
                Open in the video<Icon name="chevron-right" size={16} />
              </Link>
            </p>
          )}
          {!pinned && <p className="muted">Click the dot to keep this open.</p>}
        </div>
      </DamagePreview>
    </div>
  );
}

// Fit the view to everything drawn. Re-fits when the survey changes so switching moves the view.
function FitBounds({ points, fitKey }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 0) map.fitBounds(L.latLngBounds(points), { padding: [50, 50], maxZoom: 16 });
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
      <CircleMarker center={start} radius={7} pathOptions={{ color: ROUTE_COLOR, weight: 3, fillColor: ROUTE_CASING, fillOpacity: 1 }}>
        <Tooltip permanent direction="top" offset={[0, -8]} className="route-label">Start{label}</Tooltip>
      </CircleMarker>
      <CircleMarker center={end} radius={7} pathOptions={{ color: ROUTE_CASING, weight: 2, fillColor: ROUTE_COLOR, fillOpacity: 1 }}>
        <Tooltip permanent direction="top" offset={[0, -8]} className="route-label">End{label}</Tooltip>
      </CircleMarker>
    </>
  );
}

function Legend({ counts, hasHandPlaced, hasRoute, routeFromPoints }) {
  return (
    <section className="legend" aria-labelledby="legend-title">
      <h2 id="legend-title" className="panel-subtitle">Legend</h2>
      <ul className="legend-list">
        {DAMAGE_CLASSES.map(c => (
          <li key={c.code}>
            <span className="legend-dot" style={{ background: c.color }} />
            <span>{c.label} <span className="code">{c.code}</span></span>
            <span className="num legend-count">{counts[c.code] || 0}</span>
          </li>
        ))}
        {hasHandPlaced && (
          <li><span className="legend-dot legend-dot-hand" /><span>Placed by hand</span></li>
        )}
      </ul>
      {hasRoute && (
        <>
          <p className="legend-route">
            <span className="legend-line" /> Route
            <span className="legend-end legend-end-start" /> Start
            <span className="legend-end" /> End
          </p>
          {routeFromPoints && <p className="muted legend-note">Drawn straight between the points you placed.</p>}
        </>
      )}
    </section>
  );
}

export default function DamageMapPage() {
  const wide = useMediaQuery(WIDE);
  const [searchParams, setSearchParams] = useSearchParams();
  const videoId = searchParams.get('video') || '';   // '' means every survey

  const [detections, setDetections] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ damage_type: '', status: '' });

  // One key per (survey, filters, reload). The page is loading whenever the last completed request
  // was for a different key, so nothing is set synchronously in the effect.
  const [reloadTick, setReloadTick] = useState(0);
  const requestKey = `${videoId}|${filters.damage_type}|${filters.status}|${reloadTick}`;
  const [loadedKey, setLoadedKey] = useState(null);
  const loading = loadedKey !== requestKey;

  useEffect(() => {
    let cancelled = false;
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
      setError(errorMessage(err, 'Could not load the map. Check that the server is running, then try again.'));
      setLoadedKey(requestKey);
    });
    return () => { cancelled = true; };
  }, [requestKey, videoId, filters.damage_type, filters.status]);

  // The close-up: the dot under the pointer, else the dot last clicked.
  const [hovered, setHovered] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const selectedDet = detections.find(d => d.id === selectedId) || null;
  const previewDet = hovered || selectedDet;
  const closePreview = () => { setSelectedId(null); setHovered(null); };

  useEffect(() => {
    if (selectedId == null) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') { setSelectedId(null); setHovered(null); } };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [selectedId]);

  const reload = () => setReloadTick(t => t + 1);
  const clearFilters = () => setFilters({ damage_type: '', status: '' });

  // Switching survey resets the filters; keeping them would hide dots for no visible reason.
  const selectVideo = (id) => {
    clearFilters();
    setSearchParams(id ? { video: id } : {});
  };

  const selected = videos.find(v => String(v.id) === String(videoId));
  const filterCount = [filters.damage_type, filters.status].filter(Boolean).length;

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
  const center = boundsPoints[0] || [14.1294, 120.9056]; // Mendez-Nuñez, Cavite

  const filterFields = (
    <div className="stack-sm">
      <div className="field">
        <label className="field-label" htmlFor="map-type">Kind of damage</label>
        <select id="map-type" className="input" value={filters.damage_type}
          onChange={e => setFilters({ ...filters, damage_type: e.target.value })}>
          <option value="">All kinds</option>
          {DAMAGE_CLASSES.map(c => <option key={c.code} value={c.code}>{c.label} ({c.code})</option>)}
        </select>
      </div>
      <div className="field">
        <label className="field-label" htmlFor="map-status">Repair stage</label>
        <select id="map-status" className="input" value={filters.status}
          onChange={e => setFilters({ ...filters, status: e.target.value })}>
          <option value="">All stages</option>
          {STATUSES.map(s => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
        </select>
      </div>
      {filterCount > 0 && (
        <div><button type="button" className="btn btn-quiet" onClick={clearFilters}><Icon name="x" />Clear filters</button></div>
      )}
    </div>
  );

  const legend = (detections.length > 0 || tracks.length > 0) && (
    <Legend counts={counts} hasHandPlaced={hasHandPlaced} hasRoute={tracks.length > 0} routeFromPoints={routeFromPoints} />
  );

  const empty = !loading && !error && detections.length === 0 && tracks.length === 0;

  return (
    <div className="page page-wide">
      <div className="map-layout">
        <aside className="panel map-sidebar" aria-label="Map controls">
          <div className="panel-head">
            <h1 className="map-title">Damage map</h1>
            <button type="button" className="btn btn-quiet" onClick={reload}><Icon name="refresh" />Reload</button>
          </div>

          <div className="field">
            <label className="field-label" htmlFor="map-survey">Survey</label>
            <select id="map-survey" className="input" value={videoId} onChange={(e) => selectVideo(e.target.value)}>
              <option value="">All surveys ({videos.length})</option>
              {videos.map(v => (
                <option key={v.id} value={v.id}>
                  {v.name}{v.road_name ? ` — ${v.road_name}` : ''} ({v.detection_count})
                </option>
              ))}
            </select>
          </div>

          {selected && (
            <div className="stack-sm">
              <p className="muted"><span className="num">{selected.detection_count}</span> {selected.detection_count === 1 ? 'damage' : 'damages'} on this survey</p>
              <div className="inline-row">
                <button type="button" className="btn btn-secondary" onClick={() => selectVideo('')}>Show all surveys</button>
                {selected.can_open && <Link to={`/videos/${selected.id}`} className="btn btn-secondary"><Icon name="video" />Open the video</Link>}
              </div>
            </div>
          )}

          {wide ? filterFields : (
            <details className="details">
              <summary><Icon name="filter" />Filters{filterCount > 0 && <> (<span className="num">{filterCount}</span> on)</>}</summary>
              <div className="details-body">{filterFields}</div>
            </details>
          )}

          {wide && legend}
        </aside>

        <div className="map-area">
          {error && <Notice kind="error" action={<button type="button" className="btn btn-secondary" onClick={reload}><Icon name="refresh" />Try again</button>}>{error}</Notice>}

          {loading ? (
            <div className="map-frame map-frame-main map-loading"><SkeletonRows rows={4} label="Loading the map" /></div>
          ) : empty ? (
            <div className="map-frame map-frame-main map-empty">
              {selected ? (
                <EmptyState icon="map-pin-plus" title="This survey has no locations yet"
                  action={selected.can_open && <Link to={`/videos/${selected.id}/georeference`} className="btn btn-primary"><Icon name="map-pin-plus" />Place it on the map</Link>}>
                  Damage was found in this video, but none of it has a place on the map yet. Match a few
                  moments in the video to the map by hand.
                </EmptyState>
              ) : filterCount > 0 ? (
                <EmptyState icon="filter" title="Nothing matches these filters"
                  action={<button type="button" className="btn btn-secondary" onClick={clearFilters}><Icon name="x" />Clear filters</button>}>
                  No located damage matches the kind and repair stage you picked.
                </EmptyState>
              ) : (
                <EmptyState icon="map" title="Start with one road survey"
                  action={<Link to="/upload" className="btn btn-primary"><Icon name="upload" />Upload a road survey</Link>}>
                  Upload a video of a road with a GPS track, and every pothole and crack found in it lands on this map.
                </EmptyState>
              )}
            </div>
          ) : !error && (
            <div className="map-frame map-frame-main" role="region" aria-label="Damage map">
              <MapContainer center={center} zoom={14} style={{ height: '100%', width: '100%' }}>
                <TileLayer attribution={OSM_ATTRIBUTION} url={OSM_TILES} />
                <MapResizeFix />
                <FitBounds points={boundsPoints} fitKey={videoId} />

                {/* Route under the dots. With several surveys, the label also names the survey. */}
                {tracks.map(t => <Route key={t.video_id} track={t} label={videoId ? '' : ` · ${t.video_name}`} />)}

                <MapClick onClick={closePreview} />

                {/* The selected dot last, so it is drawn on top. */}
                {[...detections.filter(d => d.id !== selectedId), ...(selectedDet ? [selectedDet] : [])].map(d => (
                  <CircleMarker
                    key={d.id}
                    center={[d.latitude, d.longitude]}
                    radius={d.id === selectedId ? DOT_RADIUS_SELECTED : DOT_RADIUS}
                    pathOptions={dotStyle(d, d.id === selectedId)}
                    eventHandlers={{
                      mouseover: () => setHovered(d),
                      mouseout: () => setHovered(h => (h?.id === d.id ? null : h)),
                      click: () => { setSelectedId(d.id); setHovered(null); },
                    }}
                  />
                ))}
              </MapContainer>
              {wide && previewDet && (
                <MapPreview d={previewDet} pinned={previewDet.id === selectedId} onClose={closePreview} />
              )}
            </div>
          )}

          {!wide && !loading && selectedDet && (
            <MapPreview d={selectedDet} pinned inline onClose={closePreview} />
          )}

          {!wide && !loading && legend && <div className="panel">{legend}</div>}
        </div>
      </div>
    </div>
  );
}

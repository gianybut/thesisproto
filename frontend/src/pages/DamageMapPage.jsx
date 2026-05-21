import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { mapAPI, videosAPI } from '../api';

// Fix default marker icon issue with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom colored markers using SVG
const createColoredIcon = (color, size = 28) => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="${size}" height="${Math.round(size*1.3)}">
    <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z" fill="${color}" stroke="#fff" stroke-width="1.5"/>
    <circle cx="12" cy="12" r="5" fill="#fff"/>
  </svg>`;
  return L.divIcon({
    html: svg,
    className: '',
    iconSize: [size, Math.round(size * 1.3)],
    iconAnchor: [size / 2, Math.round(size * 1.3)],
    popupAnchor: [0, -Math.round(size * 1.1)],
  });
};

const SEVERITY_ICONS = {
  high: createColoredIcon('#ef4444'),
  medium: createColoredIcon('#f59e0b'),
  low: createColoredIcon('#eab308'),
  default: createColoredIcon('#3b82f6'),
};

// Auto-fit map to markers
function FitBounds({ detections }) {
  const map = useMap();
  useEffect(() => {
    if (detections.length > 0) {
      const bounds = L.latLngBounds(detections.map(d => [d.latitude, d.longitude]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  }, [detections, map]);
  return null;
}

export default function DamageMapPage() {
  const navigate = useNavigate();
  const [detections, setDetections] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ damage_type: '', severity: '', status: '' });

  const fetchData = async () => {
    try {
      const [detRes, trackRes, statsRes] = await Promise.all([
        mapAPI.getDetections(filters),
        mapAPI.getGpsTracks(),
        mapAPI.getStats(),
      ]);
      setDetections(detRes.data.detections || []);
      setTracks(trackRes.data.tracks || []);
      setStats(statsRes.data || {});
    } catch (err) {
      console.error('Map data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [filters.damage_type, filters.severity, filters.status]);

  // Default center: Philippines
  const defaultCenter = [14.5995, 120.9842];
  const center = detections.length > 0
    ? [detections[0].latitude, detections[0].longitude]
    : defaultCenter;

  if (loading) return <div className="page" style={{display:'flex',alignItems:'center',justifyContent:'center'}}><div className="spinner" /></div>;

  return (
    <div className="page fade-in" style={{ padding: '16px 32px' }}>
      <div className="page-header" style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Damage Map</h2>
          <p>Interactive visualization of geo-located road damages</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => setShowFilters(!showFilters)}>
            🔍 {showFilters ? 'Hide' : 'Show'} Filters
          </button>
          <button className="btn btn-secondary btn-sm" onClick={fetchData}>🔄 Refresh</button>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="filter-bar" style={{ marginBottom: '16px' }}>
          <select className="input-field" value={filters.damage_type}
            onChange={e => setFilters({ ...filters, damage_type: e.target.value })}>
            <option value="">All Damage Types</option>
            <option value="D10">D10 — Longitudinal Crack</option>
            <option value="D20">D20 — Transverse Crack</option>
            <option value="D30">D30 — Alligator Crack</option>
            <option value="D40">D40 — Pothole</option>
          </select>
          <select className="input-field" value={filters.severity}
            onChange={e => setFilters({ ...filters, severity: e.target.value })}>
            <option value="">All Severity</option>
            <option value="high">🔴 High</option>
            <option value="medium">🟠 Medium</option>
            <option value="low">🟡 Low</option>
          </select>
          <select className="input-field" value={filters.status}
            onChange={e => setFilters({ ...filters, status: e.target.value })}>
            <option value="">All Status</option>
            <option value="pending_validation">Pending</option>
            <option value="inspected">Inspected</option>
            <option value="scheduled">Scheduled</option>
            <option value="ongoing_repair">Ongoing Repair</option>
            <option value="resolved">Resolved</option>
          </select>
          {(filters.damage_type || filters.severity || filters.status) && (
            <button className="btn btn-secondary btn-sm"
              onClick={() => setFilters({ damage_type: '', severity: '', status: '' })}>
              ✕ Clear
            </button>
          )}
        </div>
      )}

      {/* Map */}
      <div className="map-container">
        {detections.length === 0 && tracks.length === 0 ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', background: 'var(--bg-secondary)' }}>
            <div className="empty-state">
              <div className="empty-icon">🗺️</div>
              <h3>No geo-located data yet</h3>
              <p>Upload a video with a GPS track file to see damage locations on the map</p>
              <button className="btn btn-primary" onClick={() => navigate('/upload')}>📤 Upload Survey</button>
            </div>
          </div>
        ) : (
          <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}
            zoomControl={true}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <FitBounds detections={detections} />

            {/* GPS Track Polylines */}
            {tracks.map((track) => (
              <Polyline
                key={track.video_id}
                positions={track.points}
                color="#3b82f6"
                weight={3}
                opacity={0.6}
                dashArray="5, 10"
              />
            ))}

            {/* Detection Markers */}
            {detections.map(d => (
              <Marker
                key={d.id}
                position={[d.latitude, d.longitude]}
                icon={SEVERITY_ICONS[d.severity] || SEVERITY_ICONS.default}
              >
                <Popup>
                  <div style={{ minWidth: '200px', fontFamily: 'Inter, sans-serif' }}>
                    <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
                      <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: '700', background: '#f0f0f0' }}>{d.damage_type}</span>
                      <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: '700',
                        background: d.severity === 'high' ? '#fee2e2' : d.severity === 'medium' ? '#fef3c7' : '#fef9c3',
                        color: d.severity === 'high' ? '#dc2626' : d.severity === 'medium' ? '#d97706' : '#ca8a04',
                      }}>{d.severity?.toUpperCase()}</span>
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: '600', marginBottom: '4px' }}>{d.damage_label}</div>
                    <div style={{ fontSize: '11px', color: '#666', marginBottom: '2px' }}>Confidence: {(d.confidence * 100).toFixed(1)}%</div>
                    {d.severity_score != null && <div style={{ fontSize: '11px', color: '#666', marginBottom: '2px' }}>Severity Score: {d.severity_score}</div>}
                    {d.road_name && <div style={{ fontSize: '11px', color: '#666', marginBottom: '2px' }}>📍 {d.road_name}</div>}
                    <div style={{ fontSize: '11px', color: '#666', marginBottom: '8px' }}>
                      {d.latitude.toFixed(6)}, {d.longitude.toFixed(6)}
                    </div>
                    {d.video_id > 0 && (
                      <button
                        onClick={() => navigate(`/videos/${d.video_id}?t=${d.timestamp}`)}
                        style={{ padding: '4px 10px', fontSize: '11px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                      >
                        View in Video →
                      </button>
                    )}
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        )}

        {/* Legend */}
        {detections.length > 0 && (
          <div className="map-legend">
            <div className="map-legend-item"><div className="map-legend-dot" style={{ background: '#ef4444' }} /><span>High Severity</span></div>
            <div className="map-legend-item"><div className="map-legend-dot" style={{ background: '#f59e0b' }} /><span>Medium Severity</span></div>
            <div className="map-legend-item"><div className="map-legend-dot" style={{ background: '#eab308' }} /><span>Low Severity</span></div>
            {tracks.length > 0 && <div className="map-legend-item"><div style={{ width: '20px', height: '2px', background: '#3b82f6', borderTop: '2px dashed #3b82f6' }} /><span>Survey Route</span></div>}
          </div>
        )}

        {/* Stats Bar */}
        {stats.total_geolocated > 0 && (
          <div className="map-stats-bar">
            <div className="stat"><div className="stat-num">{stats.total_geolocated}</div><div className="stat-lbl">Total</div></div>
            <div className="stat"><div className="stat-num" style={{ color: 'var(--severity-high)' }}>{stats.by_severity?.high || 0}</div><div className="stat-lbl">High</div></div>
            <div className="stat"><div className="stat-num" style={{ color: 'var(--severity-medium)' }}>{stats.by_severity?.medium || 0}</div><div className="stat-lbl">Medium</div></div>
            <div className="stat"><div className="stat-num" style={{ color: 'var(--severity-low)' }}>{stats.by_severity?.low || 0}</div><div className="stat-lbl">Low</div></div>
          </div>
        )}
      </div>
    </div>
  );
}

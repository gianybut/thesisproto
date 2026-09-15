import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { databaseAPI } from '../api';

const STATUSES = ['pending_validation', 'inspected', 'scheduled', 'ongoing_repair', 'resolved'];
const STATUS_LABELS = {
  pending_validation: 'Pending',
  inspected: 'Inspected',
  scheduled: 'Scheduled',
  ongoing_repair: 'Ongoing',
  resolved: 'Resolved',
};

export default function DatabasePage() {
  const navigate = useNavigate();
  const [detections, setDetections] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [filters, setFilters] = useState({
    damage_type: '', status: '', search: '',
    sort: 'created_at', dir: 'desc',
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [detRes, statsRes] = await Promise.all([
        databaseAPI.getDetections({ ...filters, page, per_page: 25 }),
        databaseAPI.getStats(),
      ]);
      setDetections(detRes.data.detections || []);
      setTotal(detRes.data.total);
      setTotalPages(detRes.data.total_pages);
      setStats(statsRes.data || {});
    } catch (err) {
      console.error('Database fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [page, filters]);

  const updateStatus = async (id, newStatus) => {
    try {
      await databaseAPI.updateStatus(id, { inspection_status: newStatus });
      fetchData();
    } catch (err) {
      console.error('Status update error:', err);
    }
  };

  const handleExport = async (format) => {
    try {
      const res = await databaseAPI.exportData(format);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `road_damage_data.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export error:', err);
    }
  };

  const toggleSort = (col) => {
    setFilters(prev => ({
      ...prev,
      sort: col,
      dir: prev.sort === col && prev.dir === 'desc' ? 'asc' : 'desc',
    }));
  };

  const SortIcon = ({ col }) => {
    if (filters.sort !== col) return <span style={{ opacity: 0.3 }}>↕</span>;
    return <span style={{ color: 'var(--cyan)' }}>{filters.dir === 'desc' ? '↓' : '↑'}</span>;
  };

  return (
    <div className="page fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>🗃️ Damage Database</h2>
          <p>Centralized road damage records — {total} total entries</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => handleExport('csv')}>📥 Export CSV</button>
          <button className="btn btn-secondary btn-sm" onClick={() => handleExport('json')}>📥 Export JSON</button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
        <div className="stat-card">
          <div className="stat-value" style={{ fontSize: '24px' }}>{stats.total_detections || 0}</div>
          <div className="stat-label">Total Records</div>
        </div>
        <div className="stat-card success">
          <div className="stat-value" style={{ fontSize: '24px' }}>{stats.total_geolocated || 0}</div>
          <div className="stat-label">Geo-located</div>
        </div>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <input className="input-field" type="text" placeholder="🔍 Search road name..."
          value={filters.search} onChange={e => setFilters({ ...filters, search: e.target.value })}
          style={{ minWidth: '180px' }} />
        <select className="input-field" value={filters.damage_type}
          onChange={e => { setFilters({ ...filters, damage_type: e.target.value }); setPage(1); }}>
          <option value="">All kinds of damage</option>
          <option value="D00">Longitudinal cracks</option>
          <option value="D10">Transverse cracks</option>
          <option value="D20">Alligator cracks</option>
          <option value="D40">Potholes</option>
        </select>
        <select className="input-field" value={filters.status}
          onChange={e => { setFilters({ ...filters, status: e.target.value }); setPage(1); }}>
          <option value="">All Status</option>
          {STATUSES.map(s => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
        </select>
      </div>

      {/* Data Table */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px' }}><div className="spinner" /></div>
      ) : detections.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🗃️</div>
          <h3>No records found</h3>
          <p>Upload a road survey video or submit a public report to populate the database</p>
        </div>
      ) : (
        <>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th onClick={() => toggleSort('damage_type')}>Type <SortIcon col="damage_type" /></th>
                  <th onClick={() => toggleSort('confidence')}>Confidence <SortIcon col="confidence" /></th>
                  <th>Location</th>
                  <th onClick={() => toggleSort('status')}>Status <SortIcon col="status" /></th>
                  <th>Source</th>
                  <th onClick={() => toggleSort('created_at')}>Date <SortIcon col="created_at" /></th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {detections.map(d => (
                  <tr key={d.id}>
                    <td style={{ fontSize: '12px', color: 'var(--ink-soft)' }}>#{d.id}</td>
                    <td>
                      <span className={`damage-badge damage-${d.damage_type}`}>{d.damage_type}</span>
                      <span style={{ fontSize: '11px', marginLeft: '6px', color: 'var(--ink-soft)' }}>{d.damage_label}</span>
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                      {(d.confidence * 100).toFixed(1)}%
                    </td>
                    <td>
                      {d.latitude && d.longitude ? (
                        <span style={{ fontSize: '11px', color: 'var(--ink-soft)' }}>
                          📍 {d.latitude.toFixed(4)}, {d.longitude.toFixed(4)}
                        </span>
                      ) : d.road_name ? (
                        <span style={{ fontSize: '11px' }}>{d.road_name}</span>
                      ) : (
                        <span style={{ fontSize: '11px', color: 'var(--ink-soft)' }}>—</span>
                      )}
                    </td>
                    <td>
                      <div className="status-pipeline">
                        {STATUSES.map((s, i) => {
                          const currentIdx = STATUSES.indexOf(d.inspection_status);
                          const isCompleted = i < currentIdx;
                          const isActive = s === d.inspection_status;
                          return (
                            <span key={s}>
                              {i > 0 && <span className="status-arrow">→</span>}
                              <span
                                className={`status-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                                onClick={() => updateStatus(d.id, s)}
                                title={`Set to: ${STATUS_LABELS[s]}`}
                              >
                                {STATUS_LABELS[s]}
                              </span>
                            </span>
                          );
                        })}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '11px', color: 'var(--ink-soft)' }}>
                        {d.source_type === 'public_report' ? 'Citizen report' : 'Video analysis'}
                      </span>
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--ink-soft)' }}>
                      {d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td>
                      {d.video_id > 0 && (
                        <button className="btn btn-secondary btn-sm"
                          onClick={() => navigate(`/videos/${d.video_id}?t=${d.timestamp}`)}
                          style={{ padding: '3px 8px', fontSize: '10px' }}>
                          View
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '20px', alignItems: 'center' }}>
              <button className="btn btn-secondary btn-sm" disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}>← Prev</button>
              <span style={{ fontSize: '13px', color: 'var(--ink-soft)' }}>
                Page {page} of {totalPages}
              </span>
              <button className="btn btn-secondary btn-sm" disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}>Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

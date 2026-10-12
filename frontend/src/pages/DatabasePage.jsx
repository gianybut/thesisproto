import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { databaseAPI } from '../api';
import { DAMAGE_CODES, STATUSES, STATUS_LABELS, damageName, errorMessage, formatDate } from '../labels';
import Icon from '../icons';
import PageHeader from '../components/PageHeader';
import SkeletonRows from '../components/SkeletonRows';
import EmptyState from '../components/EmptyState';
import Notice from '../components/Notice';
import Disclosure from '../components/Disclosure';
import useMediaQuery, { WIDE } from '../useMediaQuery';

const PER_PAGE = 25;

// Phones have no sortable headers, so sorting is a select there.
const SORT_OPTIONS = [
  { value: 'created_at|desc', label: 'Newest first' },
  { value: 'created_at|asc', label: 'Oldest first' },
  { value: 'confidence|desc', label: 'Highest confidence' },
  { value: 'confidence|asc', label: 'Lowest confidence' },
  { value: 'damage_type|asc', label: 'Kind of damage' },
  { value: 'status|asc', label: 'Inspection status' },
];

const confidenceText = (d) => (d.confidence == null ? '–' : `${Math.round(d.confidence * 100)}%`);

export default function DatabasePage() {
  const wide = useMediaQuery(WIDE);
  const [detections, setDetections] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [stats, setStats] = useState(null);
  const [savingId, setSavingId] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState({ damage_type: '', status: '', search: '', sort: 'created_at', dir: 'desc' });

  // One key per (filters, page) request; loading until that exact request has completed.
  const requestKey = JSON.stringify({ filters, page });
  const [loadedKey, setLoadedKey] = useState(null);
  const loading = loadedKey !== requestKey;

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      databaseAPI.getDetections({ ...filters, page, per_page: PER_PAGE }),
      databaseAPI.getStats(),
    ]).then(([detRes, statsRes]) => {
      if (cancelled) return;
      setDetections(detRes.data.detections || []);
      setTotal(detRes.data.total);
      setTotalPages(detRes.data.total_pages || 1);
      setStats(statsRes.data || {});
      setError('');
    }).catch((err) => {
      if (!cancelled) setError(errorMessage(err, 'Could not load the damage records. Check that the server is running, then reload the page.'));
    }).finally(() => {
      if (!cancelled) setLoadedKey(requestKey);
    });
    return () => { cancelled = true; };
  }, [requestKey, filters, page]);

  const setFilter = (key, value) => { setFilters(prev => ({ ...prev, [key]: value })); setPage(1); };
  const applySearch = (e) => { e.preventDefault(); setFilter('search', searchText.trim()); };
  const clearAll = () => {
    setSearchText('');
    setFilters(prev => ({ ...prev, damage_type: '', status: '', search: '' }));
    setPage(1);
  };
  const anyFilter = Boolean(filters.damage_type || filters.status || filters.search);
  const filterCount = [filters.damage_type, filters.status, filters.search].filter(Boolean).length;

  const updateStatus = async (d, value) => {
    setSavingId(d.id);
    setNotice('');
    try {
      await databaseAPI.updateStatus(d.id, { inspection_status: value });
      setDetections(prev => prev.map(x => (x.id === d.id ? { ...x, inspection_status: value } : x)));
      setNotice(`Record ${d.id} (${damageName(d.damage_type).toLowerCase()}) is now marked "${STATUS_LABELS[value]}".`);
      setError('');
    } catch (err) {
      setError(errorMessage(err, `Could not change the status of record ${d.id}. Try again.`));
    } finally {
      setSavingId(null);
    }
  };

  const download = async (format) => {
    try {
      const res = await databaseAPI.exportData(format);
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `road_damage_data.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(errorMessage(err, `Could not download the ${format.toUpperCase()} file. Try again.`));
    }
  };

  const toggleSort = (col) => setFilters(prev => ({
    ...prev, sort: col, dir: prev.sort === col && prev.dir === 'desc' ? 'asc' : 'desc',
  }));

  // A sortable column header (a function, not a component, so it is not re-created per render).
  const sortHeader = (col, children) => {
    const active = filters.sort === col;
    return (
      <th scope="col" key={col} aria-sort={active ? (filters.dir === 'desc' ? 'descending' : 'ascending') : 'none'}>
        <button type="button" className="sort-button" onClick={() => toggleSort(col)}>
          {children}
          <Icon name="chevron-down" size={16} className={`sort-icon${active ? ' is-active' : ''}${active && filters.dir === 'asc' ? ' flip' : ''}`} />
        </button>
      </th>
    );
  };

  const statusSelect = (d) => (
    <select id={`status-${d.id}`} className="input input-compact" value={d.inspection_status || 'pending_validation'}
      disabled={savingId === d.id} onChange={(e) => updateStatus(d, e.target.value)}
      aria-label={wide ? `Inspection status for record ${d.id}` : undefined}>
      {STATUSES.map(s => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
    </select>
  );

  const openInVideo = (d) => d.video_id > 0 && d.source_type !== 'public_report' && (
    <Link to={`/videos/${d.video_id}?t=${d.timestamp}`} className="link-arrow" aria-label={`Open record ${d.id} in its video`}>
      Open in video<Icon name="chevron-right" size={16} />
    </Link>
  );
  const sourceText = (d) => (d.source_type === 'public_report' ? 'Resident report' : 'Survey video');
  const location = (d) => (d.latitude && d.longitude
    ? <span className="num">{d.latitude.toFixed(5)}, {d.longitude.toFixed(5)}</span>
    : <span className="muted">No location</span>);

  const filterFields = (
    <div className="records-filters">
      <form className="field" onSubmit={applySearch} role="search">
        <label className="field-label" htmlFor="db-search">Road name</label>
        <div className="inline-row nowrap">
          <input id="db-search" className="input" type="search" value={searchText} onChange={e => setSearchText(e.target.value)} />
          <button type="submit" className="btn btn-secondary"><Icon name="search" />Search</button>
        </div>
      </form>
      <div className="field">
        <label className="field-label" htmlFor="db-type">Kind of damage</label>
        <select id="db-type" className="input" value={filters.damage_type} onChange={e => setFilter('damage_type', e.target.value)}>
          <option value="">All kinds</option>
          {DAMAGE_CODES.map(c => <option key={c} value={c}>{damageName(c)} ({c})</option>)}
        </select>
      </div>
      <div className="field">
        <label className="field-label" htmlFor="db-status">Inspection status</label>
        <select id="db-status" className="input" value={filters.status} onChange={e => setFilter('status', e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
        </select>
      </div>
      {anyFilter && <button type="button" className="btn btn-quiet" onClick={clearAll}><Icon name="x" />Clear filters</button>}
    </div>
  );

  return (
    <div className="page">
      <PageHeader
        title="Damage records"
        meta={stats && <><span className="num">{stats.total_detections ?? 0}</span> records · <span className="num">{stats.total_geolocated ?? 0}</span> with a location</>}
        actions={
          <Disclosure label="Download" icon={<Icon name="download" />}>
            {(close) => (
              <ul className="menu-list">
                <li><button type="button" className="menu-item" onClick={() => { close(); download('csv'); }}>CSV, for spreadsheets</button></li>
                <li><button type="button" className="menu-item" onClick={() => { close(); download('json'); }}>JSON</button></li>
              </ul>
            )}
          </Disclosure>
        }
      />

      {wide ? filterFields : (
        <div className="stack-sm records-phone-controls">
          <details className="details">
            <summary><Icon name="filter" />Filters{filterCount > 0 && <> (<span className="num">{filterCount}</span> on)</>}</summary>
            <div className="details-body">{filterFields}</div>
          </details>
          <div className="field">
            <label className="field-label" htmlFor="db-sort">Sort by</label>
            <select id="db-sort" className="input" value={`${filters.sort}|${filters.dir}`}
              onChange={e => { const [sort, dir] = e.target.value.split('|'); setFilters(prev => ({ ...prev, sort, dir })); setPage(1); }}>
              {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
        </div>
      )}

      <div aria-live="polite">{notice && <Notice kind="success">{notice}</Notice>}</div>
      {error && <Notice kind="error">{error}</Notice>}

      {loading && detections.length === 0 ? (
        <div className="panel"><SkeletonRows rows={6} label="Loading damage records" /></div>
      ) : detections.length === 0 && !error ? (
        anyFilter ? (
          <EmptyState icon="filter" title="No records match these filters"
            action={<button type="button" className="btn btn-secondary" onClick={clearAll}><Icon name="x" />Clear filters</button>}>
            Try another kind of damage or status, or clear the filters to see every record.
          </EmptyState>
        ) : (
          <EmptyState icon="table" title="No damage recorded yet"
            action={<Link to="/upload" className="btn btn-primary"><Icon name="upload" />Upload a road survey</Link>}>
            Records appear here once a survey has been analysed.
          </EmptyState>
        )
      ) : detections.length > 0 && (
        <>
          {wide ? (
            <div className="panel panel-flush table-wrap" aria-busy={loading}>
              <table className="table records-table">
                <caption className="visually-hidden">Damage records. Headers with a button can be sorted.</caption>
                <thead>
                  <tr>
                    {sortHeader('damage_type', 'Damage')}
                    <th scope="col">Location</th>
                    {sortHeader('status', 'Inspection status')}
                    {sortHeader('confidence', 'Confidence')}
                    {sortHeader('created_at', 'Recorded')}
                  </tr>
                </thead>
                <tbody>
                  {detections.map(d => (
                    <tr key={d.id}>
                      <td>
                        <span className="cell-main"><span className="num muted">#{d.id}</span> {damageName(d.damage_type)} <span className="code">{d.damage_type}</span></span>
                        <span className="cell-sub">{sourceText(d)}</span>
                      </td>
                      <td>
                        <span className="cell-main">{d.road_name || <span className="muted">No road name</span>}</span>
                        <span className="cell-sub">{location(d)}</span>
                      </td>
                      <td>{statusSelect(d)}</td>
                      <td className="num">{confidenceText(d)}</td>
                      <td>
                        <span className="cell-main num">{formatDate(d.created_at)}</span>
                        <span className="cell-sub">{openInVideo(d)}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <ul className="record-cards" aria-busy={loading}>
              {detections.map(d => (
                <li key={d.id} className="panel record-card">
                  <p className="record-card-head">
                    <span><span className="num muted">#{d.id}</span> · {damageName(d.damage_type)} <span className="code">{d.damage_type}</span></span>
                    <span className="num">{confidenceText(d)}</span>
                  </p>
                  {d.road_name && <p>{d.road_name}</p>}
                  <p>{location(d)}</p>
                  <p className="muted">{sourceText(d)} · <span className="num">{formatDate(d.created_at)}</span></p>
                  <div className="field">
                    <label className="field-label" htmlFor={`status-${d.id}`}>Inspection status</label>
                    {statusSelect(d)}
                  </div>
                  {openInVideo(d)}
                </li>
              ))}
            </ul>
          )}

          <nav className="pagination" aria-label="Pages of records">
            <p className="muted">
              Showing <span className="num">{(page - 1) * PER_PAGE + 1}</span>–<span className="num">{Math.min(page * PER_PAGE, total)}</span> of <span className="num">{total}</span>
            </p>
            {totalPages > 1 && (
              <div className="inline-row">
                <button type="button" className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                  <Icon name="chevron-left" size={16} />Previous
                </button>
                <span className="muted">Page <span className="num">{page}</span> of <span className="num">{totalPages}</span></span>
                <button type="button" className="btn btn-secondary" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                  Next<Icon name="chevron-right" size={16} />
                </button>
              </div>
            )}
          </nav>
        </>
      )}
    </div>
  );
}

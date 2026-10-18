import { useEffect, useState } from 'react';
import { activityAPI } from '../api';
import { errorMessage } from '../labels';
import Icon from '../icons';
import EmptyState from '../components/EmptyState';
import Notice from '../components/Notice';
import SkeletonRows from '../components/SkeletonRows';

const PER_PAGE = 50;

const when = (iso) => {
  if (!iso) return { date: '—', time: '' };
  // The server stores UTC without a zone marker; read it as UTC.
  const d = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
  return {
    date: d.toLocaleDateString('en-PH', { year: 'numeric', month: 'short', day: 'numeric' }),
    time: d.toLocaleTimeString('en-PH', { hour: 'numeric', minute: '2-digit' }),
  };
};

/** Who did what, newest first, filterable by person and by kind of action. */
export default function AdminActivityTab() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ user_id: '', action: '' });
  const [page, setPage] = useState(1);

  const requestKey = JSON.stringify({ filters, page });
  const [loadedKey, setLoadedKey] = useState(null);
  const loading = loadedKey !== requestKey;

  useEffect(() => {
    let cancelled = false;
    activityAPI.list({ ...filters, page, per_page: PER_PAGE })
      .then(res => { if (!cancelled) { setData(res.data); setError(''); } })
      .catch(err => { if (!cancelled) setError(errorMessage(err, 'Could not load the activity log. Check that the server is running, then reload the page.')); })
      .finally(() => { if (!cancelled) setLoadedKey(requestKey); });
    return () => { cancelled = true; };
  }, [requestKey, filters, page]);

  const setFilter = (k, v) => { setFilters(f => ({ ...f, [k]: v })); setPage(1); };
  const anyFilter = Boolean(filters.user_id || filters.action);
  const labels = Object.fromEntries((data?.actions || []).map(a => [a.value, a.label]));
  const entries = data?.entries || [];

  return (
    <div className="stack">
      <div className="records-filters">
        <div className="field">
          <label className="field-label" htmlFor="log-user">Person</label>
          <select id="log-user" className="input" value={filters.user_id} onChange={e => setFilter('user_id', e.target.value)}>
            <option value="">Everyone</option>
            {(data?.users || []).map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="log-action">What happened</label>
          <select id="log-action" className="input" value={filters.action} onChange={e => setFilter('action', e.target.value)}>
            <option value="">Everything</option>
            {(data?.actions || []).map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
          </select>
        </div>
        {anyFilter && <button type="button" className="btn btn-quiet" onClick={() => { setFilters({ user_id: '', action: '' }); setPage(1); }}><Icon name="x" />Clear filters</button>}
      </div>

      {error && <Notice kind="error">{error}</Notice>}

      {loading && !data ? (
        <div className="panel"><SkeletonRows rows={6} label="Loading the activity log" /></div>
      ) : entries.length === 0 && !error ? (
        <EmptyState icon="clock" title={anyFilter ? 'Nothing matches these filters' : 'No activity yet'}>
          {anyFilter ? 'Choose another person or kind of action, or clear the filters.' : 'Sign-ins, uploads and changes to records and accounts will be listed here.'}
        </EmptyState>
      ) : entries.length > 0 && (
        <>
          <p className="muted"><span className="num">{data.total}</span> {data.total === 1 ? 'entry' : 'entries'}, newest first</p>
          <ol className="panel activity-list" aria-busy={loading}>
            {entries.map(e => {
              const t = when(e.created_at);
              return (
                <li key={e.id} className="activity-row">
                  <p className="activity-when num"><span>{t.date}</span> <span className="muted">{t.time}</span></p>
                  <p className="activity-who">{e.username || <span className="muted">Unknown</span>}</p>
                  <div className="activity-what">
                    <p className={e.action === 'sign_in_failed' ? 'text-danger' : undefined}>{e.summary}</p>
                    <p className="survey-meta">{labels[e.action] || e.action}</p>
                  </div>
                </li>
              );
            })}
          </ol>
          {data.total_pages > 1 && (
            <nav className="pagination" aria-label="Pages of the activity log">
              <p className="muted">Page <span className="num">{page}</span> of <span className="num">{data.total_pages}</span></p>
              <div className="inline-row">
                <button type="button" className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                  <Icon name="chevron-left" size={16} />Newer
                </button>
                <button type="button" className="btn btn-secondary" disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)}>
                  Older<Icon name="chevron-right" size={16} />
                </button>
              </div>
            </nav>
          )}
        </>
      )}
    </div>
  );
}

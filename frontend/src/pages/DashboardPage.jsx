import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI } from '../api';
import { MAX_VIDEO_MINUTES, errorMessage, formatDate, isRunning, surveyName } from '../labels';
import { canAccess, roleOf } from '../roles';
import Icon from '../icons';
import PageHeader from '../components/PageHeader';
import SkeletonRows from '../components/SkeletonRows';
import Notice from '../components/Notice';
import { SurveyStatus } from '../components/StatusLabel';

const SHORTCUTS = [
  { path: '/map', label: 'Damage map', icon: 'map' },
  { path: '/database', label: 'Damage records', icon: 'table' },
  { path: '/videos', label: 'Surveys', icon: 'video' },
];

export default function DashboardPage({ user }) {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');
  const role = roleOf(user);

  const running = (stats?.recent_videos || []).some(isRunning) || (stats?.processing_videos || 0) > 0;

  // Load once; keep polling every 5 s only while a survey is being analysed.
  useEffect(() => {
    let cancelled = false;
    const load = () => dashboardAPI.stats()
      .then(res => { if (!cancelled) { setStats(res.data); setError(''); } })
      .catch(err => { if (!cancelled) setError(errorMessage(err, 'Could not load the overview. Check that the server is running, then reload the page.')); });
    load();
    if (!running) return () => { cancelled = true; };
    const t = setInterval(load, 5000);
    return () => { cancelled = true; clearInterval(t); };
  }, [running]);

  const s = stats || {};
  const counts = [
    { label: 'Surveys uploaded', value: s.total_videos, icon: 'video' },
    { label: 'Being analysed now', value: s.processing_videos, icon: 'hourglass' },
    { label: 'Damage found', value: s.total_detections, icon: 'alert-triangle' },
    { label: 'Damage with a location', value: s.geolocated_count, icon: 'map-pin' },
  ];

  return (
    <div className="page">
      <PageHeader title="Overview" />

      {error && <Notice kind="error">{error}</Notice>}

      {canAccess(role, '/upload') && (
        <div className="panel start-panel">
          <Link to="/upload" className="btn btn-primary"><Icon name="upload" />Upload a road survey</Link>
          <p className="muted">{MAX_VIDEO_MINUTES} minutes or shorter, with an optional GPS track</p>
        </div>
      )}

      <ul className="count-grid" aria-label="Your surveys in numbers">
        {counts.map(c => (
          <li key={c.label} className="count-tile">
            <Icon name={c.icon} className="count-icon" />
            <span className="count-value num">{stats ? (c.value ?? 0) : '–'}</span>
            <span className="count-label">{c.label}</span>
          </li>
        ))}
      </ul>

      <div className="overview-columns">
        <section className="panel" aria-labelledby="recent-title">
          <div className="panel-head">
            <h2 id="recent-title" className="panel-title">Recent surveys</h2>
            <Link to="/videos" className="link-arrow">See all surveys<Icon name="chevron-right" size={16} /></Link>
          </div>
          {!stats && !error ? <SkeletonRows rows={4} label="Loading recent surveys" /> : s.recent_videos?.length > 0 ? (
            <ul className="row-list">
              {s.recent_videos.map(v => (
                <li key={v.id} className="recent-row">
                  <span className="num muted recent-date">{formatDate(v.upload_date)}</span>
                  <Link to={`/videos/${v.id}`} className="row-title">{surveyName(v)}</Link>
                  <SurveyStatus video={v} />
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No surveys yet. Your uploads will be listed here.</p>
          )}
        </section>

        <nav className="panel" aria-labelledby="goto-title">
          <h2 id="goto-title" className="panel-title">Go to</h2>
          <ul className="shortcut-list">
            {SHORTCUTS.filter(x => canAccess(role, x.path)).map(x => (
              <li key={x.path}>
                <Link to={x.path} className="shortcut">
                  <Icon name={x.icon} className="shortcut-icon" />
                  <span className="shortcut-label">{x.label}</span>
                  <Icon name="chevron-right" size={16} />
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </div>
  );
}

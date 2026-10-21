import Icon from '../icons';
import { videoStatusLabel } from '../labels';

const SURVEY_STATUS = {
  uploaded:   { icon: 'clock',        cls: 'status-waiting' },
  processing: { icon: 'half-circle',  cls: 'status-analysing' },
  completed:  { icon: 'check',        cls: 'status-ready' },
  failed:     { icon: 'alert-circle', cls: 'status-failed' },
};

/** Survey status: always icon plus words, never colour alone. */
export function SurveyStatus({ video }) {
  const s = SURVEY_STATUS[video.status] || SURVEY_STATUS.uploaded;
  const text = video.status === 'processing'
    ? `Analysing ${Math.round(video.processing_progress || 0)}%`
    : videoStatusLabel(video.status);
  return (
    <span className={`status-label ${s.cls}`}>
      <Icon name={s.icon} size={16} />
      <span className="num">{text}</span>
    </span>
  );
}

/** Where a survey's positions come from: route icon for GPS, pin for hand-placed. */
export function LocationSource({ video, withCount = false }) {
  if (video.has_gps || video.position_source === 'gps_file') {
    return <span className="meta-icon"><Icon name="route" size={16} />GPS track</span>;
  }
  if (video.position_source === 'georeferenced') {
    return (
      <span className="meta-icon">
        <Icon name="map-pin" size={16} />
        Placed by hand{withCount && video.control_point_count ? <> from <span className="num">{video.control_point_count}</span> points</> : ''}
      </span>
    );
  }
  return <span className="meta-icon muted">No location yet</span>;
}

export function ProgressBar({ value, label }) {
  const v = Math.max(0, Math.min(100, Math.round(value || 0)));
  return (
    <div className="progress" role="progressbar" aria-label={label} aria-valuenow={v} aria-valuemin={0} aria-valuemax={100}>
      <div className="progress-fill" style={{ width: `${v}%` }} />
    </div>
  );
}

/**
 * The AI check of one damage record (backend services/damage_verifier.py): a second model's view of
 * whether the close-up is road damage. Advice for the admin, who decides. Nothing for resident
 * reports, which are photos taken by a person.
 */
export function AiCheck({ detection: d, withScore = false }) {
  if (d.source_type === 'public_report') return null;
  if (d.ai_check_score == null) {
    return <span className="status-label status-waiting"><Icon name="clock" size={16} />AI check not run</span>;
  }
  const pct = Math.round(d.ai_check_score * 100);
  return d.ai_flagged ? (
    <span className="status-label status-failed">
      <Icon name="alert-triangle" size={16} />Likely not road damage{withScore && <span className="num"> · {pct}%</span>}
    </span>
  ) : (
    <span className="status-label status-ready">
      <Icon name="check" size={16} />Looks like road damage{withScore && <span className="num"> · {pct}%</span>}
    </span>
  );
}


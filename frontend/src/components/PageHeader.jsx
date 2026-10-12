import { Link } from 'react-router-dom';
import Icon from '../icons';

/**
 * One-line page header: title plus actions. Explanations do not live here — they go into hints,
 * empty states or a closed "How this works".
 *
 * @param back   { to, label } for a single "< Surveys" link above the title
 * @param meta   one short muted line under the title (counts, facts)
 */
export default function PageHeader({ title, back, meta, actions, children }) {
  return (
    <div className="page-head">
      {back && (
        <Link to={back.to} className="back-link">
          <Icon name="chevron-left" size={16} />{back.label}
        </Link>
      )}
      <div className="page-head-row">
        <div className="page-head-title">
          {typeof title === 'string' ? <h1>{title}</h1> : title}
          {meta && <div className="page-meta">{meta}</div>}
        </div>
        {actions && <div className="page-head-actions">{actions}</div>}
      </div>
      {children}
    </div>
  );
}

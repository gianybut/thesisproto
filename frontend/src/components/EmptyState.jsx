import Icon from '../icons';

/** §9: an invitation to act, not an apology. The 48px icon is the only large icon in the app. */
export default function EmptyState({ icon, title, children, action, headingLevel = 2 }) {
  const H = `h${headingLevel}`;
  return (
    <div className="empty-state">
      {icon && <Icon name={icon} size={48} className="empty-icon" />}
      <H className="empty-title">{title}</H>
      {children && <p className="empty-text">{children}</p>}
      {action && <div className="empty-action">{action}</div>}
    </div>
  );
}

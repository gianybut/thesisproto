import Icon from '../icons';

const ICONS = { info: 'info-circle', success: 'check', error: 'alert-circle' };

/**
 * Inline notice: info, success or error, always with an icon and words.
 * Errors are announced immediately (role="alert"); the others politely.
 */
export default function Notice({ kind = 'info', title, children, action }) {
  return (
    <div className={`notice notice-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      <Icon name={ICONS[kind]} className="notice-icon" />
      <div className="notice-body">
        {title && <p className="notice-title">{title}</p>}
        {children && <div className="notice-text">{children}</div>}
        {action && <div className="notice-action">{action}</div>}
      </div>
    </div>
  );
}

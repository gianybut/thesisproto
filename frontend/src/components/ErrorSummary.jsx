import { useEffect, useRef } from 'react';
import Icon from '../icons';

/**
 * GOV.UK-style error summary: a list at the top of a form that links to each field with a
 * problem. It takes focus when it appears so screen-reader and keyboard users land on it.
 *
 * @param errors  [{ field: 'input-id', message: '...' }]
 */
export default function ErrorSummary({ errors }) {
  const ref = useRef();
  const count = errors.length;

  useEffect(() => {
    if (count > 0) ref.current?.focus();
  }, [count]);

  if (count === 0) return null;

  const jump = (e, field) => {
    e.preventDefault();
    const el = document.getElementById(field);
    el?.focus();
    el?.scrollIntoView({ block: 'center' });
  };

  return (
    <div className="error-summary" role="alert" tabIndex={-1} ref={ref}>
      <Icon name="alert-circle" className="notice-icon" />
      <div>
        <h2 className="error-summary-title">There is a problem</h2>
        <ul>
          {errors.map(e => (
            <li key={e.field + e.message}>
              <a href={`#${e.field}`} onClick={(ev) => jump(ev, e.field)}>{e.message}</a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

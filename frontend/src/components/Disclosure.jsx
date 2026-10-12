import { useEffect, useId, useRef, useState } from 'react';

/**
 * Disclosure menu (a button with aria-expanded plus a panel), not an ARIA role="menu".
 * Escape and a click outside close it; Escape returns focus to the button.
 *
 * @param label / icon / buttonClass  the default trigger button
 * @param renderButton  (props, open) => custom trigger; spread `props` onto a <button>
 * @param children      (close) => panel content
 */
export default function Disclosure({ label, buttonClass = 'btn btn-secondary', icon, align = 'end', panelClass = '', children, renderButton }) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef();
  const id = useId();

  useEffect(() => {
    if (!open) return;
    const onDoc = (e) => { if (!wrapRef.current?.contains(e.target)) setOpen(false); };
    const onKey = (e) => {
      if (e.key !== 'Escape') return;
      setOpen(false);
      wrapRef.current?.querySelector('[aria-controls]')?.focus();
    };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDoc); document.removeEventListener('keydown', onKey); };
  }, [open]);

  const close = () => setOpen(false);
  const btnProps = {
    type: 'button',
    'aria-expanded': open,
    'aria-controls': id,
    onClick: () => setOpen(o => !o),
  };

  return (
    <div className="disclosure" ref={wrapRef}>
      {renderButton ? renderButton(btnProps, open) : (
        <button className={buttonClass} {...btnProps}>
          {icon}{label}
          <svg className="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
        </button>
      )}
      {open && (
        <div id={id} className={`menu-panel menu-panel-${align} ${panelClass}`}>
          {children(close)}
        </div>
      )}
    </div>
  );
}

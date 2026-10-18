import { useEffect, useRef } from 'react';

/**
 * Native <dialog> confirmation. Opens as a modal while `open` is true; Escape or
 * "Keep" cancels. The destructive button is the only filled red button in the app.
 */
export default function ConfirmDialog({ open, title, children, confirmLabel, cancelLabel = 'Cancel', busyLabel = 'Deleting…', onConfirm, onCancel, busy }) {
  const ref = useRef();

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);

  return (
    <dialog ref={ref} className="dialog" aria-labelledby="dialog-title"
      onCancel={(e) => { e.preventDefault(); onCancel(); }}>
      <h2 id="dialog-title" className="dialog-title">{title}</h2>
      <div className="dialog-body">{children}</div>
      <div className="dialog-actions">
        <button type="button" className="btn btn-danger" onClick={onConfirm} disabled={busy}>
          {busy ? busyLabel : confirmLabel}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={busy}>
          {cancelLabel}
        </button>
      </div>
    </dialog>
  );
}

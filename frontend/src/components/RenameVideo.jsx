import { useState, useRef, useEffect } from 'react';
import { videosAPI } from '../api';
import { errorMessage } from '../labels';

/**
 * Inline rename form for a survey. The parent decides when it is shown (the survey page's
 * Rename button, or Rename in a survey's More menu). The uploaded filename is never
 * overwritten: saving an empty name goes back to it.
 */
export default function RenameVideo({ video, onRenamed, onCancel }) {
  const [value, setValue] = useState(video.name || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef();
  const id = `rename-${video.id}`;

  useEffect(() => { inputRef.current?.select(); }, []);

  const save = async (e) => {
    e?.preventDefault();
    setSaving(true);
    setError('');
    try {
      const res = await videosAPI.rename(video.id, value.trim());
      onRenamed?.(res.data.video);
    } catch (err) {
      setError(errorMessage(err, 'Could not save the name. Check your connection and try again.'));
      setSaving(false);
    }
  };

  return (
    <form className={`rename-form field${error ? ' has-error' : ''}`} onSubmit={save}
      onKeyDown={(e) => { if (e.key === 'Escape') { e.preventDefault(); onCancel?.(); } }}>
      <label className="field-label" htmlFor={id}>Survey name</label>
      <p className="field-hint" id={`${id}-hint`}>Leave it empty to use the uploaded file name, {video.original_filename}.</p>
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
      <div className="inline-row">
        <input id={id} ref={inputRef} className="input" value={value} maxLength={300} disabled={saving}
          aria-describedby={`${id}-hint${error ? ` ${id}-error` : ''}`}
          onChange={(e) => setValue(e.target.value)} />
        <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save name'}</button>
        <button type="button" className="btn btn-quiet" onClick={onCancel} disabled={saving}>Cancel</button>
      </div>
    </form>
  );
}

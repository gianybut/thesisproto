import { useState, useRef, useEffect } from 'react';
import { videosAPI } from '../api';

/**
 * Inline rename control for a video.
 *
 * Shows the video's current name with a "Rename" link; clicking swaps in a text
 * field. The uploaded filename is never overwritten — clearing the field just
 * drops back to it.
 *
 * @param video    video object from the API (needs id, name, original_filename)
 * @param onRenamed called with the updated video once the server confirms
 * @param as       heading element to render the name in (default h3)
 */
export default function RenameVideo({ video, onRenamed, as }) {
  const Tag = as || 'h3';
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(video.name || video.original_filename || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef();

  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

  const start = () => {
    setValue(video.display_name || video.name || '');
    setError('');
    setEditing(true);
  };

  const cancel = () => { setEditing(false); setError(''); };

  const save = async () => {
    setSaving(true);
    setError('');
    try {
      const res = await videosAPI.rename(video.id, value.trim());
      onRenamed?.(res.data.video);
      setEditing(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Could not save the name. Check your connection and try again.');
    } finally {
      setSaving(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); save(); }
    if (e.key === 'Escape') { e.preventDefault(); cancel(); }
  };

  if (!editing) {
    return (
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--s2)', flexWrap: 'wrap', minWidth: 0 }}>
        <Tag style={{ margin: 0, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {video.name || video.original_filename}
        </Tag>
        <button type="button" className="btn btn-secondary btn-sm" onClick={start}
          style={{ minHeight: 'auto', padding: '2px 0', fontSize: '13px' }}>
          Rename
        </button>
      </div>
    );
  }

  return (
    <div style={{ minWidth: 0, width: '100%', maxWidth: '460px' }}>
      <label htmlFor={`rename-${video.id}`}>Name this survey</label>
      <div style={{ display: 'flex', gap: 'var(--s1)', alignItems: 'center', marginTop: '6px', flexWrap: 'wrap' }}>
        <input
          id={`rename-${video.id}`}
          ref={inputRef}
          className="input-field"
          style={{ flex: 1, minWidth: '200px' }}
          value={value}
          maxLength={300}
          disabled={saving}
          placeholder={video.original_filename}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <button type="button" className="btn btn-primary btn-sm" onClick={save} disabled={saving}>
          {saving ? 'Saving' : 'Save'}
        </button>
        <button type="button" className="btn btn-secondary btn-sm" onClick={cancel} disabled={saving}>
          Cancel
        </button>
      </div>
      <p className="secondary" style={{ marginTop: '6px' }}>
        Leave it empty to go back to the uploaded file name.
      </p>
      {error && <div className="alert alert-error" style={{ marginTop: 'var(--s1)' }}>{error}</div>}
    </div>
  );
}

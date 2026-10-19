import { useState } from 'react';
import { videosAPI } from '../api';
import { errorMessage } from '../labels';
import Icon from '../icons';
import Notice from './Notice';

/**
 * A failed analysis: the server's reason (Video.error_message) and "Analyse again", which reruns
 * it from the files already on the server (POST /videos/:id/reprocess), so nobody re-uploads.
 * onRestarted(video) gets the survey back in the "Waiting to start" state.
 */
export default function AnalysisFailed({ video, onRestarted, title = 'The analysis stopped before it finished' }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const retry = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await videosAPI.reprocess(video.id);
      onRestarted?.(res.data.video);
    } catch (err) {
      setError(errorMessage(err, 'Could not start the analysis again. Try again in a moment.'));
      setBusy(false);
    }
  };

  return (
    <Notice kind="error" title={title}
      action={(
        <button type="button" className="btn btn-secondary" onClick={retry} disabled={busy}>
          <Icon name="refresh" />{busy ? 'Starting…' : 'Analyse again'}
        </button>
      )}>
      <p>{video.error_message || 'The server could not finish analysing this survey.'}</p>
      {error && <p><strong>{error}</strong></p>}
      <p>If it fails again, tell your system administrator.</p>
    </Notice>
  );
}

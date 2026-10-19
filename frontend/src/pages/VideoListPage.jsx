import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { videosAPI } from '../api';
import {
  canPlaceByHand, errorMessage, formatDate, formatDuration, formatSize, hasLocation, isRunning, surveyName,
} from '../labels';
import Icon from '../icons';
import PageHeader from '../components/PageHeader';
import SkeletonRows from '../components/SkeletonRows';
import EmptyState from '../components/EmptyState';
import Notice from '../components/Notice';
import Disclosure from '../components/Disclosure';
import ConfirmDialog from '../components/ConfirmDialog';
import RenameVideo from '../components/RenameVideo';
import { LocationSource, ProgressBar, SurveyStatus } from '../components/StatusLabel';
import { isAdmin } from '../roles';

// The one visible next step for a survey; everything else lives in its More menu.
function NextStep({ v }) {
  if (hasLocation(v)) {
    return <Link to={`/map?video=${v.id}`} className="btn btn-secondary"><Icon name="map" />See on the map</Link>;
  }
  if (canPlaceByHand(v)) {
    return <Link to={`/videos/${v.id}/georeference`} className="btn btn-secondary"><Icon name="map-pin-plus" />Place on the map</Link>;
  }
  return null;
}

export default function VideoListPage({ user }) {
  // An administrator sees every account's surveys (the server decides; this only labels them).
  const admin = isAdmin(user);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [renamingId, setRenamingId] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [toReanalyse, setToReanalyse] = useState(null);
  const [reanalysing, setReanalysing] = useState(false);

  const fetchVideos = useCallback(() => videosAPI.list()
    .then(res => { setVideos(res.data.videos); setError(''); })
    .catch(err => setError(errorMessage(err, 'Could not load your surveys. Check that the server is running, then reload the page.')))
    .finally(() => setLoading(false)), []);

  // Poll every 5 s so analysis progress stays live.
  useEffect(() => {
    fetchVideos();
    const t = setInterval(fetchVideos, 5000);
    return () => clearInterval(t);
  }, [fetchVideos]);

  // A failed survey has nothing to lose, so it starts at once; a finished one asks first
  // (its damage records are replaced, with any inspection status set on them).
  const reanalyse = async (v) => {
    setNotice('');
    setReanalysing(true);
    try {
      const res = await videosAPI.reprocess(v.id);
      setVideos(prev => prev.map(x => (x.id === v.id ? res.data.video : x)));
      setNotice(`Analysing "${surveyName(v)}" again.`);
    } catch (err) {
      setError(errorMessage(err, `Could not start the analysis of "${surveyName(v)}" again. Try again.`));
    } finally {
      setReanalysing(false);
      setToReanalyse(null);
    }
  };

  const confirmDelete = async () => {
    const v = toDelete;
    setDeleting(true);
    try {
      await videosAPI.delete(v.id);
      setNotice(`Deleted "${surveyName(v)}".`);
      setVideos(prev => prev.filter(x => x.id !== v.id));
    } catch (err) {
      setError(errorMessage(err, `Could not delete "${surveyName(v)}". Try again.`));
    } finally {
      setDeleting(false);
      setToDelete(null);
    }
  };

  return (
    <div className="page">
      <PageHeader
        title="Surveys"
        meta={!loading && videos.length > 0 ? <><span className="num">{videos.length}</span> {videos.length === 1 ? 'survey' : 'surveys'}{admin ? ' from every account' : ''}, newest first</> : null}
        actions={<Link to="/upload" className="btn btn-primary"><Icon name="upload" />Upload survey</Link>}
      />

      {notice && <Notice kind="success">{notice}</Notice>}
      {error && <Notice kind="error">{error}</Notice>}

      {loading ? (
        <div className="panel"><SkeletonRows rows={4} label="Loading surveys" /></div>
      ) : videos.length === 0 && !error ? (
        <EmptyState icon="video" title="Upload your first road survey"
          action={<Link to="/upload" className="btn btn-primary"><Icon name="upload" />Upload a road survey</Link>}>
          Record a road with a dashcam or phone, then upload the video. The damage found in it appears
          here and on the map.
        </EmptyState>
      ) : (
        <ul className="panel survey-list">
          {videos.map(v => (
            <li key={v.id} className="survey-row">
              {renamingId === v.id ? (
                <RenameVideo video={v} onCancel={() => setRenamingId(null)}
                  onRenamed={(u) => { setVideos(prev => prev.map(x => (x.id === u.id ? { ...x, ...u } : x))); setRenamingId(null); }} />
              ) : (
                <>
                  <div className="survey-main">
                    <Link to={`/videos/${v.id}`} className="row-title">{surveyName(v)}</Link>
                    <p className="survey-meta num">
                      {[admin && v.user_id !== user.id && v.uploaded_by && `By ${v.uploaded_by}`, v.road_name, formatDate(v.upload_date), formatDuration(v.duration), formatSize(v.file_size)].filter(Boolean).join(' · ')}
                    </p>
                  </div>
                  <div className="survey-state">
                    <SurveyStatus video={v} />
                    {isRunning(v) ? (
                      <>
                        <ProgressBar value={v.processing_progress} label={`Analysis progress for ${surveyName(v)}`} />
                        <LocationSource video={v} />
                      </>
                    ) : (
                      <p className="survey-meta">
                        {v.status === 'completed' && <><span className="num">{v.total_detections}</span> {v.total_detections === 1 ? 'damage' : 'damages'} · </>}
                        <LocationSource video={v} />
                      </p>
                    )}
                  </div>
                  <div className="survey-actions">
                    <NextStep v={v} />
                    <Disclosure
                      renderButton={(props) => (
                        <button className="btn btn-icon" aria-label={`More actions for ${surveyName(v)}`} {...props}>
                          <Icon name="dots" />
                        </button>
                      )}
                    >
                      {(close) => (
                        <ul className="menu-list">
                          <li><Link to={`/videos/${v.id}`} className="menu-item"><Icon name="video" />Open survey</Link></li>
                          <li><button type="button" className="menu-item" onClick={() => { close(); setRenamingId(v.id); }}><Icon name="pencil" />Rename</button></li>
                          {(v.status === 'failed' || v.status === 'completed') && (
                            <li><button type="button" className="menu-item" onClick={() => { close(); if (v.status === 'failed') reanalyse(v); else setToReanalyse(v); }}>
                              <Icon name="refresh" />Analyse again</button></li>
                          )}
                          {v.position_source === 'georeferenced' && !v.has_gps && (
                            <li><Link to={`/videos/${v.id}/georeference`} className="menu-item"><Icon name="map-pin" />Adjust map position</Link></li>
                          )}
                          <li className="menu-divider" role="separator" />
                          <li><button type="button" className="menu-item menu-item-danger" onClick={() => { close(); setToDelete(v); }}><Icon name="trash" />Delete survey</button></li>
                        </ul>
                      )}
                    </Disclosure>
                  </div>
                </>
              )}
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={Boolean(toReanalyse)}
        title={toReanalyse ? `Analyse "${surveyName(toReanalyse)}" again?` : ''}
        confirmLabel="Replace damage records"
        cancelLabel="Keep them"
        busyLabel="Starting…"
        busy={reanalysing}
        onConfirm={() => reanalyse(toReanalyse)}
        onCancel={() => setToReanalyse(null)}
      >
        {toReanalyse && (
          <p>
            The video is analysed again with the current model and settings. Its <span className="num">{toReanalyse.total_detections || 0}</span>
            {' '}damage records are replaced by the new results, and any inspection status set on them is lost.
          </p>
        )}
      </ConfirmDialog>

      <ConfirmDialog
        open={Boolean(toDelete)}
        title={toDelete ? `Delete "${surveyName(toDelete)}"?` : ''}
        confirmLabel="Delete survey"
        cancelLabel="Keep survey"
        busy={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      >
        {toDelete && (
          <p>
            This removes the video and all <span className="num">{toDelete.total_detections || 0}</span>
            {toDelete.total_detections === 1 ? ' damage' : ' damages'} found in it. This cannot be undone.
          </p>
        )}
      </ConfirmDialog>
    </div>
  );
}

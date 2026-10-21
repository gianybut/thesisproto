import { useState, useRef, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { videosAPI } from '../api';
import { DAMAGE_CODES, canPlaceByHand, damageName, hasLocation, isRunning } from '../labels';
import Icon from '../icons';
import Notice from '../components/Notice';
import AnalysisFailed from '../components/AnalysisFailed';
import DamagePreview from '../components/DamagePreview';
import { AiCheck } from '../components/StatusLabel';
import EmptyState from '../components/EmptyState';
import { ProgressBar } from '../components/StatusLabel';

/** "Damage found" tab: the video beside the list of damage found in it. */
export default function SurveyDamageTab({ video, detections, onChange }) {
  const [searchParams] = useSearchParams();
  const videoRef = useRef();
  const [activeId, setActiveId] = useState(null);
  const [filter, setFilter] = useState('');
  const [videoError, setVideoError] = useState(null);
  const [useOriginal, setUseOriginal] = useState(false);
  const [seeked, setSeeked] = useState(false);

  const running = isRunning(video);
  const processed = video.status === 'completed' && !useOriginal;
  const src = processed ? videosAPI.processedUrl(video.id) : videosAPI.streamUrl(video.id);

  // ?t=seconds jumps to that moment and highlights the nearest detection.
  const onLoaded = useCallback(() => {
    if (seeked) return;
    const t = parseFloat(searchParams.get('t'));
    if (Number.isNaN(t) || !videoRef.current) return;
    videoRef.current.currentTime = t;
    videoRef.current.pause();
    setSeeked(true);
    const nearest = detections.reduce((best, d) =>
      (!best || Math.abs(d.timestamp - t) < Math.abs(best.timestamp - t) ? d : best), null);
    if (nearest) setActiveId(nearest.id);
  }, [searchParams, detections, seeked]);

  const jump = (d) => {
    setActiveId(d.id);
    if (!videoRef.current) return;
    videoRef.current.pause();
    videoRef.current.currentTime = d.timestamp;
  };

  const present = DAMAGE_CODES.filter(c => detections.some(d => d.damage_type === c));
  const countOf = (c) => detections.filter(d => d.damage_type === c).length;
  const shown = filter ? detections.filter(d => d.damage_type === filter) : detections;
  const active = detections.find(d => d.id === activeId) || null;

  return (
    <div className="stack">
      {running && (
        <div className="panel" aria-live="polite">
          <p className="progress-caption">
            {video.status === 'uploaded' ? 'Waiting to start' : <>Analysing <span className="num">{Math.round(video.processing_progress || 0)}%</span></>}
            <span className="muted"> · damage appears in the list as it is found</span>
          </p>
          <ProgressBar value={video.processing_progress} label="Analysis progress" />
        </div>
      )}

      {video.status === 'failed' && <AnalysisFailed video={video} onRestarted={onChange} />}

      {video.status === 'completed' && detections.length > 0 && !hasLocation(video) && canPlaceByHand(video) && (
        <Notice kind="info"
          action={<Link to={`/videos/${video.id}/georeference`} className="link-arrow">Place it on the map<Icon name="chevron-right" size={16} /></Link>}>
          This survey's damage has no location yet.
        </Notice>
      )}

      <div className="viewer-grid">
        <div className="video-frame">
          {videoError ? (
            <div className="video-error">
              <Notice kind="error" title="This video can't play in this browser"
                action={processed && (
                  <button type="button" className="btn btn-secondary" onClick={() => { setUseOriginal(true); setVideoError(null); }}>
                    <Icon name="play" />Play the original video
                  </button>
                )}>
                <p>The analysed copy may not have been converted on the server. Your system administrator can check this.</p>
                <p className="muted">Browser message: <code>{videoError}</code></p>
              </Notice>
            </div>
          ) : (
            <video key={src} ref={videoRef} src={src} controls preload="metadata" crossOrigin="anonymous"
              aria-label={`Survey video${processed ? ', with damage marked' : ''}`}
              onError={(e) => setVideoError(e.target.error?.message || 'Format error')}
              onLoadedMetadata={onLoaded} />
          )}
        </div>

        <section className={`panel damage-panel${detections.length ? ' has-preview' : ''}`} aria-labelledby="damage-title">
          <h2 id="damage-title" className="panel-title">
            Damage found (<span className="num">{detections.length}</span>)
          </h2>

          {/* The close-up of the chosen damage. Its space is kept while nothing is chosen, so
              choosing one does not push the list down under the pointer. */}
          {detections.length > 0 && (
            <div className="damage-panel-preview">
              <DamagePreview
                key={active?.id ?? 'none'}
                detection={active}
                placeholder="Choose a damage in the list to see a close-up of it."
                title={active ? (
                  <>
                    <span className="num">{active.timestamp_formatted}</span>
                    <span>{damageName(active.damage_type)} <span className="code">{active.damage_type}</span></span>
                    <span className="num">{Math.round(active.confidence * 100)}%</span>
                  </>
                ) : 'Close-up'}
              >
                {active && <div><AiCheck detection={active} withScore /></div>}
              </DamagePreview>
            </div>
          )}

          {present.length > 1 && (
            <div className="chips" role="group" aria-label="Show damage of one kind">
              <button type="button" className="chip" aria-pressed={!filter} onClick={() => setFilter('')}>
                All <span className="num">{detections.length}</span>
              </button>
              {present.map(c => (
                <button type="button" key={c} className="chip" aria-pressed={filter === c} onClick={() => setFilter(c)}>
                  {damageName(c)} <span className="code">{c}</span> <span className="num">{countOf(c)}</span>
                </button>
              ))}
            </div>
          )}

          {shown.length === 0 ? (
            <EmptyState icon={running ? 'hourglass' : 'search'} headingLevel={3}
              title={running ? 'Nothing found yet' : 'No damage found'}>
              {running
                ? 'Damage appears here as the video is analysed.'
                : 'Nothing was found in this survey. Check that the video plays and shows the road surface clearly.'}
            </EmptyState>
          ) : (
            <ul className="damage-list">
              {shown.map(d => (
                <li key={d.id}>
                  <button type="button" className="damage-row" aria-current={activeId === d.id ? 'true' : undefined}
                    onClick={() => jump(d)}
                    aria-label={`${damageName(d.damage_type)} at ${d.timestamp_formatted}, ${Math.round(d.confidence * 100)}% confidence. Show a close-up and jump to this moment.`}>
                    <span className="num damage-time">{d.timestamp_formatted}</span>
                    <span className="damage-name">
                      {damageName(d.damage_type)} <span className="code">{d.damage_type}</span>
                      {d.ai_flagged && <span className="damage-flag"><Icon name="alert-triangle" size={16} />AI check: likely not road damage</span>}
                    </span>
                    <span className="num damage-conf">{Math.round(d.confidence * 100)}%</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

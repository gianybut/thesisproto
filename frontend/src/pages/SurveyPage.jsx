import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { videosAPI } from '../api';
import { canPlaceByHand, formatDuration, isRunning, surveyName } from '../labels';
import Icon from '../icons';
import { isAdmin } from '../roles';
import PageHeader from '../components/PageHeader';
import SkeletonRows from '../components/SkeletonRows';
import Notice from '../components/Notice';
import AnalysisFailed from '../components/AnalysisFailed';
import RenameVideo from '../components/RenameVideo';
import { LocationSource, SurveyStatus } from '../components/StatusLabel';
import SurveyDamageTab from './SurveyDamageTab';
import SurveyPlaceTab from './SurveyPlaceTab';

/**
 * One page per survey with a shared header (back link, name, Rename, facts line) and two tabs:
 * "Damage found" (/videos/:id) and "Place on the map" (/videos/:id/georeference). The tabs are
 * links styled as tabs; the second one appears only for surveys without GPS that did not fail.
 */
export default function SurveyPage({ tab, user }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [video, setVideo] = useState(null);
  const [detections, setDetections] = useState([]);
  const [renaming, setRenaming] = useState(false);

  const load = useCallback(() => videosAPI.get(id)
    .then(res => { setVideo(res.data.video); setDetections(res.data.detections || []); })
    .catch(() => navigate('/videos')), [id, navigate]);

  const running = !video || isRunning(video);

  // Poll only while the survey is still being analysed.
  useEffect(() => {
    load();
    if (!running) return;
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [load, running]);

  if (!video) {
    return (
      <div className="page">
        <PageHeader title="Survey" back={{ to: '/videos', label: 'Surveys' }} />
        <div className="panel"><SkeletonRows rows={6} label="Loading the survey" /></div>
      </div>
    );
  }

  const name = surveyName(video);
  const showPlaceTab = canPlaceByHand(video);
  const located = detections.some(d => d.latitude);

  return (
    <div className="page">
      <PageHeader
        back={{ to: '/videos', label: 'Surveys' }}
        title={renaming ? (
          <RenameVideo video={video} onCancel={() => setRenaming(false)}
            onRenamed={(u) => { setVideo(v => ({ ...v, ...u })); setRenaming(false); }} />
        ) : (
          <div className="title-with-action">
            <h1>{name}</h1>
            <button type="button" className="btn btn-quiet" onClick={() => setRenaming(true)}>
              <Icon name="pencil" />Rename
            </button>
          </div>
        )}
        actions={located && (
          <Link to={`/map?video=${video.id}`} className="btn btn-secondary"><Icon name="map" />See on the map</Link>
        )}
        meta={
          <p className="facts-line">
            <SurveyStatus video={video} />
            {isAdmin(user) && video.user_id !== user.id && video.uploaded_by && <span>By {video.uploaded_by}</span>}
            {video.road_name && <span>{video.road_name}</span>}
            <span className="num">{formatDuration(video.duration)}</span>
            {video.resolution && <span className="num">{video.resolution}</span>}
            <LocationSource video={video} withCount />
          </p>
        }
      >
        {showPlaceTab && (
          <nav className="tabs" aria-label="Survey sections">
            <Link to={`/videos/${video.id}`} className="tab" aria-current={tab === 'damage' ? 'page' : undefined}>
              Damage found
            </Link>
            <Link to={`/videos/${video.id}/georeference`} className="tab" aria-current={tab === 'place' ? 'page' : undefined}>
              {video.position_source === 'georeferenced' ? 'Adjust map position' : 'Place on the map'}
            </Link>
          </nav>
        )}
      </PageHeader>

      {tab === 'place' ? (
        video.has_gps ? (
          <Notice kind="info" title="This survey already has a GPS track"
            action={<Link to={`/map?video=${video.id}`} className="link-arrow">See it on the map<Icon name="chevron-right" size={16} /></Link>}>
            Its damage is placed from the measured GPS positions, so it cannot be placed by hand.
          </Notice>
        ) : video.status === 'failed' ? (
          <AnalysisFailed video={video} title="The analysis of this survey failed, so there is no damage to place"
            onRestarted={(v) => setVideo(v)} />
        ) : (
          <SurveyPlaceTab video={video} detections={detections} onSaved={(v) => { setVideo(v); load(); }} />
        )
      ) : (
        <SurveyDamageTab video={video} detections={detections} onChange={(v) => { setVideo(v); setDetections([]); }} />
      )}
    </div>
  );
}

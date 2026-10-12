import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { videosAPI } from '../api';
import {
  GPS_EXTENSIONS, MAX_VIDEO_MINUTES, VIDEO_EXTENSIONS,
  errorMessage, formatDuration, formatSize, surveyName,
} from '../labels';
import Icon from '../icons';
import PageHeader from '../components/PageHeader';
import ErrorSummary from '../components/ErrorSummary';
import Notice from '../components/Notice';
import { ProgressBar } from '../components/StatusLabel';

const extOf = (name) => name.split('.').pop().toLowerCase();
const VIDEO_TYPES = 'MP4, MOV, AVI, MKV or WEBM';

// Read the length of a local video before uploading it, so a too-long survey is refused here
// instead of after a long upload. Resolves null when the browser cannot read the format
// (AVI, MKV); the server still checks.
function readDuration(file) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const el = document.createElement('video');
    const done = (value) => { URL.revokeObjectURL(url); resolve(value); };
    el.preload = 'metadata';
    el.onloadedmetadata = () => done(Number.isFinite(el.duration) ? el.duration : null);
    el.onerror = () => done(null);
    el.src = url;
  });
}

// Uploaded → Analysing → Ready, followed live after the upload.
function UploadResult({ initialVideo, hadGps, onReset }) {
  const [video, setVideo] = useState(initialVideo);
  const finished = video.status === 'completed' || video.status === 'failed';

  useEffect(() => {
    if (finished) return;
    const t = setInterval(() => {
      videosAPI.get(video.id).then(res => setVideo(res.data.video)).catch(() => {});
    }, 2000);
    return () => clearInterval(t);
  }, [finished, video.id]);

  const step = video.status === 'completed' ? 3 : video.status === 'processing' ? 2 : 1;
  const steps = ['Uploaded', 'Analysing', 'Ready'];

  return (
    <div className="page page-narrow">
      <PageHeader title="Upload a road survey" />
      <section className="panel" aria-live="polite" aria-labelledby="result-title">
        <h2 id="result-title" className="panel-title">
          {surveyName(video)}{video.road_name ? <span className="muted"> · {video.road_name}</span> : ''}
        </h2>

        {video.status === 'failed' ? (
          <Notice kind="error" title="Analysis failed">
            The analysis stopped before it finished. Delete this survey from Surveys and upload it
            again. If it fails twice, tell your system administrator.
          </Notice>
        ) : video.status === 'completed' ? (
          <p className="result-done">
            <Icon name="check" />Ready, <span className="num">{video.total_detections}</span>
            {video.total_detections === 1 ? ' damage' : ' damages'} found
          </p>
        ) : (
          <>
            <ol className="step-track">
              {steps.map((label, i) => (
                <li key={label} className={i + 1 < step ? 'done' : i + 1 === step ? 'current' : ''}
                  aria-current={i + 1 === step ? 'step' : undefined}>
                  <Icon name={i + 1 < step ? 'check' : i + 1 === step ? 'half-circle' : 'clock'} size={16} />{label}
                </li>
              ))}
            </ol>
            <p className="progress-caption">
              {video.status === 'uploaded' ? 'Waiting to start' : <>Analysing <span className="num">{Math.round(video.processing_progress || 0)}%</span></>}
            </p>
            <ProgressBar value={video.processing_progress} label="Analysis progress" />
            <p className="muted">You can leave this page. The analysis keeps going.</p>
          </>
        )}

        {finished && (
          <div className="action-row">
            {video.status === 'completed' && (
              <Link to={`/videos/${video.id}`} className="btn btn-primary">See the damage found</Link>
            )}
            {video.status === 'completed' && !hadGps && (
              <Link to={`/videos/${video.id}/georeference`} className="btn btn-secondary">
                <Icon name="map-pin-plus" />Place this survey on the map
              </Link>
            )}
            <button type="button" className={`btn ${video.status === 'failed' ? 'btn-primary' : 'btn-quiet'}`} onClick={onReset}>
              <Icon name="upload" />Upload another video
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

export default function UploadPage() {
  const [videoFile, setVideoFile] = useState(null);
  const [videoDuration, setVideoDuration] = useState(null);
  const [gpsFile, setGpsFile] = useState(null);
  const [gpsOpen, setGpsOpen] = useState(false);
  const [roadName, setRoadName] = useState('');
  const [timeOffset, setTimeOffset] = useState('0');
  const [dragover, setDragover] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState({});       // field id -> message
  const [serverError, setServerError] = useState('');
  const videoInputRef = useRef();
  const gpsInputRef = useRef();

  const setFieldError = (field, message) => setErrors(prev => {
    const next = { ...prev };
    if (message) next[field] = message; else delete next[field];
    return next;
  });

  const chooseVideo = async (f) => {
    if (!f) return;
    setServerError('');
    if (!VIDEO_EXTENSIONS.includes(extOf(f.name))) {
      setVideoFile(null);
      setFieldError('video-file', `The video must be an ${VIDEO_TYPES} file. You chose a .${extOf(f.name)} file.`);
      return;
    }
    const seconds = await readDuration(f);
    if (seconds && seconds > MAX_VIDEO_MINUTES * 60) {
      setVideoFile(null);
      setFieldError('video-file', `This video is ${formatDuration(seconds)} long. Videos must be ${MAX_VIDEO_MINUTES} minutes or shorter. Trim it and choose it again.`);
      return;
    }
    setVideoFile(f);
    setVideoDuration(seconds);
    setFieldError('video-file', null);
  };

  const chooseGps = (f) => {
    if (!f) return;
    if (!GPS_EXTENSIONS.includes(extOf(f.name))) {
      setGpsFile(null);
      setFieldError('gps-file', `The GPS track must be a .gpx or .csv file. You chose a .${extOf(f.name)} file.`);
      return;
    }
    setGpsFile(f);
    setFieldError('gps-file', null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    setServerError('');
    const found = { ...errors };
    if (!videoFile && !found['video-file']) found['video-file'] = 'Choose the survey video to upload';
    if (gpsFile && (timeOffset.trim() === '' || Number.isNaN(Number(timeOffset)))) {
      found['time-offset'] = 'Enter the time difference as a number of seconds, for example 0 or -2.5';
    }
    setErrors(found);
    if (found['gps-file'] || found['time-offset']) setGpsOpen(true);
    if (Object.keys(found).length) return;

    setUploading(true); setProgress(0);
    const formData = new FormData();
    formData.append('video', videoFile);
    if (gpsFile) formData.append('gps_file', gpsFile);
    if (roadName.trim()) formData.append('road_name', roadName.trim());
    formData.append('time_offset', gpsFile ? Number(timeOffset) : 0);

    try {
      const res = await videosAPI.upload(formData, setProgress);
      setResult(res.data.video);
    } catch (err) {
      setServerError(errorMessage(err, 'The upload did not finish. Check your connection and upload the video again.'));
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setVideoFile(null); setVideoDuration(null); setGpsFile(null); setGpsOpen(false);
    setRoadName(''); setTimeOffset('0'); setErrors({}); setResult(null); setServerError('');
  };

  if (result) return <UploadResult initialVideo={result} hadGps={Boolean(gpsFile)} onReset={reset} />;

  const summary = Object.entries(errors).map(([field, message]) => ({ field, message }));
  const describedBy = (id, hasHint = true) =>
    [hasHint && `${id}-hint`, errors[id] && `${id}-error`].filter(Boolean).join(' ') || undefined;

  return (
    <div className="page page-narrow">
      <PageHeader title="Upload a road survey" />

      <form onSubmit={handleUpload} noValidate className="stack">
        <ErrorSummary errors={summary} />
        {serverError && <Notice kind="error">{serverError}</Notice>}

        {/* Video */}
        <div className={`field${errors['video-file'] ? ' has-error' : ''}`}>
          <span className="field-label" id="video-file-label">Video</span>
          <p className="field-hint" id="video-file-hint">{VIDEO_TYPES}. {MAX_VIDEO_MINUTES} minutes or shorter.</p>
          {errors['video-file'] && <p className="field-error" id="video-file-error">{errors['video-file']}</p>}
          {videoFile ? (
            <div className="file-card">
              <Icon name="video" className="file-card-icon" />
              <div className="file-card-text">
                <span className="file-name">{videoFile.name}</span>
                <span className="muted num">{formatSize(videoFile.size)}{videoDuration ? ` · ${formatDuration(videoDuration)}` : ''}</span>
              </div>
              <button type="button" id="video-file" className="btn btn-secondary"
                aria-describedby="video-file-label" onClick={() => videoInputRef.current?.click()}>
                Change
              </button>
            </div>
          ) : (
            <div className={`dropzone${dragover ? ' is-over' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
              onDragLeave={() => setDragover(false)}
              onDrop={(e) => { e.preventDefault(); setDragover(false); chooseVideo(e.dataTransfer.files[0]); }}>
              <Icon name="video" size={32} className="dropzone-icon" />
              <span className="dropzone-text">Drag a video here, or</span>
              <button type="button" id="video-file" className="btn btn-secondary"
                aria-describedby={describedBy('video-file')} onClick={() => videoInputRef.current?.click()}>
                Choose a video
              </button>
            </div>
          )}
          <input ref={videoInputRef} type="file" hidden accept={VIDEO_EXTENSIONS.map(e => `.${e}`).join(',')}
            onChange={(e) => { chooseVideo(e.target.files[0]); e.target.value = ''; }} />
        </div>

        {/* Road name */}
        <div className="field">
          <label className="field-label" htmlFor="road-name">Road name (optional)</label>
          <p className="field-hint" id="road-name-hint">Helps you find this survey later</p>
          <input id="road-name" className="input input-medium" type="text" value={roadName} maxLength={200}
            aria-describedby="road-name-hint" onChange={(e) => setRoadName(e.target.value)} />
        </div>

        {/* GPS track: optional, closed by default */}
        <details className="details" open={gpsOpen} onToggle={(e) => setGpsOpen(e.currentTarget.open)}>
          <summary><Icon name="route" />Add a GPS track (optional)</summary>
          <div className="details-body stack">
            <div className={`field${errors['gps-file'] ? ' has-error' : ''}`}>
              <span className="field-label" id="gps-file-label">GPS track file</span>
              <p className="field-hint" id="gps-file-hint">.gpx or .csv. Without one, you can place the survey on the map by hand later.</p>
              {errors['gps-file'] && <p className="field-error" id="gps-file-error">{errors['gps-file']}</p>}
              <div className="inline-row">
                <button type="button" id="gps-file" className="btn btn-secondary"
                  aria-describedby={`gps-file-label ${describedBy('gps-file')}`} onClick={() => gpsInputRef.current?.click()}>
                  {gpsFile ? 'Choose a different file' : 'Choose a file'}
                </button>
                {gpsFile && (
                  <>
                    <span className="file-name">{gpsFile.name}</span>
                    <button type="button" className="btn btn-quiet" onClick={() => setGpsFile(null)}>Remove</button>
                  </>
                )}
              </div>
              <input ref={gpsInputRef} type="file" hidden accept=".gpx,.csv"
                onChange={(e) => { chooseGps(e.target.files[0]); e.target.value = ''; }} />
            </div>

            {gpsFile && (
              <div className={`field${errors['time-offset'] ? ' has-error' : ''}`}>
                <label className="field-label" htmlFor="time-offset">Time difference (seconds)</label>
                <p className="field-hint" id="time-offset-hint">
                  0 if both started together. Positive if the GPS started first, negative if the video started first.
                </p>
                {errors['time-offset'] && <p className="field-error" id="time-offset-error">{errors['time-offset']}</p>}
                <input id="time-offset" className="input input-short num" type="text" inputMode="decimal"
                  value={timeOffset} aria-invalid={Boolean(errors['time-offset'])}
                  aria-describedby={describedBy('time-offset')}
                  onChange={(e) => { setTimeOffset(e.target.value); setFieldError('time-offset', null); }} />
              </div>
            )}
          </div>
        </details>

        {uploading ? (
          <div className="upload-progress" aria-live="polite">
            <p className="progress-caption">Uploading <span className="num">{progress}%</span>. Keep this page open.</p>
            <ProgressBar value={progress} label="Upload progress" />
          </div>
        ) : (
          <div>
            <button type="submit" className="btn btn-primary btn-wide"><Icon name="upload" />Upload video</button>
          </div>
        )}
      </form>
    </div>
  );
}

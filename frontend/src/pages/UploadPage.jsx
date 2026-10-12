import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { videosAPI } from '../api';

export default function UploadPage() {
  const [videoFile, setVideoFile] = useState(null);
  const [gpsFile, setGpsFile] = useState(null);
  const [roadName, setRoadName] = useState('');
  const [timeOffset, setTimeOffset] = useState(0);
  const [dragover, setDragover] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const videoInputRef = useRef();
  const gpsInputRef = useRef();
  const navigate = useNavigate();

  const handleVideoFile = (f) => {
    if (f && f.type.startsWith('video/')) { setVideoFile(f); setError(''); }
    else setError('Please select a valid video file (MP4, AVI, MOV, MKV)');
  };

  const handleGpsFile = (f) => {
    if (f) {
      const ext = f.name.split('.').pop().toLowerCase();
      if (['gpx', 'csv'].includes(ext)) { setGpsFile(f); setError(''); }
      else setError('GPS file must be .gpx or .csv format. Selected: .' + ext);
    }
  };

  const handleUpload = async () => {
    if (!videoFile) return;
    setUploading(true); setProgress(0); setError('');
    const formData = new FormData();
    formData.append('video', videoFile);
    if (gpsFile) formData.append('gps_file', gpsFile);
    if (roadName) formData.append('road_name', roadName);
    formData.append('time_offset', timeOffset);

    try {
      const res = await videosAPI.upload(formData, setProgress);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  if (result) {
    return (
      <div className="page fade-in">
        <div style={{ maxWidth: '600px', margin: '60px auto', textAlign: 'center' }}>
          <div className="panel">
            <div style={{ fontSize: '64px', marginBottom: '16px' }}>✅</div>
            <h2 style={{ marginBottom: '8px' }}>Upload Successful!</h2>
            <p style={{ color: 'var(--ink-soft)', marginBottom: '8px' }}>
              Your video is now being processed. Road damage detection will begin automatically.
            </p>
            {gpsFile ? (
              <p style={{ color: 'var(--ink-soft)', fontSize: '14px', marginBottom: '16px' }}>
                GPS track attached — detections will be geo-located
              </p>
            ) : (
              <div className="alert alert-warning" style={{ textAlign: 'left' }}>
                📍 <strong>No GPS track attached.</strong> Detections won't appear on the map until you georeference
                this video by matching a few moments in the footage to landmarks on the map.
              </div>
            )}
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
              {!gpsFile && (
                <button className="btn btn-primary" onClick={() => navigate(`/videos/${result.video.id}/georeference`)}>
                  📍 Georeference Video
                </button>
              )}
              <button className={`btn ${gpsFile ? 'btn-primary' : 'btn-secondary'}`} onClick={() => navigate(`/videos/${result.video.id}`)}>
                View Processing
              </button>
              <button className="btn btn-secondary" onClick={() => { setVideoFile(null); setGpsFile(null); setResult(null); }}>
                Upload Another
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h2>Upload Road Survey</h2>
        <p>Upload road survey video and GPS track file for automated damage detection</p>
      </div>

      <div style={{ maxWidth: '700px', margin: '0 auto' }}>
        {error && <div className="alert alert-error">{error}</div>}

        {/* Video Upload Zone */}
        <div className={`upload-zone ${dragover ? 'dragover' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
          onDragLeave={() => setDragover(false)}
          onDrop={(e) => { e.preventDefault(); setDragover(false); handleVideoFile(e.dataTransfer.files[0]); }}
          onClick={() => videoInputRef.current?.click()}>
          <input ref={videoInputRef} type="file" accept="video/*" hidden onChange={(e) => handleVideoFile(e.target.files[0])} />
          <h3>{videoFile ? videoFile.name : 'Drop your road survey video here'}</h3>
          <p>{videoFile ? `${(videoFile.size / 1024 / 1024).toFixed(1)} MB` : 'Supports MP4, AVI, MOV, MKV up to 10 minutes'}</p>
        </div>

        {/* GPS File Upload — supports click, drag-and-drop */}
        <div style={{ marginTop: '20px' }}>
          <div className={`upload-zone-sm ${gpsFile ? '' : ''}`}
            onClick={() => gpsInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
            onDrop={(e) => { e.preventDefault(); e.stopPropagation(); handleGpsFile(e.dataTransfer.files[0]); }}>
            <input ref={gpsInputRef} type="file" accept="*/*" hidden onChange={(e) => handleGpsFile(e.target.files[0])} />
            <h4>{gpsFile ? `✅ ${gpsFile.name}` : 'Attach GPS Track File (optional)'}</h4>
            <p>{gpsFile ? `${(gpsFile.size / 1024).toFixed(1)} KB — GPS coordinates will be synced with detections`
              : 'Click to browse or drag & drop your .GPX or .CSV file here'}</p>
          </div>
        </div>

        {/* Road Name and Time Offset */}
        <div style={{ marginTop: '20px', display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px' }}>
          <div className="input-group">
            <label>Road Name (optional)</label>
            <input className="input-field" type="text" value={roadName}
              onChange={(e) => setRoadName(e.target.value)}
              placeholder="e.g., Manila-Cavite Expressway" />
          </div>
          <div className="input-group">
            <label>GPS Time Offset (sec)</label>
            <input className="input-field" type="number" value={timeOffset}
              onChange={(e) => setTimeOffset(parseFloat(e.target.value) || 0)}
              step="0.1" placeholder="0" />
          </div>
        </div>

        {gpsFile && (
          <div className="alert alert-info" style={{ marginTop: '16px' }}>
            💡 <strong>Time Offset:</strong> If the GPS recording started before/after the video, enter the
            difference in seconds (positive = GPS started first, negative = video started first).
          </div>
        )}

        {videoFile && (
          <div style={{ marginTop: '24px' }}>
            {uploading ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '14px' }}>Uploading...</span>
                  <span style={{ fontSize: '14px', color: 'var(--cyan)' }}>{progress}%</span>
                </div>
                <div className="progress-bar"><div className="progress-fill" style={{ width: `${progress}%` }} /></div>
              </div>
            ) : (
              <button className="btn btn-primary btn-lg" onClick={handleUpload} style={{ width: '100%', justifyContent: 'center' }}>
               Start Upload & Analysis
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { videosAPI } from '../api';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [dragover, setDragover] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const inputRef = useRef();
  const navigate = useNavigate();

  const handleFile = (f) => {
    if (f && f.type.startsWith('video/')) { setFile(f); setError(''); }
    else setError('Please select a valid video file (MP4, AVI, MOV, MKV)');
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true); setProgress(0); setError('');
    const formData = new FormData();
    formData.append('video', file);
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
          <div className="glass-card">
            <div style={{ fontSize: '64px', marginBottom: '16px' }}>✅</div>
            <h2 style={{ marginBottom: '8px' }}>Upload Successful!</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
              Your video is now being processed. Pothole detection will begin automatically.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button className="btn btn-primary" onClick={() => navigate(`/videos/${result.video.id}`)}>
                View Processing
              </button>
              <button className="btn btn-secondary" onClick={() => { setFile(null); setResult(null); }}>
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
        <h2>Upload Video</h2>
        <p>Upload road survey footage for automated pothole detection</p>
      </div>

      <div style={{ maxWidth: '700px', margin: '0 auto' }}>
        {error && <div className="alert alert-error">{error}</div>}

        <div className={`upload-zone ${dragover ? 'dragover' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
          onDragLeave={() => setDragover(false)}
          onDrop={(e) => { e.preventDefault(); setDragover(false); handleFile(e.dataTransfer.files[0]); }}
          onClick={() => inputRef.current?.click()}>
          <input ref={inputRef} type="file" accept="video/*" hidden onChange={(e) => handleFile(e.target.files[0])} />
          <div className="upload-icon">📤</div>
          <h3>{file ? file.name : 'Drop your video here or click to browse'}</h3>
          <p>{file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : 'Supports MP4, AVI, MOV, MKV up to 500MB'}</p>
        </div>

        {file && (
          <div style={{ marginTop: '24px' }}>
            {uploading ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '14px' }}>Uploading...</span>
                  <span style={{ fontSize: '14px', color: 'var(--accent)' }}>{progress}%</span>
                </div>
                <div className="progress-bar"><div className="progress-fill" style={{ width: `${progress}%` }} /></div>
              </div>
            ) : (
              <button className="btn btn-primary btn-lg" onClick={handleUpload} style={{ width: '100%', justifyContent: 'center' }}>
                🚀 Start Upload & Analysis
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

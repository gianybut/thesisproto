import { useState, useRef } from 'react';
import { reportsAPI } from '../api';

const DAMAGE_TYPES = [
  { value: 'D40', label: 'Pothole' },
  { value: 'D10', label: 'Longitudinal Crack' },
  { value: 'D20', label: 'Transverse Crack' },
  { value: 'D30', label: 'Alligator Crack' },
];

export default function PublicReportPage({ user }) {
  const [form, setForm] = useState({
    reporter_name: user?.full_name || '',
    reporter_contact: user?.email || '',
    description: '',
    damage_type: 'D40',
    manual_location: '',
    latitude: '',
    longitude: '',
  });
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [gpsStatus, setGpsStatus] = useState('idle'); // idle, loading, success, error
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const imageRef = useRef();

  const updateField = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleImage = (f) => {
    if (f && f.type.startsWith('image/')) {
      setImage(f);
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target.result);
      reader.readAsDataURL(f);
    }
  };

  const [gpsError, setGpsError] = useState('');

  const detectGPS = () => {
    setGpsError('');

    // Check if geolocation is supported
    if (!navigator.geolocation) {
      setGpsStatus('error');
      setGpsError('Geolocation is not supported by your browser.');
      return;
    }

    // Check if running on HTTPS (required for geolocation on most browsers)
    const isSecure = window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

    setGpsStatus('loading');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm(prev => ({
          ...prev,
          latitude: pos.coords.latitude.toFixed(7),
          longitude: pos.coords.longitude.toFixed(7),
        }));
        setGpsStatus('success');
      },
      (err) => {
        setGpsStatus('error');
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setGpsError('Location permission denied. Please allow location access in your browser settings and try again.');
            break;
          case err.POSITION_UNAVAILABLE:
            setGpsError('Location unavailable. Make sure your device\'s location services are enabled.');
            break;
          case err.TIMEOUT:
            setGpsError('Location request timed out. Please try again or enter coordinates manually.');
            break;
          default:
            if (!isSecure) {
              setGpsError('GPS auto-detect requires HTTPS. On localhost, enter coordinates manually or use a mobile device with GPS.');
            } else {
              setGpsError('Could not detect location. Please enter coordinates manually below.');
            }
        }
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.latitude && !form.longitude && !form.manual_location) {
      setError('Please provide a location — either use GPS detection or enter a manual location.');
      return;
    }

    setSubmitting(true);
    const formData = new FormData();
    Object.entries(form).forEach(([k, v]) => { if (v) formData.append(k, v); });
    if (image) formData.append('image', image);

    try {
      const res = await reportsAPI.submit(formData);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit report');
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <div className="page fade-in">
        <div style={{ maxWidth: '500px', margin: '60px auto', textAlign: 'center' }}>
          <div className="glass-card">
            <div style={{ fontSize: '64px', marginBottom: '16px' }}>✅</div>
            <h2 style={{ marginBottom: '8px' }}>Report Submitted!</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
              Thank you for your report. It will be reviewed by local authorities and added
              to the road damage database once validated.
            </p>
            <button className="btn btn-primary" onClick={() => { setResult(null); setImage(null); setImagePreview(null); setForm(prev => ({ ...prev, description: '', manual_location: '' })); }}>
              Submit Another Report
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page fade-in">
      <div className="page-header">
        <h2>📱 Report Road Damage</h2>
        <p>Help improve road infrastructure by reporting damage in your area</p>
      </div>

      <div className="report-form">
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          {/* Reporter Info */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div className="input-group">
              <label>Your Name (optional)</label>
              <input className="input-field" type="text" value={form.reporter_name}
                onChange={updateField('reporter_name')} placeholder="Juan Dela Cruz" />
            </div>
            <div className="input-group">
              <label>Contact (optional)</label>
              <input className="input-field" type="text" value={form.reporter_contact}
                onChange={updateField('reporter_contact')} placeholder="Email or phone" />
            </div>
          </div>

          {/* Damage Type */}
          <div className="input-group" style={{ marginBottom: '16px' }}>
            <label>Damage Type</label>
            <select className="input-field" value={form.damage_type} onChange={updateField('damage_type')}>
              {DAMAGE_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.value} — {t.label}</option>
              ))}
            </select>
          </div>

          {/* Image Upload */}
          <div className="input-group" style={{ marginBottom: '16px' }}>
            <label>Photo of Damage</label>
            <div className="upload-zone-sm" onClick={() => imageRef.current?.click()}
              style={imagePreview ? { borderColor: 'var(--success)' } : {}}>
              <input ref={imageRef} type="file" accept="image/*" hidden
                onChange={(e) => handleImage(e.target.files[0])} />
              {imagePreview ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <img src={imagePreview} alt="Preview" style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '8px' }} />
                  <div style={{ textAlign: 'left' }}>
                    <p style={{ fontWeight: '600', fontSize: '14px' }}>✅ {image.name}</p>
                    <p style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{(image.size / 1024).toFixed(0)} KB — Click to change</p>
                  </div>
                </div>
              ) : (
                <>
                  <div className="upload-icon">📷</div>
                  <h4>Take or upload a photo</h4>
                  <p>JPG, PNG, WEBP supported</p>
                </>
              )}
            </div>
          </div>

          {/* Location */}
          <div className="input-group" style={{ marginBottom: '16px' }}>
            <label>Location</label>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
              <button type="button" className={`btn ${gpsStatus === 'success' ? 'btn-success' : 'btn-secondary'}`}
                onClick={detectGPS} disabled={gpsStatus === 'loading'}>
                {gpsStatus === 'loading' ? <><span className="spinner" /> Detecting...</> :
                 gpsStatus === 'success' ? '✅ GPS Detected' : '📍 Auto-detect GPS'}
              </button>
            </div>

            {form.latitude && form.longitude && (
              <div className="alert alert-success" style={{ marginBottom: '12px' }}>
                📍 Coordinates: {form.latitude}, {form.longitude}
              </div>
            )}

            {gpsStatus === 'error' && (
              <div className="alert alert-warning" style={{ marginBottom: '12px' }}>
                ⚠️ {gpsError || 'Could not detect GPS. Please enter location manually below.'}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <input className="input-field" type="number" step="any" value={form.latitude}
                onChange={updateField('latitude')} placeholder="Latitude (e.g., 14.5995)" />
              <input className="input-field" type="number" step="any" value={form.longitude}
                onChange={updateField('longitude')} placeholder="Longitude (e.g., 120.9842)" />
            </div>

            <input className="input-field" type="text" value={form.manual_location}
              onChange={updateField('manual_location')}
              placeholder="Or describe location: e.g., Rizal Ave near City Hall, Brgy. San Jose" />
          </div>

          {/* Description */}
          <div className="input-group" style={{ marginBottom: '24px' }}>
            <label>Description (optional)</label>
            <textarea className="input-field" value={form.description}
              onChange={updateField('description')}
              placeholder="Describe the damage, size, and any safety concerns..." />
          </div>

          <button type="submit" className="btn btn-primary btn-lg" disabled={submitting}
            style={{ width: '100%', justifyContent: 'center' }}>
            {submitting ? <span className="spinner" /> : '📤 Submit Report'}
          </button>
        </form>
      </div>
    </div>
  );
}

import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Signed token from /auth/login (backend/auth_tokens.py). It expires; any 401
// outside the login call clears it and fires AUTH_EXPIRED, which App.jsx turns
// into a return to the login screen.
export const TOKEN_KEY = 'token';
export const AUTH_EXPIRED = 'auth:expired';
const getToken = () => localStorage.getItem(TOKEN_KEY);

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !err.config?.url?.endsWith('/auth/login')) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem('user');
      window.dispatchEvent(new CustomEvent(AUTH_EXPIRED, { detail: err.response.data?.error }));
    }
    return Promise.reject(err);
  },
);

// <video>/<img> src cannot send a header, so media URLs carry the token as a
// query parameter; the backend accepts it on those endpoints only.
const withToken = (url) => `${url}?token=${encodeURIComponent(getToken() || '')}`;

// There is no self-registration: a system administrator creates accounts (accountsAPI).
export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
};

export const videosAPI = {
  upload: (formData, onProgress) =>
    api.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / e.total)),
    }),
  list: () => api.get('/videos'),
  get: (id) => api.get(`/videos/${id}`),
  rename: (id, name) => api.patch(`/videos/${id}`, { name }),
  delete: (id) => api.delete(`/videos/${id}`),
  streamUrl: (id) => withToken(`${API_BASE}/videos/${id}/stream`),
  processedUrl: (id) => withToken(`${API_BASE}/videos/${id}/processed`),
  snapshotUrl: (videoId, filename) => withToken(`${API_BASE}/videos/${videoId}/snapshot/${filename}`),
  // Manual georeferencing (videos without a GPS track)
  getControlPoints: (id) => api.get(`/videos/${id}/control-points`),
  saveControlPoints: (id, points) => api.post(`/videos/${id}/control-points`, { control_points: points }),
  deleteControlPoint: (id, cpId) => api.delete(`/videos/${id}/control-points/${cpId}`),
};

export const dashboardAPI = {
  stats: () => api.get('/dashboard/stats'),
};

export const detectionsAPI = {
  getForVideo: (videoId) => api.get(`/detections/${videoId}`),
};

// Every map call takes an optional videoId so one survey can be viewed on its own.
const videoParam = (videoId) => (videoId ? `?video_id=${videoId}` : '');

export const mapAPI = {
  getDetections: (filters = {}, videoId) => {
    const params = new URLSearchParams();
    if (videoId) params.append('video_id', videoId);
    if (filters.damage_type) params.append('damage_type', filters.damage_type);
    if (filters.status) params.append('status', filters.status);
    if (filters.min_confidence) params.append('min_confidence', filters.min_confidence);
    return api.get(`/map/detections?${params.toString()}`);
  },
  getGpsTracks: (videoId) => api.get(`/map/gps-tracks${videoParam(videoId)}`),
  getStats: (videoId) => api.get(`/map/stats${videoParam(videoId)}`),
  getMappedVideos: () => api.get('/map/videos'),
};

export const databaseAPI = {
  getDetections: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v) query.append(k, v); });
    return api.get(`/database/detections?${query.toString()}`);
  },
  updateStatus: (id, data) => api.put(`/database/detections/${id}/status`, data),
  // Admin only ("Manage detections"); the server answers 403 to anyone else.
  correct: (id, data) => api.patch(`/database/detections/${id}`, data),
  remove: (id) => api.delete(`/database/detections/${id}`),
  exportData: (format = 'csv') => api.get(`/database/export?format=${format}`, { responseType: 'blob' }),
  getStats: () => api.get('/database/stats'),
};

// Administration (admin only; the server answers 403 to anyone else).
export const accountsAPI = {
  list: () => api.get('/accounts'),
  create: (data) => api.post('/accounts', data),
  update: (id, data) => api.patch(`/accounts/${id}`, data),
  resetPassword: (id, password) => api.put(`/accounts/${id}/password`, { password }),
};

export const activityAPI = {
  list: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v) query.append(k, v); });
    return api.get(`/activity?${query.toString()}`);
  },
};

export default api;

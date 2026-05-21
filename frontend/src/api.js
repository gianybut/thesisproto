import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  if (user) {
    config.headers.Authorization = `Bearer ${user.id}`;
  }
  return config;
});

export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (data) => {
    // If data is FormData (has file), use multipart
    if (data instanceof FormData) {
      return api.post('/auth/register', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    }
    return api.post('/auth/register', data);
  },
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
};

export const accountsAPI = {
  getPending: () => api.get('/accounts/pending'),
  getAll: (status) => api.get(`/accounts/all${status ? `?status=${status}` : ''}`),
  approve: (id) => api.put(`/accounts/${id}/approve`),
  reject: (id, reason) => api.put(`/accounts/${id}/reject`, { reason }),
  getStats: () => api.get('/accounts/stats'),
  idPhotoUrl: (filename) => `${API_BASE}/accounts/id-photo/${filename}`,
};

export const videosAPI = {
  upload: (formData, onProgress) =>
    api.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / e.total)),
    }),
  list: () => api.get('/videos'),
  get: (id) => api.get(`/videos/${id}`),
  delete: (id) => api.delete(`/videos/${id}`),
  streamUrl: (id) => `${API_BASE}/videos/${id}/stream`,
  processedUrl: (id) => `${API_BASE}/videos/${id}/processed`,
  snapshotUrl: (videoId, filename) => `${API_BASE}/videos/${videoId}/snapshot/${filename}`,
};

export const dashboardAPI = {
  stats: () => api.get('/dashboard/stats'),
};

export const detectionsAPI = {
  getForVideo: (videoId) => api.get(`/detections/${videoId}`),
};

export const mapAPI = {
  getDetections: (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.damage_type) params.append('damage_type', filters.damage_type);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.status) params.append('status', filters.status);
    if (filters.min_confidence) params.append('min_confidence', filters.min_confidence);
    return api.get(`/map/detections?${params.toString()}`);
  },
  getGpsTracks: () => api.get('/map/gps-tracks'),
  getStats: () => api.get('/map/stats'),
};

export const reportsAPI = {
  submit: (formData) =>
    api.post('/reports', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: (status) => api.get(`/reports${status ? `?status=${status}` : ''}`),
  get: (id) => api.get(`/reports/${id}`),
  validate: (id) => api.put(`/reports/${id}/validate`),
  reject: (id, reason) => api.put(`/reports/${id}/reject`, { reason }),
  imageUrl: (filename) => `${API_BASE}/reports/image/${filename}`,
};

export const databaseAPI = {
  getDetections: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v) query.append(k, v); });
    return api.get(`/database/detections?${query.toString()}`);
  },
  updateStatus: (id, data) => api.put(`/database/detections/${id}/status`, data),
  exportData: (format = 'csv') => api.get(`/database/export?format=${format}`, { responseType: 'blob' }),
  getStats: () => api.get('/database/stats'),
};

export default api;

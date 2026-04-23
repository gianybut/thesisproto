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
  register: (data) => api.post('/auth/register', data),
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

export default api;

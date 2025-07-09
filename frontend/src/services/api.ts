import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials: { email: string; password: string }) =>
    api.post('/api/v1/auth/login', credentials),
  
  register: (userData: { email: string; password: string; first_name: string; last_name: string }) =>
    api.post('/api/v1/auth/register', userData),
  
  refreshToken: () =>
    api.post('/api/v1/auth/refresh'),
  
  logout: () =>
    api.post('/api/v1/auth/logout'),
};

// User API
export const userAPI = {
  getProfile: () =>
    api.get('/api/v1/users/profile'),
  
  updateProfile: (profileData: any) =>
    api.put('/api/v1/users/profile', profileData),
  
  getSettings: () =>
    api.get('/api/v1/users/settings'),
  
  updateSettings: (settings: any) =>
    api.put('/api/v1/users/settings', settings),
};

// Work Items API
export const workItemsAPI = {
  getWorkItems: (params?: any) =>
    api.get('/api/v1/ai/work-items', { params }),
  
  getWorkItem: (id: string) =>
    api.get(`/api/v1/ai/work-items/${id}`),
  
  createWorkItem: (workItem: any) =>
    api.post('/api/v1/ai/work-items', workItem),
  
  updateWorkItem: (id: string, workItem: any) =>
    api.put(`/api/v1/ai/work-items/${id}`, workItem),
  
  deleteWorkItem: (id: string) =>
    api.delete(`/api/v1/ai/work-items/${id}`),
  
  startTimer: (id: string) =>
    api.post(`/api/v1/ai/work-items/${id}/start`),
  
  stopTimer: (id: string) =>
    api.post(`/api/v1/ai/work-items/${id}/stop`),
};

// Data Collection API
export const dataCollectionAPI = {
  getActivities: (params?: any) =>
    api.get('/api/v1/data/activities', { params }),
  
  createActivity: (activity: any) =>
    api.post('/api/v1/data/activities', activity),
  
  updateActivity: (id: string, activity: any) =>
    api.put(`/api/v1/data/activities/${id}`, activity),
  
  deleteActivity: (id: string) =>
    api.delete(`/api/v1/data/activities/${id}`),
  
  getTimeEntries: (params?: any) =>
    api.get('/api/v1/data/time-entries', { params }),
  
  createTimeEntry: (timeEntry: any) =>
    api.post('/api/v1/data/time-entries', timeEntry),
};

// Reports API
export const reportsAPI = {
  getReports: (params?: any) =>
    api.get('/api/v1/reports', { params }),
  
  generateReport: (reportData: any) =>
    api.post('/api/v1/reports/generate', reportData),
  
  getReport: (id: string) =>
    api.get(`/api/v1/reports/${id}`),
  
  downloadReport: (id: string) =>
    api.get(`/api/v1/reports/${id}/download`, { responseType: 'blob' }),
};

// Notifications API
export const notificationsAPI = {
  getNotifications: (params?: any) =>
    api.get('/api/v1/notifications', { params }),
  
  markAsRead: (id: string) =>
    api.put(`/api/v1/notifications/${id}/read`),
  
  markAllAsRead: () =>
    api.put('/api/v1/notifications/read-all'),
  
  updatePreferences: (preferences: any) =>
    api.put('/api/v1/notifications/preferences', preferences),
};

export default api; 
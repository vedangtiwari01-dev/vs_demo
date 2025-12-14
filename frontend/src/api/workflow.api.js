import apiClient from './client';

export const workflowAPI = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('logs', file);

    const response = await apiClient.post('/workflows/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  list: async (params = {}) => {
    const response = await apiClient.get('/workflows', { params });
    return response.data;
  },

  getByCase: async (caseId) => {
    const response = await apiClient.get(`/workflows/${caseId}`);
    return response.data;
  },

  analyze: async () => {
    const response = await apiClient.post('/workflows/analyze');
    return response.data;
  },

  analyzePatterns: async () => {
    const response = await apiClient.post('/workflows/analyze-patterns');
    return response.data;
  },
};

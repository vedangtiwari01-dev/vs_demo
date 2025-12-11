import apiClient from './client';

export const deviationAPI = {
  list: async (params = {}) => {
    const response = await apiClient.get('/deviations', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await apiClient.get(`/deviations/${id}`);
    return response.data;
  },

  getSummary: async () => {
    const response = await apiClient.get('/deviations/summary');
    return response.data;
  },

  getByOfficer: async () => {
    const response = await apiClient.get('/deviations/by-officer');
    return response.data;
  },

  getByType: async () => {
    const response = await apiClient.get('/deviations/by-type');
    return response.data;
  },
};

export const behavioralAPI = {
  listOfficers: async () => {
    const response = await apiClient.get('/behavioral/officers');
    return response.data;
  },

  getOfficerProfile: async (id) => {
    const response = await apiClient.get(`/behavioral/officers/${id}`);
    return response.data;
  },

  buildProfile: async (officerId) => {
    const response = await apiClient.post('/behavioral/officers/profile', {
      officer_id: officerId,
    });
    return response.data;
  },

  getPatterns: async (officerId = null) => {
    const params = officerId ? { officer_id: officerId } : {};
    const response = await apiClient.get('/behavioral/patterns', { params });
    return response.data;
  },

  analyzePatterns: async (officerId) => {
    const response = await apiClient.post('/behavioral/patterns/analyze', {
      officer_id: officerId,
    });
    return response.data;
  },

  getRiskMatrix: async () => {
    const response = await apiClient.get('/behavioral/risk-matrix');
    return response.data;
  },
};

export const stressTestAPI = {
  createScenario: async (data) => {
    const response = await apiClient.post('/stress-test/scenarios', data);
    return response.data;
  },

  listScenarios: async () => {
    const response = await apiClient.get('/stress-test/scenarios');
    return response.data;
  },

  generateLogs: async (data) => {
    const response = await apiClient.post('/stress-test/generate', data);
    return response.data;
  },
};

export const analyticsAPI = {
  getDashboard: async () => {
    const response = await apiClient.get('/analytics/dashboard');
    return response.data;
  },

  getComplianceRate: async (params = {}) => {
    const response = await apiClient.get('/analytics/compliance-rate', { params });
    return response.data;
  },

  getTrends: async (days = 30) => {
    const response = await apiClient.get('/analytics/trends', { params: { days } });
    return response.data;
  },

  getProcessFlow: async () => {
    const response = await apiClient.get('/analytics/process-flow');
    return response.data;
  },
};

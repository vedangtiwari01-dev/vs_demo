import apiClient from './client';

export const sopAPI = {
  upload: async (file, title, version) => {
    const formData = new FormData();
    formData.append('sop', file);
    if (title) formData.append('title', title);
    if (version) formData.append('version', version);

    const response = await apiClient.post('/sops/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  list: async () => {
    const response = await apiClient.get('/sops');
    return response.data;
  },

  getById: async (id) => {
    const response = await apiClient.get(`/sops/${id}`);
    return response.data;
  },

  process: async (id) => {
    const response = await apiClient.post(`/sops/${id}/process`);
    return response.data;
  },

  getRules: async (id) => {
    const response = await apiClient.get(`/sops/${id}/rules`);
    return response.data;
  },

  delete: async (id) => {
    const response = await apiClient.delete(`/sops/${id}`);
    return response.data;
  },
};

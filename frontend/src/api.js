import axios from 'axios';

const API_BASE = 'http://127.0.0.1:5055/api';

export const api = {
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return axios.post(`${API_BASE}/upload-pptx`, formData);
  },
  
  editPresentation: async (fileId, prompt) => {
    return axios.post(`${API_BASE}/edit-presentation`, { file_id: fileId, prompt });
  },
  
  getSlides: async () => {
    return axios.get(`${API_BASE}/slides`);
  },
  
  getTemplates: async () => {
    return axios.get(`${API_BASE}/templates`);
  },
  
  updateSlide: async (index, data) => {
    return axios.post(`${API_BASE}/slides/${index}`, data);
  },
  
  sendChat: async (message, template = "random") => {
    // Используем process-prompt вместо chat
    return axios.post(`${API_BASE}/process-prompt`, { prompt: message, template });
  },

  draftPresentation: async (prompt) => {
    return axios.post(`${API_BASE}/draft-presentation`, { prompt });
  },

  compilePresentation: async (topic, slides_content, template) => {
    return axios.post(`${API_BASE}/compile-presentation`, { topic, slides_content, template });
  },
  
  searchFacts: async (query) => {
    return axios.get(`${API_BASE}/search`, { params: { query } });
  },
  
  insertFact: async (slideIndex, factData) => {
    return axios.post(`${API_BASE}/insert`, { slideIndex, factData });
  },
  
  getHistory: async () => {
    return axios.get(`${API_BASE}/history`);
  },
  
  restoreHistory: async (versionId) => {
    return axios.post(`${API_BASE}/restore`, { versionId });
  },
  
  saveSettings: async (settings) => {
    return axios.post(`${API_BASE}/settings`, settings);
  }
};

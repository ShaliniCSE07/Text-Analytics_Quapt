import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

export const getReviews = async (filters = {}) => {
  const response = await api.get('/reviews', { params: filters });
  return response.data;
};

export const getSummary = async () => {
  const response = await api.get('/reviews/summary');
  return response.data;
};

export const submitCorrection = async (data) => {
  const response = await api.patch('/reviews/correct', data);
  return response.data;
};

export const getTrend = async () => {
  const response = await api.get('/reviews/trend');
  return response.data;
};

export const getByProduct = async () => {
  const response = await api.get('/reviews/by-product');
  return response.data;
};

export const getSummaryText = async (filters = {}) => {
  const response = await api.get('/reviews/summary-text', { params: filters });
  return response.data;
};

export const getKeywords = async (filters = {}) => {
  const response = await api.get('/reviews/keywords', { params: filters });
  return response.data;
};

export const getLowConfidence = async (threshold = 60) => {
  const response = await api.get('/reviews/low-confidence', { params: { threshold } });
  return response.data;
};

export const getSpikeCheck = async () => {
  const response = await api.get('/reviews/spike-check');
  return response.data;
};

export const getTopics = async () => {
  const response = await api.get('/admin/topics');
  return response.data;
};

export const addTopic = async (name, description) => {
  const response = await api.post('/admin/topics', { name, description });
  return response.data;
};

export const updateTopic = async (name, description) => {
  const response = await api.put(`/admin/topics/${name}`, { description });
  return response.data;
};

export const deleteTopic = async (name) => {
  const response = await api.delete(`/admin/topics/${name}`);
  return response.data;
};

export const getReviewDetail = async (platformReferenceId) => {
  const response = await api.get(`/reviews/${platformReferenceId}`);
  return response.data;
};

export const getEmotions = async (filters = {}) => {
  const response = await api.get('/reviews/emotions', { params: filters });
  return response.data;
};

export const getEmotionsSummary = async () => {
  const response = await api.get('/reviews/emotions/summary');
  return response.data;
};

export const getEmotionsTrend = async () => {
  const response = await api.get('/reviews/emotions/trend');
  return response.data;
};

export const analyzeEmotions = async (force = false) => {
  const response = await api.post('/analyze-emotions', { force });
  return response.data;
};


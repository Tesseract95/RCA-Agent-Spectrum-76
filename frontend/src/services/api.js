/**
 * API service for the Network Investigation Agent
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Health check
 */
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

/**
 * Send a chat message to the agent
 */
export const sendChatMessage = async (message, threadId = null) => {
  const response = await api.post('/chat', {
    message,
    thread_id: threadId,
  });
  return response.data;
};

/**
 * Get all anomalies
 */
export const getAnomalies = async () => {
  const response = await api.get('/anomalies');
  return response.data;
};

/**
 * Get anomaly details
 */
export const getAnomalyDetails = async (anomalyId) => {
  const response = await api.get(`/anomalies/${anomalyId}`);
  return response.data;
};

/**
 * Investigate an anomaly
 */
export const investigateAnomaly = async (anomalyId, threadId = null) => {
  const response = await api.post(`/investigate/${anomalyId}`, null, {
    params: { thread_id: threadId },
  });
  return response.data;
};

export default api;

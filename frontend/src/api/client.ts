import axios from 'axios';
import { API_BASE_URL } from '../lib/config';
import { normalizeApiError } from '../lib/errors';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalized = normalizeApiError(error);
    return Promise.reject(normalized);
  }
);

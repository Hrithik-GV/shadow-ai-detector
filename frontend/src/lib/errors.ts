import axios, { AxiosError } from 'axios';
import type { ApiError } from '../types';
import { API_BASE_URL } from './config';

/**
 * Normalizes unknown errors or Axios errors into a consistent ApiError object.
 */
export function normalizeApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{
      message?: string;
      detail?: string;
      error?: string;
    }>;

    if (axiosErr.code === 'ECONNABORTED' || axiosErr.message?.includes('timeout')) {
      return {
        message: 'Request timed out. The backend server took too long to respond.',
        code: 'TIMEOUT',
        status: 408,
      };
    }

    if (!axiosErr.response) {
      return {
        message: `Unable to connect to backend at ${API_BASE_URL}. Ensure the server is running.`,
        code: axiosErr.code || 'NETWORK_ERROR',
        status: 0,
      };
    }

    const resData = axiosErr.response.data;
    const serverMessage =
      (typeof resData === 'object' && resData !== null
        ? resData.detail || resData.message || resData.error
        : undefined) || axiosErr.response.statusText;

    return {
      message:
        typeof serverMessage === 'string'
          ? serverMessage
          : `HTTP ${axiosErr.response.status}: Request failed.`,
      status: axiosErr.response.status,
      code: axiosErr.code || `HTTP_${axiosErr.response.status}`,
      details: resData,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      code: 'CLIENT_ERROR',
    };
  }

  return {
    message: 'An unexpected error occurred while communicating with the API.',
    code: 'UNKNOWN_ERROR',
  };
}

/**
 * Helper to extract user-facing error message string
 */
export function getErrorMessage(error: unknown): string {
  return normalizeApiError(error).message;
}

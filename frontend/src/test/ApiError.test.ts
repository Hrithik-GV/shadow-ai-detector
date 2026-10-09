import { describe, it, expect } from 'vitest';
import { normalizeApiError, getErrorMessage } from '../lib/errors';
import axios from 'axios';

describe('API Error Normalization', () => {
  it('normalizes standard JavaScript Error', () => {
    const error = new Error('Client calculation failed');
    const normalized = normalizeApiError(error);

    expect(normalized.message).toBe('Client calculation failed');
    expect(normalized.code).toBe('CLIENT_ERROR');
    expect(getErrorMessage(error)).toBe('Client calculation failed');
  });

  it('normalizes network error without response', () => {
    const error = new axios.AxiosError('Network Error', 'ERR_NETWORK');
    const normalized = normalizeApiError(error);

    expect(normalized.message).toContain('Unable to connect to backend at');
    expect(normalized.status).toBe(0);
  });

  it('normalizes timeout error', () => {
    const error = new axios.AxiosError('timeout of 15000ms exceeded', 'ECONNABORTED');
    const normalized = normalizeApiError(error);

    expect(normalized.message).toContain('Request timed out');
    expect(normalized.status).toBe(408);
  });

  it('normalizes HTTP response error with detail field', () => {
    const error = new axios.AxiosError(
      'Request failed with status code 404',
      'ERR_BAD_REQUEST',
      undefined,
      undefined,
      {
        status: 404,
        statusText: 'Not Found',
        data: { detail: 'Endpoint not discovered in catalog' },
        headers: {},
        config: {} as any,
      }
    );

    const normalized = normalizeApiError(error);
    expect(normalized.message).toBe('Endpoint not discovered in catalog');
    expect(normalized.status).toBe(404);
  });
});

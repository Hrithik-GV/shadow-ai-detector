/**
 * Application environment configuration.
 * VITE_API_BASE_URL defaults to http://localhost:8000 for local development.
 * Trailing slashes are stripped to prevent malformed double-slash endpoints.
 */
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;

export const API_BASE_URL: string =
  rawBaseUrl !== undefined && rawBaseUrl.trim() !== ''
    ? rawBaseUrl.trim().replace(/\/+$/, '')
    : 'http://localhost:8000';

/**
 * Application environment configuration.
 * VITE_API_BASE_URL defaults to http://localhost:8000 for local development.
 */
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://localhost:8000';

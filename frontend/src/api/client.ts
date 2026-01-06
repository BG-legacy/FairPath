/**
 * Legacy API Client Export
 * Re-exports from the new services/apiClient.ts for backward compatibility
 * @deprecated Use '../services/apiClient' instead
 */
export { default as apiClient, default } from '../services/apiClient';
export type { ApiError, AxiosInstance, AxiosError, AxiosRequestConfig } from '../services/apiClient';


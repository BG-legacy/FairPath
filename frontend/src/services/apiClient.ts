/**
 * API Client Service
 * Enhanced axios client with interceptors, error handling, and configuration
 */
import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios';
import { apiConfig } from '../config/api';
import { sanitizeErrorMessage } from '../utils/errorHandler';

/**
 * Create axios instance with base configuration
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: apiConfig.timeout.default,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor
 * - Adds auth headers if needed
 * - Validates request size
 * - Adds request metadata
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token if available (for future use)
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Validate request size for non-upload requests
    const contentType = config.headers?.['Content-Type'];
    const isMultipartFormData = typeof contentType === 'string' && contentType.includes('multipart/form-data');
    if (config.data && !isMultipartFormData) {
      const requestSize = JSON.stringify(config.data).length;
      if (requestSize > apiConfig.maxRequestSize) {
        return Promise.reject(
          new Error(`Request size (${(requestSize / 1024).toFixed(2)}KB) exceeds maximum allowed size (${apiConfig.maxRequestSize / 1024}KB)`)
        );
      }
    }

    // Set timeout based on endpoint type
    if (config.url?.includes('/openai') || config.url?.includes('/coach') || config.url?.includes('/resume') || config.url?.includes('/recommendations')) {
      config.timeout = apiConfig.timeout.openai;
    } else if (isMultipartFormData) {
      config.timeout = apiConfig.timeout.upload;
    }

    // Log request for debugging (only in development)
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, {
        timeout: config.timeout,
        hasData: !!config.data,
      });
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor
 * - Handles errors globally
 * - Sanitizes error messages
 * - Provides consistent error format
 */
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle timeout errors
    if (error.code === 'ECONNABORTED' || error.message?.toLowerCase().includes('timeout')) {
      const timeoutError = {
        message: 'Request timed out. Please try again.',
        code: 'TIMEOUT_ERROR',
        status: 504,
        originalError: error.message,
      };
      console.error('[API Timeout Error]', timeoutError);
      return Promise.reject(timeoutError);
    }

    // Handle network errors (no response)
    if (!error.response) {
      // Check if it's a network connectivity issue
      const isNetworkError = error.code === 'ERR_NETWORK' || 
                            error.code === 'ECONNREFUSED' ||
                            error.message?.toLowerCase().includes('network');
      
      const networkError = {
        message: isNetworkError 
          ? 'Network error. Please check your internet connection and try again.'
          : 'Unable to reach the server. Please try again later.',
        code: isNetworkError ? 'NETWORK_ERROR' : 'CONNECTION_ERROR',
        originalError: error.message,
      };
      console.error('[API Network Error]', networkError);
      return Promise.reject(networkError);
    }

    // Handle HTTP errors
    const status = error.response.status;
    const responseData = error.response.data as any;

    // Sanitize error message to prevent sensitive data exposure
    const sanitizedMessage = sanitizeErrorMessage(
      responseData?.message || responseData?.detail || error.message || 'An unexpected error occurred'
    );

    // Map error codes from backend
    const errorCode = responseData?.error || `HTTP_${status}`;

    const apiError = {
      message: sanitizedMessage,
      code: errorCode,
      status,
      data: responseData,
      originalError: error,
    };

    // Log error for debugging (only in development)
    if (import.meta.env.DEV) {
      console.error('[API Error]', {
        url: error.config?.url,
        method: error.config?.method,
        status,
        code: errorCode,
        message: sanitizedMessage,
      });
    }

    return Promise.reject(apiError);
  }
);

export default apiClient;

/**
 * Helper function to create a request with custom timeout
 */
export const createRequestWithTimeout = (timeout: number): AxiosInstance => {
  return axios.create({
    baseURL: apiConfig.baseURL,
    timeout,
    headers: {
      'Content-Type': 'application/json',
    },
  });
};

/**
 * Type definitions for API errors
 */
export interface ApiError {
  message: string;
  code: string;
  status?: number;
  data?: any;
  originalError?: any;
}

export type { AxiosInstance, AxiosError, AxiosRequestConfig };


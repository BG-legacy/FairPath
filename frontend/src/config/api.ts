/**
 * API Configuration
 * Centralized configuration for API base URL and endpoints
 */

/**
 * Get the API base URL from environment variables
 * Defaults to http://localhost:8000 for local development
 * Set VITE_API_BASE_URL in .env file for production (e.g., Heroku backend)
 */
export const getApiBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
};

/**
 * API Configuration object
 */
export const apiConfig = {
  baseURL: getApiBaseUrl(),
  timeout: {
    default: 30000, // 30 seconds for general requests
    openai: 120000, // 120 seconds (2 minutes) for OpenAI endpoints - allows time for multiple API calls
    upload: 60000, // 60 seconds for file uploads
  },
  maxRequestSize: 1024 * 1024, // 1MB for general requests
  maxUploadSize: 10 * 1024 * 1024, // 10MB for file uploads
} as const;

/**
 * API Endpoints
 * Centralized endpoint definitions for type safety
 */
export const apiEndpoints = {
  health: '/health',
  version: '/version',
  trustPanel: '/trust-panel',
  modelCards: '/model-cards',
  // Add more endpoints as needed
} as const;

export default apiConfig;


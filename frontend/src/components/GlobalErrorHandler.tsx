/**
 * Global Error Handler Component
 * Handles unhandled errors and API errors globally
 */
import { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { toastConfig, handleApiError } from '../utils/toast';

/**
 * Global Error Handler Component
 * Sets up global error handlers and toast notifications
 */
export const GlobalErrorHandler = () => {
  useEffect(() => {
    // Handle unhandled promise rejections
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      console.error('Unhandled promise rejection:', event.reason);
      
      // Only show toast for API errors, not for all unhandled rejections
      // This prevents spam from other async errors
      if (event.reason && typeof event.reason === 'object' && 'code' in event.reason) {
        handleApiError(event.reason);
      }
    };

    // Handle global JavaScript errors
    const handleError = (event: ErrorEvent) => {
      console.error('Global error:', event.error);
      // Don't show toast for all global errors to avoid spam
      // ErrorBoundary will handle React component errors
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    window.addEventListener('error', handleError);

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      window.removeEventListener('error', handleError);
    };
  }, []);

  return <Toaster {...toastConfig} />;
};

export default GlobalErrorHandler;


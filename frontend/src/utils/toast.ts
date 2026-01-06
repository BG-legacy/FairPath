/**
 * Toast Notification Utilities
 * Centralized toast notification system for API errors and user feedback
 */
import toast, { ToastOptions } from 'react-hot-toast';
import { getUserFriendlyErrorMessage, isNetworkError, isTimeoutError } from './errorHandler';

/**
 * Show error toast notification
 */
export const showErrorToast = (error: unknown, options?: ToastOptions) => {
  const message = getUserFriendlyErrorMessage(error);
  
  toast.error(message, {
    duration: 5000,
    position: 'top-right',
    ...options,
  });
};

/**
 * Show success toast notification
 */
export const showSuccessToast = (message: string, options?: ToastOptions) => {
  toast.success(message, {
    duration: 3000,
    position: 'top-right',
    ...options,
  });
};

/**
 * Show info toast notification
 */
export const showInfoToast = (message: string, options?: ToastOptions) => {
  toast(message, {
    duration: 3000,
    position: 'top-right',
    icon: 'ℹ️',
    ...options,
  });
};

/**
 * Show warning toast notification
 */
export const showWarningToast = (message: string, options?: ToastOptions) => {
  toast(message, {
    duration: 4000,
    position: 'top-right',
    icon: '⚠️',
    ...options,
  });
};

/**
 * Show loading toast notification
 * Returns a function to update/remove the toast
 */
export const showLoadingToast = (message: string = 'Loading...'): (() => void) => {
  const toastId = toast.loading(message, {
    position: 'top-right',
  });

  return () => {
    toast.dismiss(toastId);
  };
};

/**
 * Handle API error with appropriate toast notification
 */
export const handleApiError = (error: unknown, customMessage?: string) => {
  if (customMessage) {
    showErrorToast(customMessage);
    return;
  }

  if (isNetworkError(error)) {
    showErrorToast('Network error. Please check your connection.');
    return;
  }

  if (isTimeoutError(error)) {
    showErrorToast('Request timed out. Please try again.');
    return;
  }

  showErrorToast(error);
};

/**
 * Toast configuration for the app
 */
export const toastConfig: ToastOptions = {
  duration: 4000,
  position: 'top-right',
  style: {
    borderRadius: '0.5rem',
    background: '#333',
    color: '#fff',
    padding: '1rem',
    fontSize: '0.875rem',
  },
};


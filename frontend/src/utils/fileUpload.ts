/**
 * File Upload Utilities
 * Centralized utilities for file upload handling, validation, and processing
 */

import { apiConfig } from '../config/api';

/**
 * File upload constants
 */
export const MAX_FILE_SIZE = apiConfig.maxUploadSize; // 10MB
export const ALLOWED_FILE_TYPES = ['pdf', 'docx', 'txt'] as const;
export const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
] as const;

export type AllowedFileType = typeof ALLOWED_FILE_TYPES[number];
export type AllowedMimeType = typeof ALLOWED_MIME_TYPES[number];

/**
 * File validation error types
 */
export interface FileValidationError {
  type: 'size' | 'type' | 'name' | 'empty';
  message: string;
}

/**
 * File metadata interface
 */
export interface FileMetadata {
  name: string;
  size: number;
  type: string;
  lastModified: number;
  extension: string;
  formattedSize: string;
}

/**
 * Upload progress callback type
 */
export type UploadProgressCallback = (progress: number) => void;

/**
 * Format file size to human-readable string
 * @param bytes - File size in bytes
 * @returns Formatted file size string (e.g., "1.5 MB")
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

/**
 * Sanitize filename to prevent security issues
 * Removes path traversal attempts, null bytes, and unsafe characters
 * @param filename - Original filename
 * @returns Sanitized filename
 */
export const sanitizeFilename = (filename: string): string => {
  if (!filename) return 'file';

  // Remove path traversal attempts
  let sanitized = filename.replace(/\.\./g, '');
  sanitized = sanitized.replace(/\//g, '_');
  sanitized = sanitized.replace(/\\/g, '_');

  // Remove null bytes
  sanitized = sanitized.replace(/\x00/g, '');

  // Remove unsafe characters
  const unsafeChars = /[<>:"|?*]/g;
  sanitized = sanitized.replace(unsafeChars, '_');

  // Limit length
  if (sanitized.length > 255) {
    const ext = sanitized.split('.').pop();
    const nameWithoutExt = sanitized.substring(0, sanitized.lastIndexOf('.'));
    const maxNameLength = 255 - (ext ? ext.length + 1 : 0);
    sanitized = nameWithoutExt.substring(0, maxNameLength) + (ext ? '.' + ext : '');
  }

  return sanitized.trim() || 'file';
};

/**
 * Validate file size
 * @param file - File object to validate
 * @param maxSize - Maximum allowed size in bytes (default: MAX_FILE_SIZE)
 * @returns Validation error if invalid, undefined if valid
 */
export const validateFileSize = (
  file: File,
  maxSize: number = MAX_FILE_SIZE
): FileValidationError | undefined => {
  if (file.size > maxSize) {
    return {
      type: 'size',
      message: `File size (${formatFileSize(file.size)}) exceeds maximum allowed size (${formatFileSize(maxSize)})`,
    };
  }
  return undefined;
};

/**
 * Validate file type by extension
 * @param filename - File name to validate
 * @returns Validation error if invalid, undefined if valid
 */
export const validateFileType = (filename: string): FileValidationError | undefined => {
  if (!filename || filename.trim().length === 0) {
    return {
      type: 'name',
      message: 'Filename is required',
    };
  }

  const extension = filename.split('.').pop()?.toLowerCase();
  if (!extension || !ALLOWED_FILE_TYPES.includes(extension as AllowedFileType)) {
    return {
      type: 'type',
      message: `File type '${extension || 'unknown'}' not supported. Allowed types: ${ALLOWED_FILE_TYPES.join(', ')}`,
    };
  }

  return undefined;
};

/**
 * Validate file by MIME type
 * @param file - File object to validate
 * @returns Validation error if invalid, undefined if valid
 */
export const validateFileMimeType = (file: File): FileValidationError | undefined => {
  if (!file.type) {
    // Some browsers may not provide MIME type, so we'll fall back to extension validation
    return undefined;
  }

  if (!ALLOWED_MIME_TYPES.includes(file.type as AllowedMimeType)) {
    return {
      type: 'type',
      message: `File type '${file.type}' not supported. Allowed types: ${ALLOWED_MIME_TYPES.join(', ')}`,
    };
  }

  return undefined;
};

/**
 * Validate filename (prevent path traversal and unsafe characters)
 * @param filename - File name to validate
 * @returns Validation error if invalid, undefined if valid
 */
export const validateFilename = (filename: string): FileValidationError | undefined => {
  if (!filename || filename.trim().length === 0) {
    return {
      type: 'name',
      message: 'Filename is required',
    };
  }

  // Check for path traversal attempts
  if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
    return {
      type: 'name',
      message: 'Invalid filename: path traversal not allowed',
    };
  }

  // Check for reasonable length
  if (filename.length > 255) {
    return {
      type: 'name',
      message: 'Filename is too long (maximum 255 characters)',
    };
  }

  return undefined;
};

/**
 * Validate file (comprehensive validation)
 * @param file - File object to validate
 * @param maxSize - Maximum allowed size in bytes (default: MAX_FILE_SIZE)
 * @returns Validation error if invalid, undefined if valid
 */
export const validateFile = (
  file: File,
  maxSize: number = MAX_FILE_SIZE
): FileValidationError | undefined => {
  // Validate filename
  const filenameError = validateFilename(file.name);
  if (filenameError) {
    return filenameError;
  }

  // Validate file size
  const sizeError = validateFileSize(file, maxSize);
  if (sizeError) {
    return sizeError;
  }

  // Validate file type by extension
  const typeError = validateFileType(file.name);
  if (typeError) {
    return typeError;
  }

  // Validate file type by MIME type (if available)
  const mimeError = validateFileMimeType(file);
  if (mimeError) {
    return mimeError;
  }

  // Check if file is empty
  if (file.size === 0) {
    return {
      type: 'empty',
      message: 'File is empty',
    };
  }

  return undefined;
};

/**
 * Extract file metadata
 * @param file - File object
 * @returns File metadata object
 */
export const getFileMetadata = (file: File): FileMetadata => {
  const extension = file.name.split('.').pop()?.toLowerCase() || '';
  return {
    name: file.name,
    size: file.size,
    type: file.type,
    lastModified: file.lastModified,
    extension,
    formattedSize: formatFileSize(file.size),
  };
};

/**
 * Create FormData for file upload
 * @param file - File to upload
 * @param additionalData - Optional additional form fields
 * @returns FormData object ready for upload
 */
export const createFormData = (
  file: File,
  additionalData?: Record<string, string | number | boolean>
): FormData => {
  const formData = new FormData();
  
  // Sanitize filename before adding to FormData
  const sanitizedFile = new File([file], sanitizeFilename(file.name), {
    type: file.type,
    lastModified: file.lastModified,
  });
  
  formData.append('file', sanitizedFile);

  // Add additional form fields if provided
  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, String(value));
    });
  }

  return formData;
};

/**
 * Read text file content
 * @param file - File object (should be text file)
 * @returns Promise resolving to file content as string
 */
export const readTextFile = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      const content = event.target?.result;
      if (typeof content === 'string') {
        resolve(content);
      } else {
        reject(new Error('Failed to read file as text'));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Error reading file'));
    };
    
    reader.readAsText(file);
  });
};

/**
 * Create object URL for file preview
 * @param file - File object
 * @returns Object URL (should be revoked when done using URL.revokeObjectURL)
 */
export const createFilePreviewUrl = (file: File): string => {
  return URL.createObjectURL(file);
};

/**
 * Check if file is a PDF
 * @param file - File object
 * @returns True if file is PDF
 */
export const isPdfFile = (file: File): boolean => {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
};

/**
 * Check if file is a text file
 * @param file - File object
 * @returns True if file is text
 */
export const isTextFile = (file: File): boolean => {
  return file.type === 'text/plain' || file.name.toLowerCase().endsWith('.txt');
};

/**
 * Check if file type supports preview
 * @param file - File object
 * @returns True if file type can be previewed
 */
export const supportsPreview = (file: File): boolean => {
  return isPdfFile(file) || isTextFile(file);
};

/**
 * Create axios config for file upload with progress tracking
 * @param onProgress - Optional progress callback
 * @returns Axios request config object
 */
export const createUploadConfig = (onProgress?: UploadProgressCallback) => {
  return {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: onProgress
      ? (progressEvent: any) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        }
      : undefined,
  };
};


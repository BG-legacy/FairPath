/**
 * FileUpload Component
 * File upload component with drag & drop and validation
 */
import { useRef, useState, useCallback, DragEvent, ChangeEvent } from 'react';
import { UseFormRegisterReturn, FieldError } from 'react-hook-form';
import {
  validateFile,
  MAX_FILE_SIZE,
  ALLOWED_FILE_TYPES,
  formatFileSize,
  supportsPreview,
} from '../../utils/fileUpload';
import { FilePreview } from '../FilePreview';
import './FileUpload.css';

interface FileUploadProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  register?: UseFormRegisterReturn;
  error?: FieldError;
  accept?: string;
  maxSize?: number;
  allowedTypes?: readonly string[];
  placeholder?: string;
  showPreview?: boolean;
}

export function FileUpload({
  file,
  onFileChange,
  register,
  error,
  accept = '.pdf,.docx,.txt',
  maxSize = MAX_FILE_SIZE,
  allowedTypes = ALLOWED_FILE_TYPES,
  placeholder = 'Drag & drop your file here or click to browse',
  showPreview = true,
}: FileUploadProps): JSX.Element {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string>('');
  const [showPreviewModal, setShowPreviewModal] = useState<boolean>(false);

  const handleFileSelect = useCallback(
    (selectedFile: File): void => {
      setValidationError('');
      const validationResult = validateFile(selectedFile, maxSize);
      
      if (validationResult) {
        setValidationError(validationResult.message);
        onFileChange(null);
        return;
      }

      onFileChange(selectedFile);
    },
    [onFileChange, maxSize]
  );

  const handleDragOver = (e: DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleFilePickerClick = (): void => {
    fileInputRef.current?.click();
  };

  const handleRemoveFile = (): void => {
    onFileChange(null);
    setValidationError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const displayError = error?.message || validationError;
  const canPreview = file && showPreview && supportsPreview(file);

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-dropzone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''} ${displayError ? 'error' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          {...register}
        />
        {file ? (
          <div className="file-upload-preview">
            <div className="file-upload-info">
              <span className="file-upload-name">{file.name}</span>
              <span className="file-upload-size">{formatFileSize(file.size)}</span>
            </div>
            <div className="file-upload-actions">
              {canPreview && (
                <button
                  type="button"
                  className="file-upload-preview-button"
                  onClick={() => setShowPreviewModal(true)}
                  aria-label="Preview file"
                >
                  👁️ Preview
                </button>
              )}
              <button
                type="button"
                className="file-upload-remove"
                onClick={handleRemoveFile}
                aria-label="Remove file"
              >
                ×
              </button>
            </div>
          </div>
        ) : (
          <div className="file-upload-content">
            <div className="file-upload-icon">📄</div>
            <p className="file-upload-text">{placeholder}</p>
            <p className="file-upload-subtext">or</p>
            <button
              type="button"
              className="file-upload-button"
              onClick={handleFilePickerClick}
            >
              Choose File
            </button>
            <p className="file-upload-types">
              Supported: {allowedTypes.join(', ').toUpperCase()} (Max {formatFileSize(maxSize)})
            </p>
          </div>
        )}
      </div>
      {displayError && <span className="form-error">{displayError}</span>}
      
      {/* File Preview Modal */}
      {showPreviewModal && file && (
        <div className="file-preview-modal" onClick={() => setShowPreviewModal(false)}>
          <div className="file-preview-modal-content" onClick={(e) => e.stopPropagation()}>
            <FilePreview file={file} onClose={() => setShowPreviewModal(false)} />
          </div>
        </div>
      )}
    </div>
  );
}

export default FileUpload;


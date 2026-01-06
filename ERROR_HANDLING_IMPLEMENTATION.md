# Error Handling & User Feedback Implementation

This document summarizes the comprehensive error handling and user feedback features implemented across the frontend and backend.

## ✅ Completed Features

### Backend Enhancements

#### 1. Enhanced Exception Handlers (`backend/app/exception_handlers.py`)
- **HTTP Error Codes**: All HTTP status codes (400, 404, 413, 429, 500, 502, 503, 504) now return structured error responses with error codes
- **Error Code Mapping**: 
  - `400` → `BAD_REQUEST`
  - `404` → `NOT_FOUND`
  - `413` → `PAYLOAD_TOO_LARGE`
  - `429` → `RATE_LIMIT_EXCEEDED`
  - `500` → `INTERNAL_SERVER_ERROR`
  - `502` → `BAD_GATEWAY`
  - `503` → `SERVICE_UNAVAILABLE`
  - `504` → `GATEWAY_TIMEOUT`
- **Timeout Handling**: Specialized timeout exception handler for OpenAI endpoints
- **Validation Errors**: Enhanced validation error handler with detailed field-level errors
- **OpenAI Error Handling**: Dedicated handler for OpenAI API errors (timeouts, API errors)

#### 2. Rate Limiting Error Display (`backend/middleware/rate_limiting.py`)
- Returns `429` status with clear error message: "Rate limit exceeded: too many requests per minute/hour/day"
- Error response includes `RATE_LIMIT_EXCEEDED` error code

#### 3. File Size Error Messages (`backend/middleware/size_limiting.py`)
- Returns `413` status with clear message: "Request too large. Maximum size: XMB"
- Different limits for general requests (1MB) vs file uploads (10MB)

### Frontend Enhancements

#### 1. Loading States

**Skeleton Loaders** (`frontend/src/components/LoadingSkeleton.tsx`)
- `Skeleton`: Base skeleton component with customizable width, height, and border radius
- `CareerCardSkeleton`: Pre-built skeleton for career recommendation cards
- `FormSectionSkeleton`: Skeleton for form sections
- `ListItemSkeleton`: Skeleton for list items
- `TableRowSkeleton`: Skeleton for table rows
- `PageSkeleton`: Full page skeleton loader

**Progress Indicators** (`frontend/src/components/ProgressIndicator.tsx`)
- `LinearProgress`: Linear progress bar with indeterminate and determinate modes
- `CircularProgress`: Circular progress spinner
- `DotsLoader`: Animated dots loader
- `LoadingOverlay`: Full-page loading overlay with progress indicator

#### 2. Error Handling

**API Client Enhancements** (`frontend/src/services/apiClient.ts`)
- **Timeout Detection**: Detects `ECONNABORTED` and timeout-related errors
- **Network Error Detection**: Distinguishes between network errors and connection errors
- **Error Code Mapping**: Maps backend error codes to user-friendly messages
- **Error Sanitization**: Prevents sensitive data exposure in error messages

**Error Handler Utilities** (`frontend/src/utils/errorHandler.ts`)
- `getUserFriendlyErrorMessage()`: Converts error objects to user-friendly messages
- `isNetworkError()`: Detects network connectivity issues
- `isTimeoutError()`: Detects timeout errors
- `sanitizeErrorMessage()`: Removes sensitive information from error messages

**Validation Error Display** (`frontend/src/components/ValidationErrorDisplay.tsx`)
- `ValidationErrorDisplay`: Component for displaying field-level validation errors
- `FieldError`: Inline field error display component
- Shows validation errors in a user-friendly format with field names and messages

#### 3. Toast Notifications (`frontend/src/utils/toast.ts`)
- `showErrorToast()`: Display error notifications
- `showSuccessToast()`: Display success notifications
- `showInfoToast()`: Display info notifications
- `showWarningToast()`: Display warning notifications
- `showLoadingToast()`: Display loading notifications with dismiss function
- `handleApiError()`: Automatic error toast handling

#### 4. React Query Integration

**QueryProvider** (`frontend/src/providers/QueryProvider.tsx`)
- **Global Error Handling**: Automatically shows error toasts for all query and mutation errors
- **Error Filtering**: Only shows toasts for API errors (not all query errors)

**Enhanced Mutation Hook** (`frontend/src/hooks/useMutationWithToast.ts`)
- `useMutationWithToast()`: Wrapper around React Query mutations with automatic toast notifications
- Supports custom success/error messages
- Can enable/disable toasts per mutation

#### 5. Page Updates

**RecommendationsPage** (`frontend/src/pages/RecommendationsPage.tsx`)
- ✅ Skeleton loaders during loading state
- ✅ Progress indicators for long-running requests
- ✅ Validation error display
- ✅ Disabled states during API calls
- ✅ Success/error toast notifications (automatic via QueryProvider)

## Error Code Reference

### Backend Error Codes
- `BAD_REQUEST` (400): Invalid request data
- `UNAUTHORIZED` (401): Authentication required
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `VALIDATION_ERROR` (422): Request validation failed
- `PAYLOAD_TOO_LARGE` (413): Request body too large
- `RATE_LIMIT_EXCEEDED` (429): Too many requests
- `INTERNAL_SERVER_ERROR` (500): Server error
- `BAD_GATEWAY` (502): External service error
- `SERVICE_UNAVAILABLE` (503): Service temporarily unavailable
- `GATEWAY_TIMEOUT` (504): Request timeout
- `TIMEOUT_ERROR` (504): Request timed out
- `EXTERNAL_SERVICE_ERROR` (502): External API error (e.g., OpenAI)
- `NETWORK_ERROR`: Network connectivity issue
- `CONNECTION_ERROR`: Unable to reach server

## Usage Examples

### Using Skeleton Loaders
```tsx
import { CareerCardSkeleton } from '../components/LoadingSkeleton';

{isLoading ? (
  <div className="skeleton-grid">
    <CareerCardSkeleton />
    <CareerCardSkeleton />
    <CareerCardSkeleton />
  </div>
) : (
  <CareerCards data={data} />
)}
```

### Using Progress Indicators
```tsx
import { LinearProgress } from '../components/ProgressIndicator';

{isLoading && (
  <LinearProgress 
    message="Processing your request..." 
    indeterminate={true}
  />
)}
```

### Using Validation Error Display
```tsx
import { ValidationErrorDisplay } from '../components/ValidationErrorDisplay';

{validationErrors.length > 0 && (
  <ValidationErrorDisplay errors={validationErrors} />
)}
```

### Using Enhanced Mutation Hook
```tsx
import { useMutationWithToast } from '../hooks/useMutationWithToast';

const mutation = useMutationWithToast({
  mutationFn: myService.createItem,
  successMessage: 'Item created successfully!',
  errorMessage: 'Failed to create item. Please try again.',
  onSuccess: (data) => {
    // Custom success handler
  }
});
```

## Error Response Format

All backend errors follow this structure:
```json
{
  "success": false,
  "message": "User-friendly error message",
  "error": "ERROR_CODE",
  "status_code": 400,
  "details": [
    {
      "field": "field_name",
      "message": "Field-specific error message",
      "type": "validation_error"
    }
  ]
}
```

## Timeout Configuration

### Backend
- General requests: 30 seconds (handled by FastAPI/Uvicorn)
- OpenAI endpoints: Detected and handled via exception handlers

### Frontend (`frontend/src/config/api.ts`)
- Default timeout: 30 seconds
- OpenAI endpoints: 30 seconds
- File uploads: 60 seconds

## Best Practices

1. **Always use disabled states** during API calls to prevent duplicate submissions
2. **Show loading indicators** for operations longer than 500ms
3. **Use skeleton loaders** instead of spinners for content that's being loaded
4. **Display validation errors** at the form level and field level
5. **Show success toasts** for user actions (mutations)
6. **Let QueryProvider handle** error toasts automatically, but add custom messages when needed
7. **Use progress indicators** for file uploads and long-running operations

## Future Enhancements

- [ ] Add retry logic with exponential backoff for transient errors
- [ ] Add error reporting service integration (e.g., Sentry)
- [ ] Add offline detection and handling
- [ ] Add request cancellation for long-running requests
- [ ] Add progress tracking for file uploads
- [ ] Add optimistic updates for mutations



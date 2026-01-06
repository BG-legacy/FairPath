"""
Security utilities for input sanitization and safe error handling
"""
import re
import os
from typing import Any, Optional, List, Tuple
from pathlib import Path


# Sensitive keywords that should not appear in error messages
SENSITIVE_KEYWORDS = [
    'password', 'secret', 'key', 'token', 'api_key', 'apikey',
    'credential', 'auth', 'access', 'bearer', 'authorization',
    'openai', 'api', 'key', 'resume', 'content', 'file content',
    'extracted', 'text', 'bullet', 'rewritten'
]

# Patterns for potentially dangerous input
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script tags
    r'javascript:',  # JavaScript protocol
    r'on\w+\s*=',  # Event handlers (onclick, onload, etc.)
    r'<iframe[^>]*>',  # Iframes
    r'eval\s*\(',  # eval() calls
    r'exec\s*\(',  # exec() calls
    r'__import__',  # Python import
    r'subprocess',  # Subprocess execution
    r'os\.system',  # OS system calls
    r'pickle',  # Pickle deserialization
]


def sanitize_input(text: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent XSS and code injection
    
    Args:
        text: Input text to sanitize
        allow_html: Whether to allow HTML tags (default: False)
    
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove dangerous patterns
    sanitized = text
    for pattern in DANGEROUS_PATTERNS:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove HTML tags if not allowed
    if not allow_html:
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    # Remove null bytes and control characters (except newlines and tabs)
    sanitized = sanitized.replace('\x00', '')
    sanitized = re.sub(r'[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    # Limit length to prevent DoS
    max_length = 100000  # 100KB max
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def sanitize_error_message(error: Any, include_details: bool = False) -> str:
    """
    Sanitize error messages to prevent leaking sensitive information
    
    Args:
        error: Exception or error message
        include_details: Whether to include any error details (default: False for security)
    
    Returns:
        Sanitized error message safe to return to client
    """
    # Convert to string
    if isinstance(error, Exception):
        error_str = str(error)
    else:
        error_str = str(error)
    
    # Check for sensitive keywords
    error_lower = error_str.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in error_lower:
            # Return generic message if sensitive info detected
            return "An error occurred while processing your request"
    
    # Remove file paths that might leak system structure
    error_str = re.sub(r'/[^\s]+', '[path]', error_str)
    error_str = re.sub(r'[A-Z]:\\[^\s]+', '[path]', error_str)
    
    # Remove potential secrets (long alphanumeric strings)
    error_str = re.sub(r'\b[a-zA-Z0-9]{32,}\b', '[redacted]', error_str)
    
    # Remove traceback information in production
    if not include_details:
        # Remove Python traceback markers
        error_str = re.sub(r'File "[^"]+", line \d+', '[location]', error_str)
        error_str = re.sub(r'Traceback \(most recent call last\):', '', error_str)
    
    # Limit length
    max_length = 500
    if len(error_str) > max_length:
        error_str = error_str[:max_length] + "..."
    
    return error_str.strip() or "An error occurred"


def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate filename to prevent directory traversal and unsafe characters
    
    Args:
        filename: Filename to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not filename:
        return False, "Filename cannot be empty"
    
    # Check for directory traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Invalid filename: path traversal not allowed"
    
    # Check for null bytes
    if '\x00' in filename:
        return False, "Invalid filename: null bytes not allowed"
    
    # Check length
    if len(filename) > 255:
        return False, "Filename too long (max 255 characters)"
    
    # Check for unsafe characters
    unsafe_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in unsafe_chars:
        if char in filename:
            return False, f"Invalid filename: unsafe character '{char}' not allowed"
    
    # Normalize the filename
    normalized = os.path.normpath(filename)
    if normalized != filename:
        return False, "Invalid filename: not normalized"
    
    return True, None


def validate_file_size(file_size: int, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, Optional[str]]:
    """
    Validate file size
    
    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size in bytes (default 10MB)
    
    Returns:
        (is_valid, error_message)
    """
    if file_size <= 0:
        return False, "File size must be greater than 0"
    
    if file_size > max_size:
        max_size_mb = max_size // (1024 * 1024)
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    
    return True, None


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate file extension
    
    Args:
        filename: Filename to check
        allowed_extensions: List of allowed extensions (without dot, e.g., ['pdf', 'docx'])
    
    Returns:
        (is_valid, error_message)
    """
    if not filename:
        return False, "Filename cannot be empty"
    
    # Extract extension
    parts = filename.rsplit('.', 1)
    if len(parts) < 2:
        return False, "File must have an extension"
    
    extension = parts[1].lower()
    
    if extension not in [ext.lower() for ext in allowed_extensions]:
        return False, f"File type '{extension}' not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    return True, None


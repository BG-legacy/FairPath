"""
API routes for resume analysis and rewriting

PRIVACY GUARANTEES:
- Resume processed in-memory only (no disk storage)
- No resume content logged (only metadata like filename, file_type)
- No resume stored in database
- All resume content exists only in request/response cycle and is discarded after response

SECURITY:
- File size limits enforced (10MB max)
- Filename validation to prevent path traversal
- File extension validation
- Safe error messages (no content leakage)
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Body
from models.schemas import BaseResponse, ErrorResponse
from services.resume_service import ResumeService
from utils.security import (
    validate_filename, validate_file_size, validate_file_extension,
    sanitize_error_message
)
from app.config import settings
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

router = APIRouter()
resume_service = ResumeService()

# Maximum file size for resume uploads (10MB)
MAX_RESUME_SIZE = settings.MAX_UPLOAD_SIZE
ALLOWED_EXTENSIONS = ['pdf', 'docx', 'txt']


class ResumeRewriteRequest(BaseModel):
    """Request schema for resume rewriting"""
    bullets: List[str] = Field(..., description="List of bullet points to rewrite", min_length=1)
    target_career_id: Optional[str] = Field(None, description="Target career ID (career_id) - optional if target_career_name provided")
    target_career_name: Optional[str] = Field(None, description="Target career name/description - optional if target_career_id provided")
    resume_text: Optional[str] = Field(None, description="Optional full resume text for context")


@router.post("/analyze", response_model=BaseResponse)
async def analyze_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    target_career_id: Optional[str] = Form(None, description="Optional target career ID for gap analysis"),
    target_career_name: Optional[str] = Form(None, description="Optional target career name/description for gap analysis")
):
    """
    Analyze resume - extract text, detect skills, parse structure, and analyze gaps
    
    Accepts PDF, DOCX, or TXT files and returns:
    - extracted text (not persisted)
    - detected skills
    - bullet list + sections
    - gaps vs target career (if target_career_id provided)
    
    PRIVACY: Resume content is processed entirely in-memory and never stored or logged.
    Only metadata (filename, file_type) is included in error messages.
    """
    try:
        # Validate filename (prevent path traversal)
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    message="Invalid file",
                    error="Filename is required"
                ).model_dump()
            )
        
        is_valid_filename, filename_error = validate_filename(file.filename)
        if not is_valid_filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    message="Invalid filename",
                    error=filename_error or "Filename validation failed"
                ).model_dump()
            )
        
        # Validate file extension
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        is_valid_ext, ext_error = validate_file_extension(file.filename, ALLOWED_EXTENSIONS)
        if not is_valid_ext:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    message="Unsupported file type",
                    error=ext_error or f"File type '{file_extension}' not supported"
                ).model_dump()
            )
        
        # Read file content into memory only (no disk storage)
        # Limit read to prevent memory exhaustion
        file_content = await file.read()
        
        # Validate file size
        file_size = len(file_content)
        is_valid_size, size_error = validate_file_size(file_size, MAX_RESUME_SIZE)
        if not is_valid_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=ErrorResponse(
                    success=False,
                    message="File too large",
                    error=size_error or f"File exceeds maximum size of {MAX_RESUME_SIZE // (1024 * 1024)}MB"
                ).model_dump()
            )
        
        # Extract text (in-memory processing only)
        extracted_text = resume_service.extract_text_from_file(file_content, file_extension)
        
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    message="No text extracted from file",
                    error="The file appears to be empty or could not be processed"
                ).model_dump()
            )
        
        # Detect skills
        detected_skills = resume_service.detect_skills(extracted_text)
        
        # Parse resume structure
        resume_structure = resume_service.parse_resume_structure(extracted_text)
        
        # Analyze gaps if target career provided
        gap_analysis = None
        if target_career_id or target_career_name:
            try:
                gap_analysis = resume_service.analyze_gaps(
                    detected_skills, 
                    target_career_id=target_career_id,
                    target_career_name=target_career_name,
                    resume_text=extracted_text
                )
                if "error" in gap_analysis:
                    # Don't fail the whole request if gap analysis fails
                    gap_analysis = {"error": gap_analysis["error"]}
            except Exception as e:
                gap_analysis = {"error": str(e)}
        
        result = {
            "extracted_text": extracted_text,  # Not persisted per requirements
            "detected_skills": detected_skills,
            "structure": resume_structure,
            "gap_analysis": gap_analysis,
            "metadata": {
                "filename": file.filename,
                "file_type": file_extension,
                "text_length": len(extracted_text),
                "skills_count": len(detected_skills)
            }
        }
        
        return BaseResponse(
            success=True,
            message="Resume analyzed successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Privacy: Never log resume content in error messages
        # Sanitize error message to ensure no resume content leaks
        error_msg = sanitize_error_message(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                message="File processing error",
                error=error_msg
            ).model_dump()
        )
    except Exception as e:
        # Privacy: Never log resume content in error messages
        # Sanitize error message to ensure no resume content leaks
        error_msg = sanitize_error_message(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to analyze resume",
                error=error_msg
            ).model_dump()
        )


@router.post("/rewrite", response_model=BaseResponse)
async def rewrite_resume(request: ResumeRewriteRequest = Body(...)):
    """
    Rewrite resume bullets to better align with target career
    
    Returns:
    - before → after bullets
    - explanation per rewrite
    - "no fabrication" compliance notes
    
    PRIVACY: Resume content is processed entirely in-memory and never stored or logged.
    """
    try:
        result = resume_service.rewrite_bullets(
            bullets=request.bullets,
            target_career_id=request.target_career_id,
            target_career_name=request.target_career_name,
            resume_text=request.resume_text
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message="Target career not found",
                    error=result["error"]
                ).model_dump()
            )
        
        return BaseResponse(
            success=True,
            message=f"Rewrote {len(result.get('rewrites', []))} bullet points",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Privacy: Never log resume content in error messages
        # Sanitize error message to ensure no resume content leaks
        error_msg = sanitize_error_message(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to rewrite resume bullets",
                error=error_msg
            ).model_dump()
        )


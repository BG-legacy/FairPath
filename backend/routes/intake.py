"""
API routes for user intake/profile normalization
"""
from fastapi import APIRouter, HTTPException, status, Body
from models.schemas import BaseResponse, ErrorResponse, IntakeResponse
from services.intake_service import IntakeService
from utils.security import sanitize_error_message
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator

router = APIRouter()
intake_service = IntakeService()


class IntakeRequest(BaseModel):
    """Request schema for user intake/profile normalization"""
    skills: Optional[List[str]] = Field(
        None,
        description="List of skill names",
        min_length=0
    )
    interests: Optional[Union[List[str], str]] = Field(
        None,
        description="List of RIASEC interest categories (Realistic, Investigative, Artistic, Social, Enterprising, Conventional) or text description"
    )
    constraints: Optional[Dict[str, Any]] = Field(
        None,
        description="Dict with constraints: cost (min_wage), time (max_hours, flexible_hours), location (remote_preferred, location_preference)"
    )
    values: Optional[Dict[str, float]] = Field(
        None,
        description="Dict mapping career values to scores (0-7): impact, stability, flexibility"
    )
    
    @field_validator('skills')
    @classmethod
    def validate_skills(cls, v):
        if v is not None:
            # Remove empty strings and strip whitespace
            v = [s.strip() for s in v if s and s.strip()]
        return v
    
    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v):
        if v is not None:
            if isinstance(v, str):
                # Text input - will be parsed later
                if not v.strip():
                    return None
                return v.strip()
            elif isinstance(v, list):
                # List input - validate RIASEC categories
                valid_categories = {
                    "Realistic", "Investigative", "Artistic",
                    "Social", "Enterprising", "Conventional"
                }
                normalized = []
                for item in v:
                    if isinstance(item, str) and item.strip():
                        item = item.strip()
                        # Case-insensitive matching
                        for cat in valid_categories:
                            if cat.lower() == item.lower():
                                normalized.append(cat)
                                break
                return normalized if normalized else None
        return v
    
    @field_validator('values')
    @classmethod
    def validate_values(cls, v):
        if v is not None:
            valid_keys = {"impact", "stability", "flexibility"}
            normalized = {}
            for key, value in v.items():
                key_lower = key.lower()
                # Find matching key (case-insensitive)
                for valid_key in valid_keys:
                    if valid_key.lower() == key_lower:
                        # Ensure value is in valid range (0-7)
                        if isinstance(value, (int, float)):
                            normalized[valid_key] = max(0.0, min(7.0, float(value)))
                        break
            return normalized if normalized else None
        return v
    
    @field_validator('constraints')
    @classmethod
    def validate_constraints(cls, v):
        if v is not None:
            normalized = {}
            # Cost constraint (min_wage)
            if "cost" in v:
                cost = v["cost"]
                if isinstance(cost, (int, float)) and cost >= 0:
                    normalized["min_wage"] = float(cost)
                elif isinstance(cost, dict) and "min_wage" in cost:
                    min_wage = cost["min_wage"]
                    if isinstance(min_wage, (int, float)) and min_wage >= 0:
                        normalized["min_wage"] = float(min_wage)
            
            # Time constraints
            if "time" in v:
                time_constraints = v["time"]
                if isinstance(time_constraints, dict):
                    if "max_hours" in time_constraints:
                        max_hours = time_constraints["max_hours"]
                        if isinstance(max_hours, (int, float)) and 0 < max_hours <= 168:
                            normalized["max_hours"] = float(max_hours)
                    if "flexible_hours" in time_constraints:
                        flexible = time_constraints["flexible_hours"]
                        if isinstance(flexible, bool):
                            normalized["flexible_hours"] = flexible
            
            # Location constraints
            if "location" in v:
                location_constraints = v["location"]
                if isinstance(location_constraints, dict):
                    if "remote_preferred" in location_constraints:
                        remote = location_constraints["remote_preferred"]
                        if isinstance(remote, bool):
                            normalized["remote_preferred"] = remote
                    if "location_preference" in location_constraints:
                        loc = location_constraints["location_preference"]
                        if isinstance(loc, str) and loc.strip():
                            normalized["location_preference"] = loc.strip()
            
            # Support legacy format for backward compatibility
            if "min_wage" in v:
                min_wage = v["min_wage"]
                if isinstance(min_wage, (int, float)) and min_wage >= 0:
                    normalized["min_wage"] = float(min_wage)
            if "remote_preferred" in v:
                remote = v["remote_preferred"]
                if isinstance(remote, bool):
                    normalized["remote_preferred"] = remote
            if "max_education_level" in v:
                edu_level = v["max_education_level"]
                if isinstance(edu_level, (int, float)) and 0 <= edu_level <= 5:
                    normalized["max_education_level"] = int(edu_level)
            
            return normalized if normalized else None
        return v


@router.post("/intake", response_model=BaseResponse)
async def process_intake(request: IntakeRequest = Body(...)):
    """
    Process user intake and return normalized profile + derived features summary
    
    Validates and normalizes:
    - skills: List of skill names
    - interests: RIASEC categories (list) or text description
    - constraints: cost (min_wage), time (max_hours, flexible_hours), location (remote_preferred, location_preference)
    - values: impact, stability, flexibility (0-7 scale)
    
    Returns normalized profile with feature vectors and summary statistics
    """
    try:
        result = intake_service.normalize_profile(
            skills=request.skills,
            interests=request.interests,
            constraints=request.constraints,
            values=request.values
        )
        
        return BaseResponse(
            success=True,
            message="Profile normalized successfully",
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                message="Validation error",
                error=sanitize_error_message(e)
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to process intake",
                error=sanitize_error_message(e)
            ).model_dump()
        )


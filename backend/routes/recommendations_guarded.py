"""
API routes for career recommendations with ML guardrails
I'm wrapping the recommendation service with guardrails for fairness and transparency
"""
from fastapi import APIRouter, HTTPException, status, Query, Body
from models.schemas import BaseResponse, ErrorResponse
from services.guardrails_service import GuardrailsService
from utils.security import sanitize_error_message
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

router = APIRouter()
guardrails_service = GuardrailsService()


class RecommendationRequest(BaseModel):
    """Request schema for career recommendations"""
    skills: Optional[List[str]] = Field(None, description="List of skill names")
    skill_importance: Optional[Dict[str, float]] = Field(
        None, 
        description="Dict mapping skill names to importance scores (0-5)"
    )
    interests: Optional[Dict[str, float]] = Field(
        None,
        description="Dict mapping RIASEC categories to scores (0-7). Categories: Realistic, Investigative, Artistic, Social, Enterprising, Conventional"
    )
    work_values: Optional[Dict[str, float]] = Field(
        None,
        description="Dict mapping work values to scores (0-7). Values: Achievement, Working Conditions, Recognition, Relationships, Support, Independence"
    )
    constraints: Optional[Dict[str, Any]] = Field(
        None,
        description="Dict with constraints like min_wage, remote_preferred, max_education_level. Note: Demographic data is not accepted."
    )
    top_n: int = Field(5, ge=1, le=20, description="Number of recommendations to return (minimum 3 will be returned)")
    use_ml: bool = Field(True, description="Whether to use ML model or baseline ranking")


@router.post("/recommend", response_model=BaseResponse)
async def get_recommendations(request: RecommendationRequest = Body(...)):
    """
    Get career recommendations with ML guardrails applied
    
    Guardrails:
    - No demographic features accepted
    - Always returns multiple recommendations (minimum 3)
    - Includes uncertainty ranges and confidence indicators
    - Fallback behavior for thin/empty inputs
    """
    try:
        result = guardrails_service.recommend_with_guardrails(
            skills=request.skills,
            skill_importance=request.skill_importance,
            interests=request.interests,
            work_values=request.work_values,
            constraints=request.constraints,
            top_n=request.top_n,
            use_ml=request.use_ml
        )
        
        # Check for demographic data error
        if "error" in result and "demographic" in result["error"].lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    message=result.get("message", "Demographic features detected"),
                    error=result.get("issues", [])
                ).model_dump()
            )
        
        return BaseResponse(
            success=True,
            message=f"Generated {result.get('total_count', 0)} recommendations with guardrails applied",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to generate recommendations",
                error=sanitize_error_message(e)
            ).model_dump()
        )


@router.get("/recommend/simple", response_model=BaseResponse)
async def get_simple_recommendations(
    skills: Optional[str] = Query(None, description="Comma-separated list of skills"),
    top_n: int = Query(5, ge=1, le=20, description="Number of recommendations")
):
    """
    Simple recommendation endpoint with guardrails
    Just provide skills as comma-separated string
    """
    try:
        skills_list = [s.strip() for s in skills.split(",")] if skills else None
        
        result = guardrails_service.recommend_with_guardrails(
            skills=skills_list,
            top_n=top_n,
            use_ml=True
        )
        
        if "error" in result and "demographic" in result["error"].lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    message=result.get("message", "Demographic features detected")
                ).model_dump()
            )
        
        return BaseResponse(
            success=True,
            message=f"Generated {result.get('total_count', 0)} recommendations",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to generate recommendations",
                error=sanitize_error_message(e)
            ).model_dump()
        )


@router.get("/guardrails/info", response_model=BaseResponse)
async def get_guardrails_info():
    """
    Get information about ML guardrails in place
    """
    return BaseResponse(
        success=True,
        message="ML Guardrails information",
        data={
            "guardrails": [
                "No demographic features accepted, stored, or inferred",
                "Always returns multiple recommendations (minimum 3)",
                "Uncertainty ranges and confidence indicators included",
                "Fallback behavior for thin/empty inputs"
            ],
            "demographic_keywords_blocked": GuardrailsService.DEMOGRAPHIC_KEYWORDS,
            "minimum_recommendations": GuardrailsService.MIN_RECOMMENDATIONS,
            "default_recommendations": GuardrailsService.DEFAULT_RECOMMENDATIONS
        }
    )






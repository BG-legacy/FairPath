"""
API routes for career recommendations
"""
from fastapi import APIRouter, HTTPException, status, Query, Body
from models.schemas import BaseResponse, ErrorResponse
from services.recommendation_service import CareerRecommendationService
from utils.security import sanitize_error_message
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

router = APIRouter()
recommendation_service = CareerRecommendationService()

# Try to load model on startup
recommendation_service.load_model_artifacts()


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
        description="Dict with constraints like min_wage, remote_preferred, max_education_level"
    )
    top_n: int = Field(5, ge=1, le=20, description="Number of recommendations to return")
    use_ml: bool = Field(True, description="Whether to use ML model or baseline ranking")


@router.post("/recommendations", response_model=BaseResponse)
async def get_recommendations(request: RecommendationRequest = Body(...)):
    """
    Get enhanced career recommendations with:
    - 3-5 careers
    - Confidence bands (with score ranges)
    - Explainability (top features)
    - Alternatives
    - "Why" narrative
    
    Uses ML model if available, otherwise falls back to baseline similarity ranking
    """
    try:
        result = recommendation_service.get_enhanced_recommendations(
            skills=request.skills,
            skill_importance=request.skill_importance,
            interests=request.interests,
            work_values=request.work_values,
            constraints=request.constraints,
            use_ml=request.use_ml,
            use_openai=True
        )
        
        return BaseResponse(
            success=True,
            message=f"Generated {len(result['careers'])} recommendations with {len(result.get('alternatives', []))} alternatives",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to generate recommendations",
                error=sanitize_error_message(e)
            ).model_dump()
        )


@router.post("/recommend", response_model=BaseResponse)
async def get_recommendations_legacy(request: RecommendationRequest = Body(...)):
    """
    Legacy endpoint - Get career recommendations based on user skills, interests, values, and constraints
    
    Uses ML model if available, otherwise falls back to baseline similarity ranking
    """
    try:
        result = recommendation_service.recommend(
            skills=request.skills,
            skill_importance=request.skill_importance,
            interests=request.interests,
            work_values=request.work_values,
            constraints=request.constraints,
            top_n=5,
            use_ml=request.use_ml
        )
        
        return BaseResponse(
            success=True,
            message=f"Generated {len(result['recommendations'])} recommendations",
            data=result
        )
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
    Simple recommendation endpoint - just provide skills as comma-separated string
    Useful for quick testing
    """
    try:
        skills_list = [s.strip() for s in skills.split(",")] if skills else None
        
        result = recommendation_service.recommend(
            skills=skills_list,
            top_n=top_n,
            use_ml=True
        )
        
        return BaseResponse(
            success=True,
            message=f"Generated {len(result['recommendations'])} recommendations",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to generate recommendations",
                error=sanitize_error_message(e)
            ).model_dump()
        )


@router.get("/model/status", response_model=BaseResponse)
async def get_model_status():
    """
    Get status of the ML model - whether it's loaded and what version
    """
    try:
        has_model = recommendation_service.ml_model is not None
        has_scaler = recommendation_service.scaler is not None
        
        return BaseResponse(
            success=True,
            message="Model status retrieved",
            data={
                "model_loaded": has_model,
                "scaler_loaded": has_scaler,
                "model_version": recommendation_service.model_version,
                "fallback_to_baseline": not has_model
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to get model status",
                error=str(e)
            ).model_dump()
        )






"""
API routes for career switch intelligence
"""
from fastapi import APIRouter, HTTPException, status, Query, Body
from models.schemas import BaseResponse, ErrorResponse
from services.career_switch_service import CareerSwitchService
from typing import Optional
from pydantic import BaseModel, Field

router = APIRouter()
switch_service = CareerSwitchService()


class CareerSwitchRequest(BaseModel):
    """Request schema for career switch analysis"""
    source_career_id: str = Field(..., description="Career ID of current occupation")
    target_career_id: str = Field(..., description="Career ID of target occupation")


class CareerSwitchByNameRequest(BaseModel):
    """Request schema for career switch analysis using career names directly"""
    source_career_name: str = Field(..., description="Name of current career (as typed by user)")
    target_career_name: str = Field(..., description="Name of target career (as typed by user)")


@router.post("/analyze", response_model=BaseResponse)
async def analyze_career_switch(request: CareerSwitchRequest = Body(...)):
    """
    Analyze a career switch from source to target occupation
    
    Returns skill overlap, transfer map, difficulty classification, 
    transition time estimate, and success/risk factors
    """
    try:
        result = switch_service.analyze_career_switch(
            source_career_id=request.source_career_id,
            target_career_id=request.target_career_id
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message=result["error"]
                ).model_dump()
            )
        
        return BaseResponse(
            success=True,
            message="Career switch analysis completed",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to analyze career switch",
                error=str(e)
            ).model_dump()
        )


@router.post("/switch", response_model=BaseResponse)
async def career_switch(request: CareerSwitchRequest = Body(...)):
    """
    Analyze a career switch from source to target occupation.
    
    Returns:
    - overlap %: Percentage of skills that overlap between source and target
    - difficulty: Transition difficulty classification (Low, Medium, High)
    - transition time range: Estimated time range for the transition
    - skill translation map: Structured map of skills (transfers directly, needs learning, optional)
    - success factors + risk factors: Non-deterministic assessment of transition factors
    """
    try:
        result = switch_service.analyze_career_switch(
            source_career_id=request.source_career_id,
            target_career_id=request.target_career_id
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message=result["error"]
                ).model_dump()
            )
        
        # Format response with requested fields
        formatted_result = {
            "overlap_percentage": result["skill_overlap"]["percentage"],
            "difficulty": result["difficulty"],
            "transition_time_range": {
                "min_months": result["transition_time"]["min_months"],
                "max_months": result["transition_time"]["max_months"],
                "range": result["transition_time"]["range"],
                "note": result["transition_time"].get("note", "")
            },
            "skill_translation_map": {
                "transfers_directly": result["transfer_map"]["transfers_directly"],
                "needs_learning": result["transfer_map"]["needs_learning"],
                "optional_skills": result["transfer_map"]["optional_skills"]
            },
            "success_factors": result["success_risk_assessment"]["success_factors"],
            "risk_factors": result["success_risk_assessment"]["risk_factors"],
            "overall_assessment": result["success_risk_assessment"].get("overall_assessment", ""),
            "source_career": result["source_career"],
            "target_career": result["target_career"]
        }
        
        return BaseResponse(
            success=True,
            message="Career switch analysis completed",
            data=formatted_result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to analyze career switch",
                error=str(e)
            ).model_dump()
        )


@router.post("/switch-by-name", response_model=BaseResponse)
async def career_switch_by_name(request: CareerSwitchByNameRequest = Body(...)):
    """
    Analyze a career switch using career names directly (no database lookup required).
    Uses OpenAI to generate analysis based on the career names provided.
    """
    try:
        result = switch_service.analyze_career_switch_by_name(
            source_career_name=request.source_career_name,
            target_career_name=request.target_career_name
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    message=result["error"]
                ).model_dump()
            )
        
        # Format response with requested fields
        formatted_result = {
            "overlap_percentage": result.get("overlap_percentage", 0),
            "difficulty": result.get("difficulty", "Medium"),
            "transition_time_range": result.get("transition_time_range", {
                "min_months": 6,
                "max_months": 12,
                "range": "6-12 months",
                "note": "Estimated transition time"
            }),
            "skill_translation_map": result.get("skill_translation_map", {
                "transfers_directly": [],
                "needs_learning": [],
                "optional_skills": []
            }),
            "success_factors": result.get("success_factors", []),
            "risk_factors": result.get("risk_factors", []),
            "overall_assessment": result.get("overall_assessment", ""),
            "source_career": {
                "career_id": result.get("source_career", {}).get("career_id", ""),
                "name": request.source_career_name
            },
            "target_career": {
                "career_id": result.get("target_career", {}).get("career_id", ""),
                "name": request.target_career_name
            }
        }
        
        return BaseResponse(
            success=True,
            message="Career switch analysis completed",
            data=formatted_result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to analyze career switch",
                error=str(e)
            ).model_dump()
        )


@router.get("/overlap", response_model=BaseResponse)
async def get_skill_overlap(
    source: str = Query(..., description="Source career ID"),
    target: str = Query(..., description="Target career ID")
):
    """
    Get skill overlap percentage and transfer map between two careers
    Quick endpoint for just the overlap data
    """
    try:
        result = switch_service.compute_skill_overlap(source, target)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message=result["error"]
                ).model_dump()
            )
        
        return BaseResponse(
            success=True,
            message="Skill overlap computed",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to compute skill overlap",
                error=str(e)
            ).model_dump()
        )






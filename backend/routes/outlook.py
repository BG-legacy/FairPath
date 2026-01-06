"""
API routes for 5-10 year outlook analysis
"""
from fastapi import APIRouter, HTTPException, status
from models.schemas import BaseResponse, ErrorResponse
from services.outlook_service import OutlookService

router = APIRouter()
outlook_service = OutlookService()


@router.get("/{career_id}", response_model=BaseResponse)
async def get_outlook(career_id: str):
    """
    Get 5-10 year outlook for a specific career
    
    Returns:
    - growth_outlook: Classification (Strong/Moderate/Declining/Uncertain) with range
    - automation_risk: Risk level (Low/Medium/High/Uncertain)
    - stability: Stability signal (Expanding/Shifting/Declining/Uncertain)
    - confidence: Confidence indicator with reasoning
    - assumptions: Assumptions and disclaimers
    """
    try:
        result = outlook_service.analyze_outlook(career_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message=result["error"]
                ).model_dump()
            )
        
        # Structure response according to requirements
        outlook_data = {
            "growth_outlook": {
                "outlook": result.get("growth_outlook", {}).get("outlook"),
                "range": {
                    "growth_rate_percent": result.get("raw_metrics", {}).get("growth_rate"),
                    "employment_2024": result.get("raw_metrics", {}).get("employment_2024"),
                    "employment_2034": result.get("raw_metrics", {}).get("employment_2034"),
                    "annual_openings": result.get("raw_metrics", {}).get("annual_openings")
                },
                "confidence": result.get("growth_outlook", {}).get("confidence"),
                "reasoning": result.get("growth_outlook", {}).get("reasoning")
            },
            "automation_risk": {
                "risk": result.get("automation_risk", {}).get("risk"),
                "confidence": result.get("automation_risk", {}).get("confidence"),
                "reasoning": result.get("automation_risk", {}).get("reasoning")
            },
            "stability": {
                "signal": result.get("stability_signal", {}).get("signal"),
                "confidence": result.get("stability_signal", {}).get("confidence"),
                "reasoning": result.get("stability_signal", {}).get("reasoning")
            },
            "confidence": result.get("confidence", {}),
            "assumptions": result.get("assumptions_and_limitations", {})
        }
        
        return BaseResponse(
            success=True,
            message="Outlook analysis completed",
            data=outlook_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to analyze outlook",
                error=str(e)
            ).model_dump()
        )


@router.get("/assumptions", response_model=BaseResponse)
async def get_assumptions():
    """
    Get documented assumptions and limitations for the outlook model
    Useful for understanding what the model can and can't predict
    """
    try:
        assumptions = outlook_service.get_assumptions_and_limitations()
        
        return BaseResponse(
            success=True,
            message="Assumptions and limitations retrieved",
            data=assumptions
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to retrieve assumptions",
                error=str(e)
            ).model_dump()
        )






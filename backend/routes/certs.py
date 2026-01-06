"""
API routes for career certifications
"""
from fastapi import APIRouter, HTTPException, status
from models.schemas import BaseResponse, ErrorResponse
from services.data_processing import DataProcessingService
from services.openai_enhancement import OpenAIEnhancementService

router = APIRouter()
data_service = DataProcessingService()
openai_service = OpenAIEnhancementService()


@router.get("/{career_id}", response_model=BaseResponse)
async def get_certifications(career_id: str):
    """
    Get certifications for a specific career
    
    Returns:
    - entry_level: List of entry-level certifications
    - career_advancing: List of career-advancing certifications
    - optional_overhyped: List of optional/overhyped certifications with rationale
    """
    try:
        # Load processed data
        processed_data = data_service.load_processed_data()
        
        # Find occupation by career_id
        occ_data = None
        for occ in processed_data["occupations"]:
            if occ["career_id"] == career_id:
                occ_data = occ
                break
        
        if not occ_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message=f"Occupation with career_id {career_id} not found"
                ).model_dump()
            )
        
        # Get certifications using OpenAI service
        certifications = openai_service.get_career_certifications(
            career_name=occ_data.get("name"),
            career_data=occ_data
        )
        
        # Structure response according to requirements
        certs_data = {
            "career": {
                "career_id": career_id,
                "name": occ_data.get("name"),
                "soc_code": occ_data.get("soc_code")
            },
            "entry_level": certifications.get("entry_level", []),
            "career_advancing": certifications.get("career_advancing", []),
            "optional_overhyped": certifications.get("optional_overhyped", []),
            "available": certifications.get("available", False)
        }
        
        # Ensure rationale field exists for optional_overhyped certifications
        # (use description as fallback if rationale not provided)
        for cert in certs_data["optional_overhyped"]:
            if "rationale" not in cert or not cert.get("rationale"):
                if "description" in cert:
                    cert["rationale"] = cert["description"]
        
        return BaseResponse(
            success=True,
            message="Certifications retrieved successfully",
            data=certs_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to retrieve certifications",
                error=str(e)
            ).model_dump()
        )


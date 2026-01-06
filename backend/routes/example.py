"""
Example route - showing how to do validation and consistent responses
You can delete this once you have real routes, I'm just using it as a template
"""
from fastapi import APIRouter, HTTPException, status
from models.schemas import BaseResponse, ErrorResponse, ExampleRequest, ExampleResponse
from services.example_service import ExampleService
from datetime import datetime

router = APIRouter()
service = ExampleService()

@router.post("/process", response_model=BaseResponse)
async def process_example(request: ExampleRequest):
    """
    Example endpoint with full validation
    Using consistent response format so frontend knows what to expect
    """
    try:
        # service handles the business logic, keeping routes thin
        result = await service.process_data(request)
        
        # wrapping in consistent response format
        return BaseResponse(
            success=True,
            message="Processed successfully",
            data=result
        )
    except ValueError as e:
        # validation errors - these should be caught by Pydantic but just in case
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                message="Validation failed",
                error=str(e)
            ).dict()
        )
    except Exception as e:
        # unexpected errors - probably should log these in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Internal server error",
                error=str(e)
            ).dict()
        )

@router.get("/test", response_model=BaseResponse)
async def test_endpoint():
    """Simple test endpoint to make sure things are working"""
    return BaseResponse(
        success=True,
        message="Test endpoint working",
        data={"timestamp": datetime.now().isoformat()}
    )


"""
Data routes for accessing O*NET and BLS data
"""
from fastapi import APIRouter, HTTPException, status, Query
from models.schemas import BaseResponse, ErrorResponse
from models.data_models import OccupationCatalog, DataDictionary
from services.data_ingestion import DataIngestionService
from services.data_processing import DataProcessingService
from services.openai_enhancement import OpenAIEnhancementService
from typing import List, Optional
import json
from pathlib import Path

router = APIRouter()
service = DataIngestionService()
processing_service = DataProcessingService()
openai_service = OpenAIEnhancementService()

# Cache for loaded catalog
_catalog_cache: Optional[List[OccupationCatalog]] = None
_data_dict_cache: Optional[List[DataDictionary]] = None
_processed_data_cache: Optional[dict] = None


def load_catalog() -> List[OccupationCatalog]:
    """Load catalog from artifacts or build it"""
    global _catalog_cache
    
    if _catalog_cache is not None:
        return _catalog_cache
    
    # Try to load from artifacts
    catalog_file = Path(__file__).parent.parent / "artifacts" / "occupation_catalog.json"
    
    if catalog_file.exists():
        try:
            with open(catalog_file, 'r') as f:
                data = json.load(f)
                _catalog_cache = [OccupationCatalog(**item) for item in data]
                return _catalog_cache
        except Exception as e:
            print(f"Error loading catalog from file: {e}")
    
    # Build catalog if file doesn't exist
    _catalog_cache = service.build_occupation_catalog(min_occupations=50, max_occupations=150)
    return _catalog_cache


def load_data_dictionary() -> List[DataDictionary]:
    """Load data dictionary from artifacts or create it"""
    global _data_dict_cache
    
    if _data_dict_cache is not None:
        return _data_dict_cache
    
    # Try to load from artifacts
    dict_file = Path(__file__).parent.parent / "artifacts" / "data_dictionary.json"
    
    if dict_file.exists():
        try:
            with open(dict_file, 'r') as f:
                data = json.load(f)
                _data_dict_cache = [DataDictionary(**item) for item in data]
                return _data_dict_cache
        except Exception as e:
            print(f"Error loading data dictionary from file: {e}")
    
    # Create dictionary if file doesn't exist
    _data_dict_cache = service.create_data_dictionary()
    return _data_dict_cache


@router.get("/catalog", response_model=BaseResponse)
async def get_occupation_catalog(
    limit: Optional[int] = Query(None, ge=1, le=500, description="Limit number of results"),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination"),
    soc_code: Optional[str] = Query(None, description="Filter by SOC code"),
    search: Optional[str] = Query(None, description="Search in occupation names")
):
    """
    Get the occupation catalog
    
    Returns filtered list of occupations with their skills, tasks, and BLS projections
    """
    try:
        catalogs = load_catalog()
        
        # Apply filters
        if soc_code:
            normalized_soc = service.normalize_soc_code(soc_code)
            catalogs = [c for c in catalogs if c.occupation.soc_code == normalized_soc]
        
        if search:
            search_lower = search.lower()
            catalogs = [
                c for c in catalogs
                if search_lower in c.occupation.name.lower() or
                   search_lower in c.occupation.description.lower()
            ]
        
        # Apply pagination
        total = len(catalogs)
        if offset:
            catalogs = catalogs[offset:]
        if limit:
            catalogs = catalogs[:limit]
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(catalogs)} occupations",
            data={
                "total": total,
                "count": len(catalogs),
                "offset": offset or 0,
                "occupations": [c.model_dump() for c in catalogs]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to load occupation catalog",
                error=str(e)
            ).model_dump()
        )


@router.get("/catalog/validate", response_model=BaseResponse)
async def validate_career_name(
    career_input: str = Query(..., description="Career name or description to validate")
):
    """
    Validate and normalize a career name/description using OpenAI.
    Returns the best matching career from the database.
    This endpoint helps users enter career names naturally without needing to select from a list.
    """
    try:
        if not career_input.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    message="Career input is required"
                ).model_dump()
            )
        
        if not openai_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse(
                    success=False,
                    message="OpenAI service is not available"
                ).model_dump()
            )
        
        # Load all careers from catalog
        catalogs = load_catalog()
        
        # Convert to format expected by OpenAI service
        all_careers = []
        for catalog in catalogs:
            career_dict = {
                "career_id": catalog.occupation.career_id,
                "name": catalog.occupation.name,
                "soc_code": catalog.occupation.soc_code,
                "description": catalog.occupation.description
            }
            all_careers.append(career_dict)
        
        # Use OpenAI to validate and find best match
        result = openai_service.validate_career_name(
            career_input=career_input,
            all_careers=all_careers
        )
        
        if not result:
            return BaseResponse(
                success=False,
                message="No matching career found",
                data=None
            )
        
        # Find the full catalog entry for consistency
        catalog = next(
            (c for c in catalogs if c.occupation.career_id == result["career_id"]),
            None
        )
        
        if not catalog:
            return BaseResponse(
                success=False,
                message="Career found but catalog entry not available",
                data=None
            )
        
        return BaseResponse(
            success=True,
            message="Career validated successfully",
            data={
                "career_id": result["career_id"],
                "name": result["name"],
                "soc_code": result["soc_code"],
                "match_explanation": result.get("match_explanation", ""),
                "match_score": result.get("match_score", 0.0),
                "occupation": catalog.occupation.model_dump()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to validate career name",
                error=str(e)
            ).model_dump()
        )


@router.get("/catalog/{career_id}", response_model=BaseResponse)
async def get_occupation_by_id(career_id: str):
    """
    Get a specific occupation by career_id
    """
    try:
        catalogs = load_catalog()
        
        catalog = next(
            (c for c in catalogs if c.occupation.career_id == career_id),
            None
        )
        
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message=f"Occupation with career_id {career_id} not found"
                ).model_dump()
            )
        
        return BaseResponse(
            success=True,
            message="Occupation retrieved successfully",
            data=catalog.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to load occupation",
                error=str(e)
            ).model_dump()
        )


@router.get("/dictionary", response_model=BaseResponse)
async def get_data_dictionary():
    """
    Get the data dictionary documenting all data files
    """
    try:
        dictionaries = load_data_dictionary()
        
        return BaseResponse(
            success=True,
            message="Data dictionary retrieved successfully",
            data=[dd.model_dump() for dd in dictionaries]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to load data dictionary",
                error=str(e)
            ).model_dump()
        )


@router.get("/stats", response_model=BaseResponse)
async def get_data_stats():
    """
    Get statistics about the loaded data
    """
    try:
        catalogs = load_catalog()
        
        total_skills = sum(len(c.skills) for c in catalogs)
        total_tasks = sum(len(c.tasks) for c in catalogs)
        occupations_with_bls = sum(1 for c in catalogs if c.bls_projection is not None)
        
        # Get unique skills
        all_skill_names = set()
        for catalog in catalogs:
            for skill in catalog.skills:
                all_skill_names.add(skill.skill_name)
        
        stats = {
            "total_occupations": len(catalogs),
            "total_skills": total_skills,
            "unique_skills": len(all_skill_names),
            "total_tasks": total_tasks,
            "occupations_with_bls_data": occupations_with_bls,
            "occupations_with_skills": sum(1 for c in catalogs if len(c.skills) > 0),
            "occupations_with_tasks": sum(1 for c in catalogs if len(c.tasks) > 0)
        }
        
        return BaseResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to load statistics",
                error=str(e)
            ).model_dump()
        )


def load_processed_data() -> Optional[dict]:
    """Load processed data from artifacts"""
    global _processed_data_cache
    
    if _processed_data_cache is not None:
        return _processed_data_cache
    
    processed_data = processing_service.load_processed_data()
    if processed_data:
        _processed_data_cache = processed_data
    return processed_data


@router.get("/processed", response_model=BaseResponse)
async def get_processed_data(
    career_id: Optional[str] = Query(None, description="Filter by career_id")
):
    """
    Get processed datasets - skill vectors, task features, outlook features, education data
    Includes version stamp for reproducibility
    """
    try:
        processed = load_processed_data()
        
        if not processed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message="Processed data not found. Run process_data.py script first."
                ).model_dump()
            )
        
        # Filter by career_id if provided
        occupations = processed.get("occupations", [])
        if career_id:
            occupations = [occ for occ in occupations if occ.get("career_id") == career_id]
            if not occupations:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponse(
                        success=False,
                        message=f"No processed data found for career_id {career_id}"
                    ).model_dump()
                )
        
        return BaseResponse(
            success=True,
            message="Processed data retrieved successfully",
            data={
                "version": processed.get("version"),
                "processed_date": processed.get("processed_date"),
                "num_occupations": len(occupations),
                "num_skills": processed.get("num_skills"),
                "occupations": occupations
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to load processed data",
                error=str(e)
            ).model_dump()
        )


@router.get("/processed/version", response_model=BaseResponse)
async def get_processed_version():
    """
    Get version information for processed data
    Useful for checking what version you're working with
    """
    try:
        processed = load_processed_data()
        
        if not processed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message="Processed data not found"
                ).model_dump()
            )
        
        return BaseResponse(
            success=True,
            message="Version information retrieved",
            data={
                "version": processed.get("version"),
                "processed_date": processed.get("processed_date"),
                "num_occupations": processed.get("num_occupations"),
                "num_skills": processed.get("num_skills")
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to load version information",
                error=str(e)
            ).model_dump()
        )


@router.get("/catalog/search/openai", response_model=BaseResponse)
async def search_careers_openai(
    query: str = Query(..., description="Search query - can be job title, description, skills, industry, etc."),
    max_results: int = Query(10, ge=1, le=20, description="Maximum number of results to return")
):
    """
    Use OpenAI to search for careers based on a detailed search query.
    This helps users find careers even if they don't know the exact name.
    Can handle descriptions, skills, industries, job functions, etc.
    """
    try:
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    message="Search query is required"
                ).model_dump()
            )
        
        if not openai_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse(
                    success=False,
                    message="OpenAI service is not available"
                ).model_dump()
            )
        
        # Load all careers from catalog
        catalogs = load_catalog()
        
        # Convert to format expected by OpenAI service
        all_careers = []
        for catalog in catalogs:
            career_dict = {
                "career_id": catalog.occupation.career_id,
                "name": catalog.occupation.name,
                "soc_code": catalog.occupation.soc_code,
                "description": catalog.occupation.description
            }
            all_careers.append(career_dict)
        
        # Use OpenAI to search
        results = openai_service.search_careers(
            search_query=query,
            all_careers=all_careers,
            max_results=max_results
        )
        
        # Convert results to OccupationCatalog format for consistency
        result_catalogs = []
        for result in results:
            # Find the full catalog entry
            catalog = next(
                (c for c in catalogs if c.occupation.career_id == result["career_id"]),
                None
            )
            if catalog:
                result_catalogs.append({
                    "occupation": catalog.occupation.model_dump(),
                    "match_explanation": result.get("match_explanation", ""),
                    "match_score": result.get("match_score", 0.0)
                })
        
        return BaseResponse(
            success=True,
            message=f"Found {len(result_catalogs)} matching careers",
            data={
                "count": len(result_catalogs),
                "query": query,
                "results": result_catalogs
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to search careers",
                error=str(e)
            ).model_dump()
        )


@router.get("/processed/{career_id}", response_model=BaseResponse)
async def get_processed_occupation(career_id: str):
    """
    Get processed data for a specific occupation by career_id
    Returns skill vectors, task features, outlook features, and education data
    """
    try:
        processed = load_processed_data()
        
        if not processed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message="Processed data not found. Run process_data.py script first."
                ).model_dump()
            )
        
        occupation = next(
            (occ for occ in processed.get("occupations", []) if occ.get("career_id") == career_id),
            None
        )
        
        if not occupation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    message=f"Processed data not found for career_id {career_id}"
                ).model_dump()
            )
        
        return BaseResponse(
            success=True,
            message="Processed occupation data retrieved successfully",
            data={
                "version": processed.get("version"),
                "processed_date": processed.get("processed_date"),
                "occupation": occupation
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                message="Failed to load processed occupation data",
                error=str(e)
            ).model_dump()
        )


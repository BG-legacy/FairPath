"""
Pydantic schemas for request/response validation
Keeping it simple but making sure we validate everything
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# Base response schema - using this everywhere for consistency
class BaseResponse(BaseModel):
    """Standard response format"""
    success: bool = True
    message: str = ""
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    """Error response format"""
    success: bool = False
    message: str
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# Example request schemas - adjust these based on what you need
class ExampleRequest(BaseModel):
    """Example request with validation"""
    text: str = Field(..., min_length=1, max_length=1000, description="Some text input")
    count: int = Field(default=1, ge=1, le=100, description="Number of items")
    optional_field: Optional[str] = Field(None, max_length=500)
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text can't be empty")
        return v.strip()

class ExampleResponse(BaseModel):
    """Example response"""
    result: str
    processed_at: datetime
    metadata: Optional[Dict[str, Any]] = None

# Intake response schemas
class FeatureVectors(BaseModel):
    """Feature vectors in normalized profile"""
    skill_vector: List[float] = Field(..., description="Skill feature vector")
    interest_vector: List[float] = Field(..., description="RIASEC interest feature vector")
    values_vector: List[float] = Field(..., description="Work values feature vector")
    constraint_features: List[float] = Field(..., description="Constraint feature vector")
    combined_vector: List[float] = Field(..., description="Combined feature vector")

class NormalizedInterests(BaseModel):
    """Normalized interests structure"""
    riasec_scores: Dict[str, float] = Field(..., description="RIASEC category scores")
    raw_input: Optional[Union[List[str], str]] = Field(None, description="Original input")

class NormalizedProfileData(BaseModel):
    """Normalized profile data structure"""
    skills: List[str] = Field(default_factory=list, description="List of skills")
    interests: NormalizedInterests = Field(..., description="Normalized interests")
    values: Dict[str, float] = Field(default_factory=dict, description="Work values (impact, stability, flexibility)")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="User constraints")
    feature_vectors: FeatureVectors = Field(..., description="Feature vectors")

class DominantItem(BaseModel):
    """Dominant interest or value item"""
    category: Optional[str] = Field(None, description="RIASEC category (for interests)")
    value: Optional[str] = Field(None, description="Value name (for values)")
    score: float = Field(..., description="Score value")

class FeatureVectorStats(BaseModel):
    """Feature vector statistics"""
    dimension: int = Field(..., description="Vector dimension")
    non_zero_count: int = Field(..., description="Number of non-zero elements")
    max_value: float = Field(..., description="Maximum value")
    mean_value: float = Field(..., description="Mean value")
    std_value: float = Field(..., description="Standard deviation")

class ConstraintsSummary(BaseModel):
    """Constraints summary"""
    has_wage_constraint: bool = Field(..., description="Has wage constraint")
    has_location_constraint: bool = Field(..., description="Has location constraint")
    has_time_constraint: bool = Field(..., description="Has time constraint")
    constraint_count: int = Field(..., description="Total number of constraints")

class DerivedFeaturesSummary(BaseModel):
    """Derived features summary"""
    profile_completeness: float = Field(..., ge=0.0, le=1.0, description="Profile completeness score (0-1)")
    dominant_interests: List[DominantItem] = Field(default_factory=list, description="Top dominant interests")
    dominant_values: List[DominantItem] = Field(default_factory=list, description="Top dominant values")
    feature_vector_stats: FeatureVectorStats = Field(..., description="Feature vector statistics")
    constraints_summary: ConstraintsSummary = Field(..., description="Constraints summary")

class IntakeResponse(BaseModel):
    """Complete intake response structure"""
    normalized_profile: NormalizedProfileData = Field(..., description="Normalized profile data")
    derived_features_summary: DerivedFeaturesSummary = Field(..., description="Derived features summary")

# Add more schemas as needed for your actual endpoints


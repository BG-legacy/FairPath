"""
Data models for O*NET and BLS data
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Occupation(BaseModel):
    """Occupation catalog entry"""
    career_id: str = Field(..., description="Unique career identifier")
    name: str = Field(..., description="Occupation title")
    soc_code: str = Field(..., description="Standard Occupational Classification code")
    description: str = Field(..., description="Short description of the occupation")
    onet_soc_code: Optional[str] = Field(None, description="O*NET SOC code (may differ from BLS SOC)")
    alternate_titles: Optional[List[str]] = Field(default_factory=list, description="Alternative job titles")
    job_zone: Optional[int] = Field(None, description="O*NET Job Zone (1-5)")
    created_at: datetime = Field(default_factory=datetime.now)


class Skill(BaseModel):
    """Skill associated with an occupation"""
    skill_id: str = Field(..., description="Unique skill identifier")
    skill_name: str = Field(..., description="Name of the skill")
    element_id: Optional[str] = Field(None, description="O*NET element ID")
    importance: Optional[float] = Field(None, description="Importance rating (0-5)")
    level: Optional[float] = Field(None, description="Level rating (0-7)")
    soc_code: str = Field(..., description="SOC code of associated occupation")


class Task(BaseModel):
    """Task associated with an occupation"""
    task_id: str = Field(..., description="Unique task identifier")
    task_description: str = Field(..., description="Description of the task")
    task_type: Optional[str] = Field(None, description="Core or Supplemental")
    soc_code: str = Field(..., description="SOC code of associated occupation")
    incumbents_responding: Optional[int] = Field(None, description="Number of incumbents who responded")


class BLSProjection(BaseModel):
    """BLS employment projections"""
    soc_code: str = Field(..., description="SOC code")
    occupation_title: str = Field(..., description="Occupation title")
    employment_2024: Optional[int] = Field(None, description="Employment in 2024 (thousands)")
    employment_2034: Optional[int] = Field(None, description="Projected employment in 2034 (thousands)")
    change_2024_2034: Optional[int] = Field(None, description="Change in employment (thousands)")
    percent_change: Optional[float] = Field(None, description="Percent change 2024-2034")
    annual_openings: Optional[int] = Field(None, description="Annual average job openings")
    median_wage_2024: Optional[float] = Field(None, description="Median annual wage in 2024 (dollars)")
    typical_education: Optional[str] = Field(None, description="Typical education required")


class OccupationCatalog(BaseModel):
    """Complete occupation catalog with all related data"""
    occupation: Occupation
    skills: List[Skill] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)
    bls_projection: Optional[BLSProjection] = None


class DataDictionary(BaseModel):
    """Data dictionary entry for a file"""
    file_name: str
    file_type: str  # "O*NET" or "BLS"
    description: str
    columns: List[Dict[str, str]]  # [{"name": "col_name", "description": "col_desc", "type": "str/int/float"}]
    source: str
    last_updated: Optional[str] = None







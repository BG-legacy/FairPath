"""
Data ingestion service for O*NET and BLS data
Handles loading, normalizing, and cataloging occupation data
"""
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from models.data_models import (
    Occupation, Skill, Task, BLSProjection, OccupationCatalog, DataDictionary
)


class DataIngestionService:
    """Service for ingesting and processing O*NET and BLS data"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the data ingestion service
        
        Args:
            data_dir: Path to data directory. Defaults to backend/data
        """
        if data_dir is None:
            # Get the backend directory (parent of services)
            backend_dir = Path(__file__).parent.parent
            self.data_dir = backend_dir / "data"
        else:
            self.data_dir = Path(data_dir)
        
        self.onet_text_dir = self.data_dir / "db_30_1_text"
        self.occupations: Dict[str, Occupation] = {}
        self.skills: Dict[str, List[Skill]] = {}  # SOC -> List[Skill]
        self.tasks: Dict[str, List[Task]] = {}  # SOC -> List[Task]
        self.bls_projections: Dict[str, BLSProjection] = {}
        
    def normalize_soc_code(self, soc_code: str) -> str:
        """
        Normalize SOC code to consistent format (XX-XXXX.XX)
        
        Args:
            soc_code: SOC code in various formats
            
        Returns:
            Normalized SOC code
        """
        if not soc_code or pd.isna(soc_code):
            return ""
        
        # Convert to string and strip whitespace
        soc = str(soc_code).strip()
        
        # Remove any non-digit, non-dash, non-period characters
        soc = re.sub(r'[^\d\-.]', '', soc)
        
        # Handle different formats
        # Format: XX-XXXX.XX or XX-XXXX
        if '-' in soc:
            parts = soc.split('-')
            if len(parts) == 2:
                major = parts[0].zfill(2)  # Ensure 2 digits
                minor = parts[1]
                # Ensure minor part has proper format
                if '.' in minor:
                    minor_parts = minor.split('.')
                    if len(minor_parts) == 2:
                        return f"{major}-{minor_parts[0].zfill(4)}.{minor_parts[1].zfill(2)}"
                    else:
                        return f"{major}-{minor_parts[0].zfill(4)}.00"
                else:
                    # Try to infer format
                    if len(minor) >= 4:
                        return f"{major}-{minor[:4]}.{minor[4:].zfill(2) if len(minor) > 4 else '00'}"
                    else:
                        return f"{major}-{minor.zfill(4)}.00"
        
        # If no dash, try to parse as 6-7 digit code
        soc_clean = re.sub(r'[^\d]', '', soc)
        if len(soc_clean) >= 6:
            return f"{soc_clean[:2]}-{soc_clean[2:6]}.{soc_clean[6:].zfill(2) if len(soc_clean) > 6 else '00'}"
        
        return soc
    
    def load_onet_occupations(self) -> Dict[str, Occupation]:
        """
        Load O*NET occupation data from Occupation Data.txt
        
        Returns:
            Dictionary mapping normalized SOC codes to Occupation objects
        """
        occupations = {}
        file_path = self.onet_text_dir / "Occupation Data.txt"
        
        if not file_path.exists():
            raise FileNotFoundError(f"O*NET occupation data not found at {file_path}")
        
        # Read tab-separated file
        df = pd.read_csv(file_path, sep='\t', dtype=str)
        
        # Expected columns: O*NET-SOC Code, Title, Description
        for _, row in df.iterrows():
            onet_soc = str(row.get('O*NET-SOC Code', '')).strip()
            title = str(row.get('Title', '')).strip()
            description = str(row.get('Description', '')).strip()
            
            if not onet_soc or not title:
                continue
            
            # Normalize SOC code
            soc_code = self.normalize_soc_code(onet_soc)
            if not soc_code:
                continue
            
            # Create career_id from SOC (remove dashes and periods)
            career_id = soc_code.replace('-', '').replace('.', '')
            
            occupation = Occupation(
                career_id=career_id,
                name=title,
                soc_code=soc_code,
                description=description[:500] if description else title,  # Limit description length
                onet_soc_code=onet_soc
            )
            
            occupations[soc_code] = occupation
        
        self.occupations = occupations
        return occupations
    
    def load_onet_skills(self) -> Dict[str, List[Skill]]:
        """
        Load O*NET skills data from Skills.txt
        
        Returns:
            Dictionary mapping SOC codes to lists of Skill objects
        """
        skills_dict = {}
        file_path = self.onet_text_dir / "Skills.txt"
        
        if not file_path.exists():
            raise FileNotFoundError(f"O*NET skills data not found at {file_path}")
        
        # Read tab-separated file
        df = pd.read_csv(file_path, sep='\t', dtype=str)
        
        for _, row in df.iterrows():
            onet_soc = str(row.get('O*NET-SOC Code', '')).strip()
            element_id = str(row.get('Element ID', '')).strip()
            element_name = str(row.get('Element Name', '')).strip()
            scale_id = str(row.get('Scale ID', '')).strip()
            data_value = row.get('Data Value', '')
            
            if not onet_soc or not element_name:
                continue
            
            soc_code = self.normalize_soc_code(onet_soc)
            if not soc_code:
                continue
            
            # Parse data value
            importance = None
            level = None
            try:
                val = float(data_value) if pd.notna(data_value) else None
                if scale_id == 'IM':
                    importance = val
                elif scale_id == 'LV':
                    level = val
            except (ValueError, TypeError):
                pass
            
            skill_id = f"{soc_code}_{element_id}"
            skill = Skill(
                skill_id=skill_id,
                skill_name=element_name,
                element_id=element_id,
                importance=importance,
                level=level,
                soc_code=soc_code
            )
            
            if soc_code not in skills_dict:
                skills_dict[soc_code] = []
            
            # Check if skill already exists (same element_id)
            existing = next((s for s in skills_dict[soc_code] if s.element_id == element_id), None)
            if existing:
                # Update with missing data
                if importance is not None:
                    existing.importance = importance
                if level is not None:
                    existing.level = level
            else:
                skills_dict[soc_code].append(skill)
        
        self.skills = skills_dict
        return skills_dict
    
    def load_onet_tasks(self) -> Dict[str, List[Task]]:
        """
        Load O*NET tasks data from Task Statements.txt
        
        Returns:
            Dictionary mapping SOC codes to lists of Task objects
        """
        tasks_dict = {}
        file_path = self.onet_text_dir / "Task Statements.txt"
        
        if not file_path.exists():
            raise FileNotFoundError(f"O*NET tasks data not found at {file_path}")
        
        # Read tab-separated file
        df = pd.read_csv(file_path, sep='\t', dtype=str)
        
        for _, row in df.iterrows():
            onet_soc = str(row.get('O*NET-SOC Code', '')).strip()
            task_id = str(row.get('Task ID', '')).strip()
            task = str(row.get('Task', '')).strip()
            task_type = str(row.get('Task Type', '')).strip()
            incumbents = row.get('Incumbents Responding', '')
            
            if not onet_soc or not task:
                continue
            
            soc_code = self.normalize_soc_code(onet_soc)
            if not soc_code:
                continue
            
            incumbents_count = None
            try:
                if pd.notna(incumbents):
                    incumbents_count = int(float(incumbents))
            except (ValueError, TypeError):
                pass
            
            task_obj = Task(
                task_id=f"{soc_code}_{task_id}",
                task_description=task,
                task_type=task_type if task_type else None,
                soc_code=soc_code,
                incumbents_responding=incumbents_count
            )
            
            if soc_code not in tasks_dict:
                tasks_dict[soc_code] = []
            tasks_dict[soc_code].append(task_obj)
        
        self.tasks = tasks_dict
        return tasks_dict
    
    def load_bls_projections(self) -> Dict[str, BLSProjection]:
        """
        Load BLS employment projections from occupation.xlsx
        
        Returns:
            Dictionary mapping SOC codes to BLSProjection objects
        """
        projections = {}
        file_path = self.data_dir / "occupation.xlsx"
        
        if not file_path.exists():
            raise FileNotFoundError(f"BLS occupation data not found at {file_path}")
        
        # Read Table 1.2 which has detailed occupation projections
        try:
            df = pd.read_excel(file_path, sheet_name='Table 1.2', header=1)
        except Exception:
            # Try without header
            df = pd.read_excel(file_path, sheet_name='Table 1.2')
        
        # Map column names (handle variations)
        soc_col = None
        title_col = None
        emp_2024_col = None
        emp_2034_col = None
        change_col = None
        pct_change_col = None
        wage_col = None
        openings_col = None
        education_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if 'code' in col_lower or 'soc' in col_lower:
                soc_col = col
            elif 'title' in col_lower and '2024' in col_lower:
                title_col = col
            elif 'employment, 2024' in col_lower or 'employment 2024' in col_lower:
                emp_2024_col = col
            elif 'employment, 2034' in col_lower or 'employment 2034' in col_lower:
                emp_2034_col = col
            elif 'change, numeric' in col_lower or 'change numeric' in col_lower:
                change_col = col
            elif 'change, percent' in col_lower or 'change percent' in col_lower:
                pct_change_col = col
            elif 'wage' in col_lower and '2024' in col_lower:
                wage_col = col
            elif 'openings' in col_lower:
                openings_col = col
            elif 'education' in col_lower and 'entry' in col_lower:
                education_col = col
        
        # Process each row
        for _, row in df.iterrows():
            # Get SOC code
            soc_code = None
            if soc_col:
                soc_val = str(row.get(soc_col, '')).strip()
                if soc_val and soc_val != 'nan' and soc_val != '—':
                    soc_code = self.normalize_soc_code(soc_val)
            
            # Get title
            title = None
            if title_col:
                title_val = str(row.get(title_col, '')).strip()
                if title_val and title_val != 'nan' and title_val != '—':
                    title = title_val.strip()
            
            # Skip if missing essential data
            if not soc_code or not title:
                continue
            
            # Skip summary rows (they have occupation type = 'Summary')
            occupation_type = str(row.get('Occupation type', '')).strip()
            if occupation_type == 'Summary':
                continue
            
            # Extract numeric values
            employment_2024 = None
            employment_2034 = None
            change = None
            percent_change = None
            median_wage = None
            annual_openings = None
            typical_education = None
            
            if emp_2024_col:
                try:
                    val = row.get(emp_2024_col)
                    if pd.notna(val):
                        employment_2024 = int(float(val) * 1000)  # Convert from thousands
                except (ValueError, TypeError):
                    pass
            
            if emp_2034_col:
                try:
                    val = row.get(emp_2034_col)
                    if pd.notna(val):
                        employment_2034 = int(float(val) * 1000)  # Convert from thousands
                except (ValueError, TypeError):
                    pass
            
            if change_col:
                try:
                    val = row.get(change_col)
                    if pd.notna(val):
                        change = int(float(val) * 1000)  # Convert from thousands
                except (ValueError, TypeError):
                    pass
            
            if pct_change_col:
                try:
                    val = row.get(pct_change_col)
                    if pd.notna(val):
                        percent_change = float(val)
                except (ValueError, TypeError):
                    pass
            
            if wage_col:
                try:
                    val = row.get(wage_col)
                    if pd.notna(val):
                        median_wage = float(val)
                except (ValueError, TypeError):
                    pass
            
            if openings_col:
                try:
                    val = row.get(openings_col)
                    if pd.notna(val):
                        annual_openings = int(float(val) * 1000)  # Convert from thousands
                except (ValueError, TypeError):
                    pass
            
            if education_col:
                val = str(row.get(education_col, '')).strip()
                if val and val != 'nan' and val != '—':
                    typical_education = val
            
            projection = BLSProjection(
                soc_code=soc_code,
                occupation_title=title,
                employment_2024=employment_2024,
                employment_2034=employment_2034,
                change_2024_2034=change,
                percent_change=percent_change,
                annual_openings=annual_openings,
                median_wage_2024=median_wage,
                typical_education=typical_education
            )
            
            projections[soc_code] = projection
        
        self.bls_projections = projections
        return projections
    
    def build_occupation_catalog(self, min_occupations: int = 50, max_occupations: int = 150) -> List[OccupationCatalog]:
        """
        Build complete occupation catalog with all related data
        
        Args:
            min_occupations: Minimum number of occupations to include
            max_occupations: Maximum number of occupations to include
            
        Returns:
            List of OccupationCatalog objects
        """
        # Load all data if not already loaded
        if not self.occupations:
            self.load_onet_occupations()
        if not self.skills:
            self.load_onet_skills()
        if not self.tasks:
            self.load_onet_tasks()
        if not self.bls_projections:
            try:
                self.load_bls_projections()
            except Exception as e:
                print(f"Warning: Could not load BLS projections: {e}")
        
        catalogs = []
        
        # Filter occupations - prioritize those with complete data
        # Score occupations by data completeness
        occupation_scores = {}
        for soc_code, occupation in self.occupations.items():
            score = 0
            if soc_code in self.skills and len(self.skills[soc_code]) > 0:
                score += 2
            if soc_code in self.tasks and len(self.tasks[soc_code]) > 0:
                score += 2
            if soc_code in self.bls_projections:
                score += 1
            occupation_scores[soc_code] = score
        
        # Sort by score (descending) and take top occupations
        sorted_occupations = sorted(
            occupation_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Select occupations within range
        selected_soc_codes = [soc for soc, score in sorted_occupations[:max_occupations]]
        
        # Ensure we have at least min_occupations
        if len(selected_soc_codes) < min_occupations:
            # Add more occupations even if they have less data
            all_soc_codes = list(self.occupations.keys())
            for soc in all_soc_codes:
                if soc not in selected_soc_codes and len(selected_soc_codes) < min_occupations:
                    selected_soc_codes.append(soc)
        
        # Build catalogs for selected occupations
        for soc_code in selected_soc_codes:
            occupation = self.occupations.get(soc_code)
            if not occupation:
                continue
            
            skills = self.skills.get(soc_code, [])
            tasks = self.tasks.get(soc_code, [])
            bls_projection = self.bls_projections.get(soc_code)
            
            catalog = OccupationCatalog(
                occupation=occupation,
                skills=skills,
                tasks=tasks,
                bls_projection=bls_projection
            )
            catalogs.append(catalog)
        
        return catalogs
    
    def create_data_dictionary(self) -> List[DataDictionary]:
        """
        Create data dictionary documenting all data files
        
        Returns:
            List of DataDictionary objects
        """
        dictionaries = []
        
        # O*NET Occupation Data
        dictionaries.append(DataDictionary(
            file_name="Occupation Data.txt",
            file_type="O*NET",
            description="O*NET occupation catalog with titles and descriptions",
            columns=[
                {"name": "O*NET-SOC Code", "description": "O*NET Standard Occupational Classification code", "type": "str"},
                {"name": "Title", "description": "Occupation title", "type": "str"},
                {"name": "Description", "description": "Detailed occupation description", "type": "str"}
            ],
            source="O*NET 30.1 Database",
            last_updated="2025-12"
        ))
        
        # O*NET Skills
        dictionaries.append(DataDictionary(
            file_name="Skills.txt",
            file_type="O*NET",
            description="Skills ratings for occupations (importance and level)",
            columns=[
                {"name": "O*NET-SOC Code", "description": "O*NET SOC code", "type": "str"},
                {"name": "Element ID", "description": "O*NET element identifier", "type": "str"},
                {"name": "Element Name", "description": "Skill name", "type": "str"},
                {"name": "Scale ID", "description": "IM (Importance) or LV (Level)", "type": "str"},
                {"name": "Data Value", "description": "Rating value (0-5 for IM, 0-7 for LV)", "type": "float"}
            ],
            source="O*NET 30.1 Database",
            last_updated="2025-12"
        ))
        
        # O*NET Tasks
        dictionaries.append(DataDictionary(
            file_name="Task Statements.txt",
            file_type="O*NET",
            description="Task statements for occupations",
            columns=[
                {"name": "O*NET-SOC Code", "description": "O*NET SOC code", "type": "str"},
                {"name": "Task ID", "description": "Unique task identifier", "type": "str"},
                {"name": "Task", "description": "Task description", "type": "str"},
                {"name": "Task Type", "description": "Core or Supplemental", "type": "str"},
                {"name": "Incumbents Responding", "description": "Number of incumbents who responded", "type": "int"}
            ],
            source="O*NET 30.1 Database",
            last_updated="2025-12"
        ))
        
        # BLS Occupation Projections
        dictionaries.append(DataDictionary(
            file_name="occupation.xlsx",
            file_type="BLS",
            description="BLS employment projections and wage data by occupation",
            columns=[
                {"name": "2024 National Employment Matrix title", "description": "Occupation title", "type": "str"},
                {"name": "Employment 2024", "description": "Employment in 2024 (thousands)", "type": "int"},
                {"name": "Employment 2034", "description": "Projected employment in 2034 (thousands)", "type": "int"},
                {"name": "Change 2024-2034", "description": "Change in employment (thousands)", "type": "int"},
                {"name": "Percent change", "description": "Percent change 2024-2034", "type": "float"},
                {"name": "Median annual wage 2024", "description": "Median annual wage in dollars", "type": "float"}
            ],
            source="BLS Employment Projections 2024-2034",
            last_updated="2024"
        ))
        
        return dictionaries


"""
Data processing service - generates processed datasets from raw data
Creates skill vectors, task features, outlook features, and education data
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from services.data_ingestion import DataIngestionService
from models.data_models import OccupationCatalog


class DataProcessingService:
    """
    Takes the raw catalog and processes it into feature vectors and structured data
    I'm generating skill vectors, task features, outlook scores, and education data
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent / "data"
        self.artifacts_dir = Path(__file__).parent.parent / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)
        
        # Version stamp - helps track what version of processed data we're using
        self.version = "1.0.0"
        self.processed_date = datetime.now().isoformat()
        
        # I'll cache the unique skills list so I can build consistent vectors
        self._unique_skills_cache = None
    
    def get_all_unique_skills(self, catalogs: List[OccupationCatalog]) -> List[str]:
        """
        Get all unique skill names across all occupations
        Need this to build consistent skill vectors
        """
        if self._unique_skills_cache is not None:
            return self._unique_skills_cache
        
        skill_set = set()
        for catalog in catalogs:
            for skill in catalog.skills:
                skill_set.add(skill.skill_name)
        
        # Sort for consistency
        skills_list = sorted(list(skill_set))
        self._unique_skills_cache = skills_list
        return skills_list
    
    def generate_skill_vector(self, catalog: OccupationCatalog, all_skills: List[str]) -> Dict[str, Any]:
        """
        Generate a skill vector for an occupation
        Using importance and level ratings to create a normalized vector
        """
        # Initialize vector with zeros
        importance_vector = np.zeros(len(all_skills))
        level_vector = np.zeros(len(all_skills))
        
        # Build a lookup for this occupation's skills
        skill_lookup = {skill.skill_name: skill for skill in catalog.skills}
        
        # Fill in the vectors
        for idx, skill_name in enumerate(all_skills):
            if skill_name in skill_lookup:
                skill = skill_lookup[skill_name]
                # Normalize importance (0-5 scale) to 0-1
                if skill.importance is not None:
                    importance_vector[idx] = skill.importance / 5.0
                # Normalize level (0-7 scale) to 0-1
                if skill.level is not None:
                    level_vector[idx] = skill.level / 7.0
        
        # I'm also creating a combined score - weighted average
        # Importance matters more, but level is useful too
        combined_vector = (importance_vector * 0.6) + (level_vector * 0.4)
        
        return {
            "importance": importance_vector.tolist(),
            "level": level_vector.tolist(),
            "combined": combined_vector.tolist(),
            "skill_names": all_skills,
            "num_skills": len([s for s in catalog.skills if s.importance is not None or s.level is not None])
        }
    
    def generate_task_features(self, catalog: OccupationCatalog) -> Dict[str, Any]:
        """
        Generate task features - could be used as automation proxy
        Looking at task complexity, variety, and type distribution
        I'm basically trying to figure out how automatable a job might be based on tasks
        """
        tasks = catalog.tasks
        
        if not tasks:
            # No tasks means I can't really say much
            return {
                "num_tasks": 0,
                "num_core_tasks": 0,
                "num_supplemental_tasks": 0,
                "avg_incumbents": 0,
                "task_complexity_score": 0.0,
                "automation_proxy": 0.0  # Lower = more automatable potentially
            }
        
        # Count task types - core tasks are the main ones, supplemental are extra
        core_tasks = [t for t in tasks if t.task_type == "Core"]
        supplemental_tasks = [t for t in tasks if t.task_type == "Supplemental"]
        
        # Calculate average incumbents responding - this tells me how common the tasks are
        incumbents_list = [t.incumbents_responding for t in tasks if t.incumbents_responding is not None]
        avg_incumbents = np.mean(incumbents_list) if incumbents_list else 0
        
        # Task complexity - more tasks and more core tasks = potentially less automatable
        # This is a simple heuristic, could definitely be improved but it works for now
        task_complexity = len(tasks) / 50.0  # Normalize by typical max (rough guess)
        core_ratio = len(core_tasks) / len(tasks) if tasks else 0
        
        # Automation proxy - higher score = potentially less automatable
        # More tasks, more core tasks, higher incumbents = less automatable
        # The weights here are kind of arbitrary but seem reasonable
        automation_proxy = (task_complexity * 0.4) + (core_ratio * 0.4) + (min(avg_incumbents / 100.0, 1.0) * 0.2)
        
        return {
            "num_tasks": len(tasks),
            "num_core_tasks": len(core_tasks),
            "num_supplemental_tasks": len(supplemental_tasks),
            "avg_incumbents": float(avg_incumbents),
            "task_complexity_score": float(task_complexity),
            "automation_proxy": float(automation_proxy),
            "core_task_ratio": float(core_ratio)
        }
    
    def generate_outlook_features(self, catalog: OccupationCatalog) -> Dict[str, Any]:
        """
        Generate outlook features from BLS data
        Creating derived metrics like growth rate, opportunity score, etc.
        I'm basically trying to make the BLS numbers more useful by combining them
        """
        bls = catalog.bls_projection
        
        if not bls:
            # Return defaults if no BLS data - can't do much without it
            return {
                "has_projection": False,
                "growth_rate": 0.0,
                "opportunity_score": 0.0,
                "wage_score": 0.0,
                "stability_score": 0.0
            }
        
        # Growth rate from percent change - straightforward
        growth_rate = bls.percent_change if bls.percent_change else 0.0
        
        # Opportunity score - combines growth and openings
        # Normalize annual openings (assuming max around 200k - might need to adjust this)
        openings_score = min((bls.annual_openings or 0) / 200000.0, 1.0) if bls.annual_openings else 0.0
        growth_score = min(max(growth_rate / 20.0, 0.0), 1.0)  # Cap at 20% growth = 1.0
        
        # Equal weight for now, could tweak this
        opportunity_score = (openings_score * 0.5) + (growth_score * 0.5)
        
        # Wage score - normalize median wage (assuming range 20k-250k)
        # These ranges are rough estimates, might need to update
        wage_score = 0.0
        if bls.median_wage_2024:
            wage_score = min(max((bls.median_wage_2024 - 20000) / 230000.0, 0.0), 1.0)
        
        # Stability score - based on employment size and growth
        # Larger occupations with steady growth = more stable
        # This is my attempt to quantify job security
        employment_size = bls.employment_2024 or 0
        size_score = min(employment_size / 1000000.0, 1.0)  # 1M+ = max
        growth_stability = 1.0 - abs(growth_rate / 50.0)  # Closer to 0% change = more stable
        growth_stability = max(growth_stability, 0.0)
        
        # Size matters more for stability, but growth matters too
        stability_score = (size_score * 0.6) + (growth_stability * 0.4)
        
        return {
            "has_projection": True,
            "growth_rate": float(growth_rate),
            "employment_2024": bls.employment_2024,
            "employment_2034": bls.employment_2034,
            "annual_openings": bls.annual_openings,
            "median_wage_2024": bls.median_wage_2024,
            "opportunity_score": float(opportunity_score),
            "wage_score": float(wage_score),
            "stability_score": float(stability_score),
            "growth_category": self._categorize_growth(growth_rate)
        }
    
    def _categorize_growth(self, growth_rate: float) -> str:
        """Simple categorization of growth rate"""
        if growth_rate < -5:
            return "declining"
        elif growth_rate < 0:
            return "slight_decline"
        elif growth_rate < 5:
            return "stable"
        elif growth_rate < 10:
            return "growing"
        elif growth_rate < 20:
            return "fast_growing"
        else:
            return "very_fast_growing"
    
    def generate_education_data(self, catalog: OccupationCatalog) -> Dict[str, Any]:
        """
        Generate curated education/certification data
        Quality over quantity - only storing meaningful data
        I'm trying to keep this clean and useful, not just dump everything
        """
        bls = catalog.bls_projection
        
        # Start with basic structure
        education_data = {
            "typical_entry_education": None,
            "education_level": None,
            "requires_certification": False,
            "requires_license": False,
            "typical_training": None
        }
        
        if bls and bls.typical_education:
            typical_ed = bls.typical_education.strip()
            
            # Map to standardized levels - doing some basic string matching
            # Could be more sophisticated but this works for most cases
            if "doctoral" in typical_ed.lower() or "ph.d" in typical_ed.lower():
                education_data["education_level"] = "doctoral"
                education_data["typical_entry_education"] = typical_ed
            elif "professional" in typical_ed.lower() or "m.d" in typical_ed.lower() or "j.d" in typical_ed.lower():
                education_data["education_level"] = "professional"
                education_data["typical_entry_education"] = typical_ed
            elif "master" in typical_ed.lower():
                education_data["education_level"] = "masters"
                education_data["typical_entry_education"] = typical_ed
            elif "bachelor" in typical_ed.lower():
                education_data["education_level"] = "bachelors"
                education_data["typical_entry_education"] = typical_ed
            elif "associate" in typical_ed.lower():
                education_data["education_level"] = "associates"
                education_data["typical_entry_education"] = typical_ed
            elif "some college" in typical_ed.lower() or "postsecondary" in typical_ed.lower():
                education_data["education_level"] = "some_college"
                education_data["typical_entry_education"] = typical_ed
            elif "high school" in typical_ed.lower():
                education_data["education_level"] = "high_school"
                education_data["typical_entry_education"] = typical_ed
            else:
                # Keep the original if we can't categorize - better than nothing
                education_data["typical_entry_education"] = typical_ed
            
            # Check for certification/licensing keywords - simple but works
            if "certificate" in typical_ed.lower() or "certification" in typical_ed.lower():
                education_data["requires_certification"] = True
            if "license" in typical_ed.lower() or "licensed" in typical_ed.lower():
                education_data["requires_license"] = True
        
        return education_data
    
    def process_all_catalogs(self, catalogs: List[OccupationCatalog]) -> Dict[str, Any]:
        """
        Process all catalogs and generate all feature vectors
        Returns a dictionary with all processed data
        """
        print(f"Processing {len(catalogs)} occupations...")
        
        # Get unique skills list first
        all_skills = self.get_all_unique_skills(catalogs)
        print(f"Found {len(all_skills)} unique skills")
        
        processed_data = {
            "version": self.version,
            "processed_date": self.processed_date,
            "num_occupations": len(catalogs),
            "num_skills": len(all_skills),
            "skill_names": all_skills,
            "occupations": []
        }
        
        # Process each occupation
        for catalog in catalogs:
            soc_code = catalog.occupation.soc_code
            career_id = catalog.occupation.career_id
            
            # Generate all features
            skill_vector = self.generate_skill_vector(catalog, all_skills)
            task_features = self.generate_task_features(catalog)
            outlook_features = self.generate_outlook_features(catalog)
            education_data = self.generate_education_data(catalog)
            
            occupation_data = {
                "career_id": career_id,
                "soc_code": soc_code,
                "name": catalog.occupation.name,
                "skill_vector": skill_vector,
                "task_features": task_features,
                "outlook_features": outlook_features,
                "education_data": education_data
            }
            
            processed_data["occupations"].append(occupation_data)
        
        return processed_data
    
    def save_processed_data(self, processed_data: Dict[str, Any], filename: str = "processed_data.json"):
        """
        Save processed data to artifacts directory
        Includes version stamp for reproducibility
        """
        output_path = self.artifacts_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(processed_data, f, indent=2)
        
        print(f"Saved processed data to {output_path}")
        print(f"Version: {processed_data['version']}, Date: {processed_data['processed_date']}")
        
        return output_path
    
    def load_processed_data(self, filename: str = "processed_data.json") -> Optional[Dict[str, Any]]:
        """
        Load processed data from file
        """
        file_path = self.artifacts_dir / filename
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            return json.load(f)


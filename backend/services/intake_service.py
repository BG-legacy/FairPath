"""
Intake service for normalizing user profiles and deriving features
"""
import numpy as np
from typing import Dict, List, Optional, Any, Union
from services.recommendation_service import CareerRecommendationService


class IntakeService:
    """Service for normalizing user intake data and deriving features"""
    
    # RIASEC categories
    RIASEC_CATEGORIES = [
        "Realistic", "Investigative", "Artistic",
        "Social", "Enterprising", "Conventional"
    ]
    
    def __init__(self):
        self.recommendation_service = CareerRecommendationService()
    
    def _parse_interests_text(self, text: str) -> Dict[str, float]:
        """
        Parse text description of interests into RIASEC scores
        Simple keyword matching approach
        """
        text_lower = text.lower()
        scores = {}
        
        # Keywords for each RIASEC category
        keywords = {
            "Realistic": ["practical", "hands-on", "mechanical", "technical", "construction", "repair", "tools", "physical", "outdoor", "building"],
            "Investigative": ["research", "analyze", "investigate", "science", "math", "data", "experiment", "theory", "study", "intellectual"],
            "Artistic": ["creative", "art", "design", "music", "writing", "imagination", "expression", "aesthetic", "original", "innovative"],
            "Social": ["help", "people", "teach", "care", "service", "counsel", "community", "support", "interpersonal", "relationships"],
            "Enterprising": ["lead", "business", "sales", "manage", "persuade", "entrepreneur", "executive", "negotiate", "influence", "competitive"],
            "Conventional": ["organized", "structured", "systematic", "routine", "data entry", "administrative", "detail", "order", "procedure", "follow"]
        }
        
        # Count keyword matches for each category
        for category, category_keywords in keywords.items():
            matches = sum(1 for keyword in category_keywords if keyword in text_lower)
            # Normalize to 0-7 scale (simple linear scaling)
            score = min(7.0, (matches / len(category_keywords)) * 7.0)
            if score > 0:
                scores[category] = score
        
        # If no matches found, return empty dict (will be handled as no interests)
        return scores
    
    def _normalize_interests(
        self,
        interests: Optional[Union[List[str], str]]
    ) -> Dict[str, float]:
        """Normalize interests to RIASEC scores"""
        if interests is None:
            return {}
        
        if isinstance(interests, str):
            # Parse text description
            return self._parse_interests_text(interests)
        elif isinstance(interests, list):
            # Convert list to scores (each mentioned category gets score of 5)
            scores = {}
            for category in interests:
                if category in self.RIASEC_CATEGORIES:
                    scores[category] = 5.0  # Default score when category is mentioned
            return scores
        
        return {}
    
    def _normalize_values(self, values: Optional[Dict[str, float]]) -> Dict[str, float]:
        """Normalize values (impact, stability, flexibility)"""
        if values is None:
            return {}
        
        normalized = {}
        for key in ["impact", "stability", "flexibility"]:
            if key in values:
                # Ensure value is in 0-7 range
                normalized[key] = max(0.0, min(7.0, float(values[key])))
        
        return normalized
    
    def _derive_features_summary(
        self,
        normalized_profile: Dict[str, Any],
        values: Dict[str, float],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Derive summary features from normalized profile"""
        summary = {
            "profile_completeness": 0.0,
            "dominant_interests": [],
            "dominant_values": [],
            "feature_vector_stats": {},
            "constraints_summary": {}
        }
        
        # Calculate profile completeness
        completeness_scores = []
        
        # Skills completeness
        skill_vector = normalized_profile.get("skill_vector", [])
        skills_count = sum(1 for s in skill_vector if s > 0)
        if skill_vector:
            skills_completeness = min(1.0, skills_count / 10.0)  # At least 10 skills = full
            completeness_scores.append(skills_completeness)
        
        # Interests completeness
        interest_vector = normalized_profile.get("interest_vector", [])
        interests_count = sum(1 for i in interest_vector if i > 0)
        if self.RIASEC_CATEGORIES:
            interests_completeness = min(1.0, interests_count / len(self.RIASEC_CATEGORIES))
            completeness_scores.append(interests_completeness)
        
        # Values completeness
        if values:
            values_completeness = min(1.0, len(values) / 3.0)
            completeness_scores.append(values_completeness)
        
        # Constraints completeness
        if constraints:
            constraints_completeness = min(1.0, len(constraints) / 3.0)
            completeness_scores.append(constraints_completeness)
        
        if completeness_scores:
            summary["profile_completeness"] = sum(completeness_scores) / len(completeness_scores)
        
        # Dominant interests (top 2)
        if interest_vector:
            interest_scores = [
                (category, score)
                for category, score in zip(self.RIASEC_CATEGORIES, interest_vector)
            ]
            interest_scores.sort(key=lambda x: x[1], reverse=True)
            summary["dominant_interests"] = [
                {"category": cat, "score": float(score)}
                for cat, score in interest_scores[:2] if score > 0
            ]
        
        # Dominant values
        if values:
            value_items = sorted(values.items(), key=lambda x: x[1], reverse=True)
            summary["dominant_values"] = [
                {"value": value, "score": float(score)}
                for value, score in value_items[:2] if score > 0
            ]
        
        # Feature vector statistics
        combined_vector = normalized_profile.get("combined_vector", [])
        if combined_vector:
            vec_array = np.array(combined_vector)
            summary["feature_vector_stats"] = {
                "dimension": len(combined_vector),
                "non_zero_count": int(np.count_nonzero(vec_array)),
                "max_value": float(np.max(vec_array)),
                "mean_value": float(np.mean(vec_array)),
                "std_value": float(np.std(vec_array))
            }
        
        # Constraints summary
        if constraints:
            summary["constraints_summary"] = {
                "has_wage_constraint": "min_wage" in constraints,
                "has_location_constraint": "remote_preferred" in constraints or "location_preference" in constraints,
                "has_time_constraint": "max_hours" in constraints or "flexible_hours" in constraints,
                "constraint_count": len(constraints)
            }
        
        return summary
    
    def normalize_profile(
        self,
        skills: Optional[List[str]] = None,
        interests: Optional[Union[List[str], str]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        values: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Normalize user profile and derive features
        
        Args:
            skills: List of skill names
            interests: RIASEC categories (list) or text description
            constraints: Dict with cost/time/location constraints
            values: Dict with impact/stability/flexibility scores (0-7)
        
        Returns:
            Dict with normalized profile and derived features summary
        """
        # Normalize interests to RIASEC scores
        riasec_interests = self._normalize_interests(interests)
        
        # Normalize values
        normalized_values = self._normalize_values(values)
        
        # Map values to work_values format (for compatibility with recommendation service)
        # Map impact/stability/flexibility to existing work_values structure
        work_values_mapping = {}
        # We'll keep values separate for the summary, but can use work_values for feature vector
        
        # Build feature vector using recommendation service
        normalized_profile = self.recommendation_service.build_user_feature_vector(
            skills=skills,
            skill_importance=None,  # Not provided in intake
            interests=riasec_interests if riasec_interests else None,
            work_values=None,  # Using separate values system
            constraints=constraints
        )
        
        # Add values information to normalized profile
        normalized_profile["values"] = normalized_values
        normalized_profile["values_vector"] = [
            normalized_values.get("impact", 0.0) / 7.0,
            normalized_values.get("stability", 0.0) / 7.0,
            normalized_values.get("flexibility", 0.0) / 7.0
        ]
        
        # Derive features summary
        features_summary = self._derive_features_summary(
            normalized_profile,
            normalized_values,
            constraints
        )
        
        return {
            "normalized_profile": {
                "skills": skills or [],
                "interests": {
                    "riasec_scores": riasec_interests,
                    "raw_input": interests
                },
                "values": normalized_values,
                "constraints": constraints or {},
                "feature_vectors": {
                    "skill_vector": normalized_profile.get("skill_vector", []),
                    "interest_vector": normalized_profile.get("interest_vector", []),
                    "values_vector": normalized_profile.get("values_vector", []),
                    "constraint_features": normalized_profile.get("constraint_features", []),
                    "combined_vector": normalized_profile.get("combined_vector", [])
                }
            },
            "derived_features_summary": features_summary
        }


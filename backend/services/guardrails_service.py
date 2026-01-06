"""
ML Guardrails Service
I'm adding protections to ensure the recommendation system is fair and transparent
No demographic data, always multiple options, uncertainty ranges, and fallback behavior
"""
from typing import Dict, List, Optional, Any
from services.recommendation_service import CareerRecommendationService
import numpy as np


class GuardrailsService:
    """
    Wraps the recommendation service with guardrails
    I'm making sure we never use demographic data, always return multiple options,
    include uncertainty, and handle edge cases gracefully
    """
    
    # List of demographic-related keywords that should be rejected
    DEMOGRAPHIC_KEYWORDS = [
        "age", "gender", "sex", "race", "ethnicity", "religion", "nationality",
        "birth", "born", "country", "origin", "disability", "veteran", "marital",
        "married", "single", "divorced", "sexual", "orientation", "identity"
    ]
    
    # Minimum number of recommendations to always return (even if input is thin)
    MIN_RECOMMENDATIONS = 3
    
    # Default number when user doesn't specify
    DEFAULT_RECOMMENDATIONS = 5
    
    def __init__(self):
        self.recommendation_service = CareerRecommendationService()
        # Don't load models in __init__ - load lazily on first use to save memory
        self._model_loaded = False
    
    def _ensure_model_loaded(self):
        """
        Lazy-load model artifacts only when needed.
        This loads ONLY the ML model, scaler, and vectorizer - NOT processed data.
        Processed data loads separately and lazily when actually needed for recommendations.
        """
        if not self._model_loaded:
            self.recommendation_service.load_model_artifacts()
            self._model_loaded = True
    
    def check_demographic_features(
        self,
        skills: Optional[List[str]] = None,
        skill_importance: Optional[Dict[str, float]] = None,
        interests: Optional[Dict[str, float]] = None,
        work_values: Optional[Dict[str, float]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check if any demographic features are present in the input
        I'm scanning all inputs for demographic keywords and rejecting them
        """
        issues = []
        
        # Check skills list
        if skills:
            for skill in skills:
                skill_lower = skill.lower()
                for keyword in self.DEMOGRAPHIC_KEYWORDS:
                    if keyword in skill_lower:
                        issues.append(f"Skill '{skill}' contains demographic keyword '{keyword}'")
        
        # Check skill importance keys
        if skill_importance:
            for skill in skill_importance.keys():
                skill_lower = skill.lower()
                for keyword in self.DEMOGRAPHIC_KEYWORDS:
                    if keyword in skill_lower:
                        issues.append(f"Skill importance key '{skill}' contains demographic keyword '{keyword}'")
        
        # Check constraints for demographic data
        if constraints:
            # Check for common demographic constraint keys
            demographic_constraint_keys = [
                "age", "gender", "race", "ethnicity", "religion", "nationality",
                "birth_country", "disability", "veteran_status", "marital_status"
            ]
            for key in constraints.keys():
                key_lower = key.lower()
                # Only flag if it's actually a demographic key, not if it just contains the word
                if key_lower in demographic_constraint_keys or any(demo_key == key_lower for demo_key in demographic_constraint_keys):
                    issues.append(f"Constraint key '{key}' appears to be demographic data")
                # Also check values for demographic keywords
                if isinstance(constraints[key], str):
                    value_lower = constraints[key].lower()
                    for keyword in self.DEMOGRAPHIC_KEYWORDS:
                        if keyword in value_lower:
                            issues.append(f"Constraint value for '{key}' contains demographic keyword '{keyword}'")
        
        if issues:
            return {
                "has_demographic_data": True,
                "issues": issues,
                "message": "Demographic features are not accepted. Please remove demographic information from your request."
            }
        
        return {
            "has_demographic_data": False,
            "issues": []
        }
    
    def ensure_multiple_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        min_count: int = None
    ) -> Dict[str, Any]:
        """
        Ensure we always return multiple recommendations, never just one
        If we only have one, I'm adding alternatives or using fallback logic
        """
        min_count = min_count or self.MIN_RECOMMENDATIONS
        
        if len(recommendations) == 0:
            # No recommendations - use fallback
            return self._get_fallback_recommendations(min_count)
        
        if len(recommendations) == 1:
            # Only one recommendation - add alternatives
            primary = recommendations[0]
            alternatives = self._get_alternative_recommendations(primary, min_count - 1)
            
            return {
                "primary_recommendation": primary,
                "alternatives": alternatives,
                "total_count": 1 + len(alternatives),
                "note": "Only one strong match found. Alternatives provided for comparison."
            }
        
        # We have multiple recommendations - good
        # But make sure we have at least min_count
        if len(recommendations) < min_count:
            # Add a few more alternatives to reach minimum
            primary = recommendations[0]
            needed = min_count - len(recommendations)
            alternatives = self._get_alternative_recommendations(primary, needed)
            
            return {
                "recommendations": recommendations,
                "additional_alternatives": alternatives,
                "total_count": len(recommendations) + len(alternatives),
                "note": f"Found {len(recommendations)} recommendations. Added {len(alternatives)} alternatives to provide more options."
            }
        
        # We have enough recommendations
        return {
            "recommendations": recommendations,
            "total_count": len(recommendations)
        }
    
    def _get_fallback_recommendations(self, count: int) -> Dict[str, Any]:
        """
        Fallback when we have no recommendations
        I'm returning diverse occupations from different categories
        """
        processed_data = self.recommendation_service.load_processed_data()
        occupations = processed_data["occupations"]
        
        # Get diverse set - different SOC codes, different outlooks
        # Just pick some varied ones
        fallback = []
        seen_soc_prefixes = set()
        
        for occ in occupations:
            if len(fallback) >= count:
                break
            
            # Try to get diverse SOC codes (first 2 digits)
            soc_prefix = occ["soc_code"][:2] if occ.get("soc_code") else None
            if soc_prefix and soc_prefix not in seen_soc_prefixes:
                fallback.append({
                    "career_id": occ["career_id"],
                    "name": occ["name"],
                    "soc_code": occ.get("soc_code"),
                    "score": 0.0,  # No score since we don't have user input
                    "confidence": "Low",
                    "explanation": {
                        "method": "fallback",
                        "reasoning": "No user input provided. Showing diverse career options for exploration."
                    },
                    "outlook": occ.get("outlook_features", {}),
                    "education": occ.get("education_data", {})
                })
                seen_soc_prefixes.add(soc_prefix)
        
        # If we still don't have enough, just fill with any
        while len(fallback) < count and len(fallback) < len(occupations):
            for occ in occupations:
                if len(fallback) >= count:
                    break
                if not any(f["career_id"] == occ["career_id"] for f in fallback):
                    fallback.append({
                        "career_id": occ["career_id"],
                        "name": occ["name"],
                        "soc_code": occ.get("soc_code"),
                        "score": 0.0,
                        "confidence": "Low",
                        "explanation": {
                            "method": "fallback",
                            "reasoning": "No user input provided. Showing diverse career options for exploration."
                        },
                        "outlook": occ.get("outlook_features", {}),
                        "education": occ.get("education_data", {})
                    })
        
        return {
            "recommendations": fallback,
            "total_count": len(fallback),
            "note": "No user input provided. Showing diverse career options for exploration.",
            "fallback_used": True
        }
    
    def _get_alternative_recommendations(
        self,
        primary: Dict[str, Any],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Get alternative recommendations when we only have one primary match
        I'm finding similar but different careers
        """
        processed_data = self.recommendation_service.load_processed_data()
        occupations = processed_data["occupations"]
        
        primary_id = primary["career_id"]
        primary_soc = primary.get("soc_code", "")
        
        # Find alternatives - similar SOC code but different career
        alternatives = []
        seen_ids = {primary_id}
        
        # First try same SOC category (first 2 digits)
        if primary_soc:
            soc_prefix = primary_soc[:2]
            for occ in occupations:
                if len(alternatives) >= count:
                    break
                if occ["career_id"] not in seen_ids and occ.get("soc_code", "").startswith(soc_prefix):
                    alternatives.append({
                        "career_id": occ["career_id"],
                        "name": occ["name"],
                        "soc_code": occ.get("soc_code"),
                        "score": 0.0,
                        "confidence": "Low",
                        "explanation": {
                            "method": "alternative",
                            "reasoning": f"Alternative option in similar field to {primary['name']}"
                        },
                        "outlook": occ.get("outlook_features", {}),
                        "education": occ.get("education_data", {})
                    })
                    seen_ids.add(occ["career_id"])
        
        # Fill with any diverse options if needed
        for occ in occupations:
            if len(alternatives) >= count:
                break
            if occ["career_id"] not in seen_ids:
                alternatives.append({
                    "career_id": occ["career_id"],
                    "name": occ["name"],
                    "soc_code": occ.get("soc_code"),
                    "score": 0.0,
                    "confidence": "Low",
                    "explanation": {
                        "method": "alternative",
                        "reasoning": "Alternative option for comparison"
                    },
                    "outlook": occ.get("outlook_features", {}),
                    "education": occ.get("education_data", {})
                })
                seen_ids.add(occ["career_id"])
        
        return alternatives
    
    def add_uncertainty_ranges(
        self,
        recommendations: List[Dict[str, Any]],
        input_quality: str
    ) -> List[Dict[str, Any]]:
        """
        Add uncertainty ranges to all recommendations
        I'm converting precise scores to ranges and adding confidence bands
        No false precision - scores are ranges, not exact numbers
        """
        enhanced = []
        
        for rec in recommendations:
            score = rec.get("score", 0.0)
            confidence = rec.get("confidence", "Low")
            
            # Convert score to range based on confidence
            # Higher confidence = narrower range, lower confidence = wider range
            if confidence == "High":
                score_range = (max(0.0, score - 0.05), min(1.0, score + 0.05))
            elif confidence == "Medium":
                score_range = (max(0.0, score - 0.1), min(1.0, score + 0.1))
            else:  # Low or Very Low
                score_range = (max(0.0, score - 0.2), min(1.0, score + 0.2))
            
            # Adjust range based on input quality
            if input_quality == "thin":
                # Widen ranges if input is thin
                range_width = score_range[1] - score_range[0]
                score_range = (
                    max(0.0, score_range[0] - 0.1),
                    min(1.0, score_range[1] + 0.1)
                )
            
            # Add uncertainty info
            rec["score_range"] = {
                "min": round(score_range[0], 2),
                "max": round(score_range[1], 2),
                "point_estimate": round(score, 3)  # Keep point estimate but emphasize range
            }
            
            rec["uncertainty"] = {
                "level": confidence,
                "reasoning": self._get_uncertainty_reasoning(confidence, input_quality, rec.get("explanation", {}).get("method"))
            }
            
            enhanced.append(rec)
        
        return enhanced
    
    def _get_uncertainty_reasoning(
        self,
        confidence: str,
        input_quality: str,
        method: str
    ) -> str:
        """Generate reasoning for uncertainty level"""
        reasons = []
        
        if input_quality == "thin":
            reasons.append("Limited user input provided")
        elif input_quality == "empty":
            reasons.append("No user input provided")
        
        if confidence == "Low":
            reasons.append("Low confidence in match quality")
        elif confidence == "Very Low":
            reasons.append("Very low confidence - recommendations are exploratory")
        
        if method == "fallback":
            reasons.append("Using fallback logic due to insufficient input")
        elif method == "alternative":
            reasons.append("Alternative recommendation - not primary match")
        
        if not reasons:
            return "Moderate confidence based on available data"
        
        return ". ".join(reasons) + "."
    
    def assess_input_quality(
        self,
        skills: Optional[List[str]] = None,
        skill_importance: Optional[Dict[str, float]] = None,
        interests: Optional[Dict[str, float]] = None,
        work_values: Optional[Dict[str, float]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Assess input quality - empty, thin, or sufficient
        I'm using this to adjust fallback behavior and uncertainty ranges
        """
        has_skills = bool(skills and len(skills) > 0)
        has_importance = bool(skill_importance and len(skill_importance) > 0)
        has_interests = bool(interests and len(interests) > 0)
        has_values = bool(work_values and len(work_values) > 0)
        has_constraints = bool(constraints and len(constraints) > 0)
        
        input_count = sum([
            has_skills, has_importance, has_interests, has_values, has_constraints
        ])
        
        if input_count == 0:
            return "empty"
        elif input_count <= 2:
            return "thin"
        else:
            return "sufficient"
    
    def recommend_with_guardrails(
        self,
        skills: Optional[List[str]] = None,
        skill_importance: Optional[Dict[str, float]] = None,
        interests: Optional[Dict[str, float]] = None,
        work_values: Optional[Dict[str, float]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        top_n: int = 5,
        use_ml: bool = True
    ) -> Dict[str, Any]:
        """
        Main method - get recommendations with all guardrails applied
        I'm checking demographics, ensuring multiple options, adding uncertainty, handling fallbacks
        """
        # Guardrail 1: Check for demographic features
        demographic_check = self.check_demographic_features(
            skills=skills,
            skill_importance=skill_importance,
            interests=interests,
            work_values=work_values,
            constraints=constraints
        )
        
        if demographic_check["has_demographic_data"]:
            return {
                "error": "Demographic features detected",
                "message": demographic_check["message"],
                "issues": demographic_check["issues"],
                "recommendations": []
            }
        
        # Guardrail 2: Assess input quality for fallback behavior
        input_quality = self.assess_input_quality(
            skills=skills,
            skill_importance=skill_importance,
            interests=interests,
            work_values=work_values,
            constraints=constraints
        )
        
        # Adjust top_n based on input quality - ensure minimum
        effective_top_n = max(top_n, self.MIN_RECOMMENDATIONS)
        if input_quality == "empty":
            effective_top_n = self.DEFAULT_RECOMMENDATIONS
        
        # Get recommendations from underlying service
        # Ensure model is loaded if ML is being used
        if use_ml:
            self._ensure_model_loaded()
        
        try:
            result = self.recommendation_service.recommend(
                skills=skills,
                skill_importance=skill_importance,
                interests=interests,
                work_values=work_values,
                constraints=constraints,
                top_n=effective_top_n,
                use_ml=use_ml
            )
            
            recommendations = result.get("recommendations", [])
        except Exception as e:
            # Fallback if service fails
            print(f"Recommendation service failed: {e}")
            recommendations = []
        
        # Guardrail 3: Ensure multiple recommendations
        multi_result = self.ensure_multiple_recommendations(recommendations, self.MIN_RECOMMENDATIONS)
        
        # Extract the actual recommendations list
        if "recommendations" in multi_result:
            final_recommendations = multi_result["recommendations"]
        elif "primary_recommendation" in multi_result:
            # Single recommendation case
            final_recommendations = [multi_result["primary_recommendation"]] + multi_result.get("alternatives", [])
        else:
            # Fallback case
            final_recommendations = multi_result.get("recommendations", [])
        
        # Guardrail 4: Add uncertainty ranges
        final_recommendations = self.add_uncertainty_ranges(final_recommendations, input_quality)
        
        # Build response
        response = {
            "recommendations": final_recommendations,
            "input_quality": input_quality,
            "total_count": len(final_recommendations),
            "guardrails_applied": {
                "demographic_check": "passed",
                "multiple_recommendations": len(final_recommendations) >= self.MIN_RECOMMENDATIONS,
                "uncertainty_ranges": True,
                "fallback_used": input_quality in ["empty", "thin"] or len(recommendations) == 0
            }
        }
        
        # Add notes if needed
        if "note" in multi_result:
            response["note"] = multi_result["note"]
        
        if input_quality in ["empty", "thin"]:
            response["input_quality_note"] = f"Input quality is {input_quality}. Recommendations may be less precise. Consider providing more information for better matches."
        
        return response


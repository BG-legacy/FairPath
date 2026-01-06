"""
ML-based career recommendation service
I'm building a recommendation system that matches user skills/interests/values to careers
Uses both baseline similarity and trained ML models for ranking
"""
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import joblib

from services.data_processing import DataProcessingService
from services.openai_enhancement import OpenAIEnhancementService
from services.skill_expansion_service import SkillExpansionService
from services.career_generation_service import CareerGenerationService


class CareerRecommendationService:
    """
    Main recommendation service - handles feature engineering, ranking, and explainability
    I'm keeping this pretty straightforward - baseline similarity plus a simple ML model
    """
    
    def __init__(self, artifacts_dir: Optional[Path] = None):
        self.artifacts_dir = artifacts_dir or Path(__file__).parent.parent / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)
        
        # Model artifacts - will load these if they exist
        self.skill_vectorizer = None
        self.scaler = None
        self.ml_model = None
        self.model_version = None
        
        # Processed data cache
        self._processed_data = None
        self._occupation_vectors = None
        
        # OpenAI enhancement (optional)
        self.openai_service = OpenAIEnhancementService()
        
        # Skill expansion service (uses OpenAI to map user skills to O*NET taxonomy)
        self.skill_expansion_service = SkillExpansionService()
        
        # Career generation service (uses OpenAI to suggest careers beyond O*NET)
        self.career_generation_service = CareerGenerationService()
        
        # RIASEC interest categories - using these for matching
        self.riasec_categories = [
            "Realistic", "Investigative", "Artistic", 
            "Social", "Enterprising", "Conventional"
        ]
        
        # Work values categories
        self.work_values = [
            "Achievement", "Working Conditions", "Recognition",
            "Relationships", "Support", "Independence"
        ]
    
    def load_processed_data(self) -> Dict[str, Any]:
        """Load the processed occupation data - caching it so I don't reload constantly"""
        if self._processed_data is None:
            processing_service = DataProcessingService()
            self._processed_data = processing_service.load_processed_data()
            if not self._processed_data:
                raise ValueError("Processed data not found. Run process_data.py first.")
        return self._processed_data
    
    def build_user_feature_vector(
        self,
        skills: Optional[List[str]] = None,
        skill_importance: Optional[Dict[str, float]] = None,
        interests: Optional[Dict[str, float]] = None,
        work_values: Optional[Dict[str, float]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        use_openai_expansion: bool = True
    ) -> Dict[str, Any]:
        """
        Convert user inputs into a feature vector that matches occupation vectors
        This is my feature pipeline - taking various inputs and making them comparable
        
        Args:
            skills: List of skill names the user has/wants
            skill_importance: Dict mapping skill names to importance scores (0-5)
            interests: Dict mapping RIASEC categories to scores (0-7)
            work_values: Dict mapping work value names to scores (0-7)
            constraints: Dict with constraints like min_wage, education_level, etc.
        """
        processed_data = self.load_processed_data()
        all_skills = processed_data["skill_names"]
        
        # Start with skill vector - similar to how occupations have skill vectors
        skill_vector = np.zeros(len(all_skills))
        
        if skills:
            # If user provides skills, mark them as important
            # Build lookup with normalized skill names
            skill_lookup = {s.lower(): i for i, s in enumerate(all_skills)}
            
            # Try OpenAI skill expansion first (if available)
            openai_expansions = {}
            if use_openai_expansion and self.skill_expansion_service.openai_service.is_available():
                try:
                    print(f"Using OpenAI to expand {len(skills)} skills...")
                    openai_expansions = self.skill_expansion_service.expand_user_skills(
                        skills, 
                        all_skills,
                        use_cache=True
                    )
                    print(f"OpenAI expanded skills successfully")
                except Exception as e:
                    print(f"OpenAI skill expansion failed, using fallback: {e}")
            
            # Enhanced skill matching - match multiple O*NET skills per user skill
            for skill in skills:
                skill_lower = skill.lower()
                matched_any = False
                importance = skill_importance.get(skill, 3.0) if skill_importance else 3.0
                
                # First, check if we have OpenAI expansion for this skill
                if skill in openai_expansions and openai_expansions[skill]:
                    # Use OpenAI-generated mappings with confidence weights
                    for onet_skill, confidence in openai_expansions[skill].items():
                        if onet_skill.lower() in skill_lookup:
                            idx = skill_lookup[onet_skill.lower()]
                            # Apply weighted importance based on OpenAI confidence
                            weighted_importance = (importance / 5.0) * confidence
                            skill_vector[idx] = max(skill_vector[idx], weighted_importance)
                            matched_any = True
                    
                    if matched_any:
                        continue  # Skip fallback matching if OpenAI succeeded
                
                # Fallback: Direct match (exact or substring)
                for skill_name, idx in skill_lookup.items():
                    if skill_lower in skill_name or skill_name in skill_lower:
                        # Don't overwrite if already set - take max value
                        skill_vector[idx] = max(skill_vector[idx], importance / 5.0)
                        matched_any = True
                        # Don't break - keep matching more skills
                
                # Enhanced matching for common programming/tech skills
                if not matched_any:
                    # Map common tech terms to O*NET skills
                    tech_mappings = {
                        'python': ['programming', 'systems analysis', 'technology design'],
                        'javascript': ['programming', 'systems analysis', 'technology design'],
                        'java': ['programming', 'systems analysis'],
                        'programming': ['programming', 'systems analysis'],
                        'software': ['programming', 'systems analysis', 'quality control analysis'],
                        'data': ['systems analysis', 'mathematics', 'complex problem solving'],
                        'project': ['management of personnel resources', 'time management', 'coordination'],
                        'management': ['management of personnel resources', 'time management', 'coordination'],
                        'communication': ['speaking', 'active listening', 'writing'],
                        'analysis': ['systems analysis', 'critical thinking', 'complex problem solving'],
                        'design': ['technology design', 'operations analysis'],
                    }
                    
                    # Check if this skill maps to known O*NET skills
                    for keyword, onet_skills in tech_mappings.items():
                        if keyword in skill_lower:
                            importance = skill_importance.get(skill, 3.0) if skill_importance else 3.0
                            for onet_skill in onet_skills:
                                if onet_skill in skill_lookup:
                                    idx = skill_lookup[onet_skill]
                                    # Apply with slightly reduced weight since it's a mapping
                                    skill_vector[idx] = max(skill_vector[idx], (importance * 0.8) / 5.0)
                            matched_any = True
                            break
        
        # Add interest vector (RIASEC)
        interest_vector = np.zeros(len(self.riasec_categories))
        if interests:
            for i, category in enumerate(self.riasec_categories):
                if category in interests:
                    interest_vector[i] = interests[category] / 7.0  # Normalize 0-7 to 0-1
        
        # Add work values vector
        values_vector = np.zeros(len(self.work_values))
        if work_values:
            for i, value in enumerate(self.work_values):
                if value in work_values:
                    values_vector[i] = work_values[value] / 7.0
        
        # Constraint features - encoding these as simple scalars
        constraint_features = np.array([
            constraints.get("min_wage", 0) / 200000.0 if constraints else 0.0,  # Normalize wage
            1.0 if constraints and constraints.get("remote_preferred", False) else 0.0,
            constraints.get("max_education_level", 5) / 5.0 if constraints else 1.0,  # 0=high school, 5=doctoral
        ])
        
        # Combine everything into one big vector
        combined_vector = np.concatenate([
            skill_vector,
            interest_vector,
            values_vector,
            constraint_features
        ])
        
        return {
            "combined_vector": combined_vector.tolist(),
            "skill_vector": skill_vector.tolist(),
            "interest_vector": interest_vector.tolist(),
            "values_vector": values_vector.tolist(),
            "constraint_features": constraint_features.tolist(),
            "skill_names": all_skills
        }
    
    def build_occupation_vectors(self) -> Dict[str, np.ndarray]:
        """
        Build feature vectors for all occupations
        I'm doing this once and caching it since it doesn't change
        """
        if self._occupation_vectors is not None:
            return self._occupation_vectors
        
        processed_data = self.load_processed_data()
        all_skills = processed_data["skill_names"]
        
        vectors = {}
        
        for occ_data in processed_data["occupations"]:
            career_id = occ_data["career_id"]
            
            # Get skill vector
            skill_vec = np.array(occ_data["skill_vector"]["combined"])
            
            # For now I'm setting interest/values to zeros since we don't have them in processed data
            # In a real system I'd load these from the raw O*NET data
            # But for now I'll just use skills + outlook features
            interest_vec = np.zeros(len(self.riasec_categories))
            values_vec = np.zeros(len(self.work_values))
            
            # Add outlook features as constraints-like features
            outlook = occ_data.get("outlook_features", {})
            constraint_features = np.array([
                (outlook.get("median_wage_2024", 0) or 0) / 200000.0,
                0.0,  # remote_preferred - not in data
                self._education_level_to_float(occ_data.get("education_data", {}).get("education_level")) / 5.0
            ])
            
            combined = np.concatenate([
                skill_vec,
                interest_vec,
                values_vec,
                constraint_features
            ])
            
            vectors[career_id] = combined
        
        self._occupation_vectors = vectors
        return vectors
    
    def _education_level_to_float(self, level: Optional[str]) -> float:
        """Convert education level string to numeric (0-5)"""
        if not level:
            return 2.5  # Default to bachelor's level
        mapping = {
            "high_school": 0.0,
            "some_college": 1.0,
            "associates": 2.0,
            "bachelors": 3.0,
            "masters": 4.0,
            "professional": 4.5,
            "doctoral": 5.0
        }
        return mapping.get(level, 2.5)
    
    def baseline_rank(
        self,
        user_vector: np.ndarray,
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Baseline ranking using cosine similarity
        Simple but effective - just comparing vectors
        """
        occupation_vectors = self.build_occupation_vectors()
        processed_data = self.load_processed_data()
        
        similarities = []
        
        for career_id, occ_vector in occupation_vectors.items():
            # Cosine similarity between user and occupation
            similarity = cosine_similarity(
                user_vector.reshape(1, -1),
                occ_vector.reshape(1, -1)
            )[0][0]
            similarities.append((career_id, float(similarity)))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Normalize scores to 0-1 range using min-max scaling on top_n
        # With improved skill matching, we should get better raw scores
        top_similarities = similarities[:top_n]
        if len(top_similarities) > 0:
            max_sim = top_similarities[0][1]
            min_sim = top_similarities[-1][1] if len(top_similarities) > 1 else 0.0
            
            # Apply min-max normalization with better ranges
            if max_sim > min_sim:
                # Scale raw scores first if they're very low (< 0.2)
                if max_sim < 0.2:
                    print(f"Baseline scores are low (max: {max_sim:.4f}), applying scaling")
                    normalized = [
                        (career_id, 0.5 + 0.5 * (score - min_sim) / (max_sim - min_sim))
                        for career_id, score in top_similarities
                    ]
                else:
                    # Good scores - apply lighter normalization
                    normalized = [
                        (career_id, 0.6 + 0.4 * (score - min_sim) / (max_sim - min_sim))
                        for career_id, score in top_similarities
                    ]
                return normalized
            else:
                # All scores are the same, give them mid-range scores
                return [(career_id, 0.6) for career_id, _ in top_similarities]
        
        return top_similarities
    
    def ml_rank(
        self,
        user_vector: np.ndarray,
        top_n: int = 5,
        use_model: bool = True
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        ML-based ranking - uses trained model if available, falls back to baseline
        Returns list of (career_id, score, explanation_dict)
        """
        if not use_model or self.ml_model is None:
            # Fall back to baseline if no model
            baseline_results = self.baseline_rank(user_vector, top_n)
            return [
                (career_id, score, {"method": "baseline", "confidence": self._score_to_confidence(score)})
                for career_id, score in baseline_results
            ]
        
        occupation_vectors = self.build_occupation_vectors()
        processed_data = self.load_processed_data()
        
        scores = []
        
        for career_id, occ_vector in occupation_vectors.items():
            # Build feature vector same way we did in training: (user, career, diff)
            # Don't scale individual vectors - scale the combined feature vector
            feature_combined = np.concatenate([
                user_vector,
                occ_vector,
                user_vector - occ_vector
            ])
            
            # Scale the combined feature vector if we have a scaler
            if self.scaler:
                feature_combined = self.scaler.transform(feature_combined.reshape(1, -1))[0]
            
            # Get prediction from model
            try:
                feature_reshaped = feature_combined.reshape(1, -1)
                if hasattr(self.ml_model, 'predict_proba'):
                    # Use probability of positive class as score
                    proba = self.ml_model.predict_proba(feature_reshaped)[0]
                    score = proba[1] if len(proba) > 1 else proba[0]
                else:
                    # Use raw prediction
                    score = self.ml_model.predict(feature_reshaped)[0]
                    # If output is binary, convert to probability-like score
                    if score <= 1.0:
                        score = float(score)
                    else:
                        # Normalize if needed
                        score = min(max(float(score) / 10.0, 0.0), 1.0)
            except Exception as e:
                # Fallback to cosine similarity if model fails
                print(f"Model prediction failed for {career_id}, using baseline: {e}")
                score = float(cosine_similarity(user_vector.reshape(1, -1), occ_vector.reshape(1, -1))[0][0])
            
            # Get explainability info
            explanation = self._explain_prediction(user_vector, occ_vector, career_id, processed_data)
            explanation["method"] = "ml_model"
            explanation["confidence"] = self._score_to_confidence(score)
            
            scores.append((career_id, score, explanation))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Normalize scores to ensure they're meaningful
        # ML models can produce very low probabilities that round to 0.00
        top_scores = scores[:top_n]
        if len(top_scores) > 0:
            max_score = top_scores[0][1]
            min_score = top_scores[-1][1] if len(top_scores) > 1 else 0.0
            
            # Apply normalization based on score range
            if max_score < 0.3:
                # Very low scores - likely sparse matching
                print(f"ML scores are low (max: {max_score:.6f}), applying strong normalization")
                if max_score > min_score:
                    normalized = [
                        (career_id, 0.5 + 0.5 * (score - min_score) / (max_score - min_score), explanation)
                        for career_id, score, explanation in top_scores
                    ]
                    return normalized
                else:
                    # All scores identical, give mid-range
                    return [(career_id, 0.55, explanation) for career_id, _, explanation in top_scores]
            elif max_score < 0.7:
                # Moderate scores - light normalization
                print(f"ML scores are moderate (max: {max_score:.6f}), applying light normalization")
                if max_score > min_score:
                    normalized = [
                        (career_id, 0.6 + 0.4 * (score - min_score) / (max_score - min_score), explanation)
                        for career_id, score, explanation in top_scores
                    ]
                    return normalized
        
        # Good scores or no normalization needed
        return top_scores
    
    def _explain_prediction(
        self,
        user_vector: np.ndarray,
        occ_vector: np.ndarray,
        career_id: str,
        processed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate explanation for why this career was recommended
        I'm finding the top contributing features (skills mostly)
        """
        all_skills = processed_data["skill_names"]
        num_skills = len(all_skills)
        
        # Get skill portions of vectors
        user_skills = user_vector[:num_skills]
        occ_skills = occ_vector[:num_skills]
        
        # Find skills where both user and occupation have high values
        contributing_skills = []
        for i, skill_name in enumerate(all_skills):
            user_val = user_skills[i]
            occ_val = occ_skills[i]
            # Contribution is product of user interest and occupation requirement
            contribution = user_val * occ_val
            if contribution > 0.1:  # Threshold to filter noise
                contributing_skills.append({
                    "skill": skill_name,
                    "user_value": float(user_val),
                    "occupation_value": float(occ_val),
                    "contribution": float(contribution)
                })
        
        # Sort by contribution
        contributing_skills.sort(key=lambda x: x["contribution"], reverse=True)
        top_skills = contributing_skills[:5]  # Top 5 contributing skills
        
        # Build "why" text inputs - these can be polished by OpenAI later
        why_points = []
        for skill_info in top_skills:
            if skill_info["user_value"] > 0.3:
                why_points.append(f"Your skill in {skill_info['skill']} aligns with this career's requirements")
        
        return {
            "top_contributing_skills": top_skills,
            "why_points": why_points,
            "similarity_breakdown": {
                "skill_similarity": float(cosine_similarity(
                    user_skills.reshape(1, -1),
                    occ_skills.reshape(1, -1)
                )[0][0])
            }
        }
    
    def _score_to_confidence(self, score: float) -> str:
        """Convert numeric score to confidence band"""
        if score >= 0.8:
            return "High"
        elif score >= 0.6:
            return "Med"
        elif score >= 0.4:
            return "Low"
        else:
            return "Very Low"
    
    def recommend(
        self,
        skills: Optional[List[str]] = None,
        skill_importance: Optional[Dict[str, float]] = None,
        interests: Optional[Dict[str, float]] = None,
        work_values: Optional[Dict[str, float]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        top_n: int = 5,
        use_ml: bool = True,
        use_openai: bool = True
    ) -> Dict[str, Any]:
        """
        Main recommendation method - returns top N careers with explanations
        """
        # Build user feature vector
        user_features = self.build_user_feature_vector(
            skills=skills,
            skill_importance=skill_importance,
            interests=interests,
            work_values=work_values,
            constraints=constraints
        )
        user_vector = np.array(user_features["combined_vector"])
        
        # Get rankings
        if use_ml:
            ranked_careers = self.ml_rank(user_vector, top_n=top_n, use_model=True)
        else:
            baseline_results = self.baseline_rank(user_vector, top_n=top_n)
            ranked_careers = [
                (career_id, score, {
                    "method": "baseline",
                    "confidence": self._score_to_confidence(score),
                    "top_contributing_skills": [],
                    "why_points": []
                })
                for career_id, score in baseline_results
            ]
        
        # Get full occupation data for recommendations
        processed_data = self.load_processed_data()
        recommendations = []
        
        for career_id, score, explanation in ranked_careers:
            occ_data = next(
                (occ for occ in processed_data["occupations"] if occ["career_id"] == career_id),
                None
            )
            if not occ_data:
                continue
            
            rec = {
                "career_id": career_id,
                "name": occ_data["name"],
                "soc_code": occ_data["soc_code"],
                "score": score,
                "confidence": explanation["confidence"],  # Confidence band (Low/Med/High)
                "explanation": explanation,
                "outlook": occ_data.get("outlook_features", {}),
                "education": occ_data.get("education_data", {})
            }
            
            # Add OpenAI enhancement if available
            if use_openai and self.openai_service.is_available():
                enhanced = self.openai_service.enhance_recommendation_explanation(
                    career_name=occ_data["name"],
                    user_skills=skills or [],
                    user_interests=interests,
                    match_score=score,
                    top_skills=explanation.get("top_contributing_skills", [])
                )
                rec["openai_enhancement"] = enhanced
            
            recommendations.append(rec)
        
        # Optionally refine ranking with OpenAI (graceful fallback - always returns ML outputs even if OpenAI fails)
        if use_openai and self.openai_service.is_available() and len(recommendations) > 0:
            try:
                user_profile = {
                    "skills": skills or [],
                    "interests": interests or {},
                    "values": work_values or {},
                    "constraints": constraints or {}
                }
                # refine_recommendations returns original recommendations if it fails
                recommendations = self.openai_service.refine_recommendations(
                    recommendations, user_profile
                )
                
                # Get additional career suggestions from OpenAI (returns [] if it fails)
                all_careers_data = [
                    {
                        "career_id": occ["career_id"],
                        "name": occ["name"],
                        "soc_code": occ["soc_code"],
                        "outlook_features": occ.get("outlook_features", {}),
                        "education_data": occ.get("education_data", {})
                    }
                    for occ in processed_data["occupations"]
                ]
                
                openai_suggestions = self.openai_service.suggest_additional_careers(
                    user_profile=user_profile,
                    existing_recommendations=recommendations,
                    all_careers=all_careers_data
                )
                
                # Add OpenAI suggestions if they're not already in recommendations
                existing_ids = {r["career_id"] for r in recommendations}
                for suggestion in openai_suggestions:
                    if suggestion["career_id"] not in existing_ids:
                        # Enhance the suggestion with OpenAI explanation (graceful fallback - returns None if fails)
                        enhanced = self.openai_service.enhance_recommendation_explanation(
                            career_name=suggestion["name"],
                            user_skills=skills or [],
                            user_interests=interests,
                            match_score=suggestion["score"],
                            top_skills=[]
                        )
                        suggestion["openai_enhancement"] = enhanced
                        recommendations.append(suggestion)
            except Exception as e:
                # Graceful fallback - if OpenAI fails, still return ML outputs with raw "why" bullets
                print(f"OpenAI refinement/suggestions failed, using ML outputs only: {e}")
                # recommendations already contains ML outputs, so just continue
        
        return {
            "recommendations": recommendations,
            "user_features": {
                "num_skills_provided": len(skills) if skills else 0,
                "interests_provided": bool(interests),
                "values_provided": bool(work_values),
                "constraints_provided": bool(constraints)
            },
            "method": "ml_model" if (use_ml and self.ml_model) else "baseline"
        }
    
    def get_enhanced_recommendations(
        self,
        skills: Optional[List[str]] = None,
        skill_importance: Optional[Dict[str, float]] = None,
        interests: Optional[Dict[str, float]] = None,
        work_values: Optional[Dict[str, float]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        use_ml: bool = True,
        use_openai: bool = True
    ) -> Dict[str, Any]:
        """
        Get enhanced recommendations with confidence bands, explainability, alternatives, and why narrative
        Returns 3-5 careers
        
        If ML matches are not good enough (top score < 0.5), uses OpenAI to generate recommendations
        """
        # Get base recommendations - request more to have alternatives
        base_result = self.recommend(
            skills=skills,
            skill_importance=skill_importance,
            interests=interests,
            work_values=work_values,
            constraints=constraints,
            top_n=8,  # Get more for alternatives
            use_ml=use_ml,
            use_openai=False  # Don't use OpenAI enhancement here, we'll check quality first
        )
        
        all_recommendations = base_result["recommendations"]
        
        # Universal career detection - works for ALL fields (tech, medical, business, creative, etc.)
        # Detect if match quality is poor or if there's a skill-career mismatch
        use_openai_supplement = False
        if len(all_recommendations) > 0 and skills:
            top_recommendation = all_recommendations[0]
            top_name = top_recommendation.get("name", "").lower()
            top_score = top_recommendation.get("score", 0.0)
            
            print(f"Top recommendation: {top_recommendation.get('name')}, Score: {top_score:.4f}")
            
            # Strategy 1: If top score isn't high enough, get better options
            if top_score < 0.90:
                use_openai_supplement = True
                print(f"Top match score is not high enough ({top_score:.2f}) - supplementing with OpenAI for better careers")
            
            # Strategy 2: Detect professional/specialized skills vs generic/technician matches
            # This catches cases where user has specialized skills but got generic roles
            has_professional_skills = any(
                any(keyword in skill.lower() for keyword in [
                    # Tech & IT
                    'programming', 'software', 'developer', 'python', 'javascript', 'java',
                    'web', 'react', 'node', 'database', 'data', 'ml', 'ai', 'cloud', 'devops',
                    # Medical & Healthcare
                    'medical', 'clinical', 'healthcare', 'nursing', 'patient', 'laboratory',
                    'diagnostic', 'surgical', 'pharmacy', 'therapeutic', 'research',
                    # Business & Finance
                    'management', 'marketing', 'sales', 'finance', 'accounting', 'consulting',
                    'business', 'strategy', 'analytics', 'economics', 'investment',
                    # Science & Research
                    'research', 'scientific', 'analysis', 'laboratory', 'statistics',
                    'biology', 'chemistry', 'physics', 'engineering',
                    # Creative & Design
                    'design', 'graphics', 'art', 'creative', 'ux', 'ui', 'branding',
                    'writing', 'editing', 'content', 'media', 'photography',
                    # Education & Social Services
                    'teaching', 'education', 'curriculum', 'counseling', 'social work',
                    # Legal & Policy
                    'legal', 'law', 'compliance', 'policy', 'regulatory'
                ])
                for skill in skills
            )
            
            is_generic_technician = any(
                word in top_name
                for word in ['technician', 'technologist', 'operator', 'inspector', 
                           'production manager', 'industrial production', 'manufacturing',
                           'mechanical', 'assembler', 'fabricator']
            )
            
            if has_professional_skills and is_generic_technician:
                use_openai_supplement = True
                print(f"User has professional/specialized skills but top match is generic/technician role - supplementing with OpenAI")
            
            # Strategy 3: User has multiple specific skills (3+ words) but got very generic match
            specific_skills = [s for s in skills if len(s.split()) >= 2]  # Multi-word skills are more specific
            if len(specific_skills) >= 2 and top_score < 0.95:
                use_openai_supplement = True
                print(f"User has specific multi-word skills but match isn't excellent - supplementing with OpenAI")
        
        # If we need to supplement with OpenAI-generated careers
        if use_openai_supplement and use_openai and self.career_generation_service.openai_service.is_available():
            try:
                user_profile = {
                    "skills": skills or [],
                    "interests": interests or {},
                    "values": work_values or {},
                    "constraints": constraints or {}
                }
                
                # Generate careers using OpenAI (can suggest careers not in O*NET)
                print("Generating career recommendations with OpenAI...")
                openai_careers = self.career_generation_service.generate_career_recommendations(
                    user_profile=user_profile,
                    num_recommendations=5
                )
                
                if openai_careers:
                    # Merge OpenAI careers with O*NET careers, prioritize by score
                    # Pass user skills so merge can filter out nonsensical O*NET matches
                    merged = self.career_generation_service.merge_with_onet_careers(
                        openai_careers=openai_careers,
                        onet_careers=all_recommendations,
                        max_total=8,
                        user_skills=skills
                    )
                    all_recommendations = merged["primary"] + merged["alternatives"]
                    base_result["method"] = "hybrid_ml_openai"
                    print(f"Merged {len(openai_careers)} OpenAI careers with O*NET careers")
            except Exception as e:
                print(f"OpenAI career generation failed, using ML recommendations: {e}")
                # Continue with ML recommendations if OpenAI fails
        
        # Take top 3-5 as primary recommendations
        primary_count = min(max(3, len(all_recommendations)), 5)
        primary_recommendations = all_recommendations[:primary_count]
        
        # Only include alternatives if they meet HIGH quality threshold
        # Filter out low-scoring alternatives (< 0.80) or generic/irrelevant careers
        alternatives = []
        if len(all_recommendations) > primary_count:
            potential_alternatives = all_recommendations[primary_count:primary_count + 3]
            for alt in potential_alternatives:
                # Only include if score is high (≥ 0.80) and not a generic/mismatched role
                if alt.get("score", 0) >= 0.80:
                    career_name = alt.get("name", "").lower()
                    # Skip generic/technical roles that are likely mismatches
                    is_generic_or_mismatch = any(
                        word in career_name
                        for word in ['technician', 'technologist', 'operator', 
                                   'production', 'manufacturing', 'inspector',
                                   'assembler', 'fabricator', 'surveyor',
                                   'network', 'systems administrator', 'computer systems',
                                   'mechanical', 'electrical', 'industrial',
                                   'nuclear', 'aerospace', 'automotive']
                    )
                    if not is_generic_or_mismatch:
                        alternatives.append(alt)
        
        # Enhance each recommendation with confidence bands and formatted explainability
        enhanced_primary = []
        for rec in primary_recommendations:
            # Add OpenAI enhancement for explanations BEFORE formatting
            # This allows _build_why_narrative to use the OpenAI content
            if use_openai and self.openai_service.is_available() and not rec.get("openai_generated"):
                try:
                    enhanced_explanation = self.openai_service.enhance_recommendation_explanation(
                        career_name=rec.get("name", ""),
                        user_skills=skills or [],
                        user_interests=interests,
                        match_score=rec.get("score", 0.0),
                        top_skills=rec.get("explanation", {}).get("top_contributing_skills", [])
                    )
                    if enhanced_explanation.get("why_this_career") or enhanced_explanation.get("enhanced_explanation"):
                        rec["openai_enhancement"] = enhanced_explanation
                except Exception as e:
                    print(f"OpenAI enhancement failed for {rec.get('name')}: {e}")
            
            # Now format the recommendation (this will use the OpenAI enhancement if present)
            enhanced = self._enhance_recommendation_format(rec)
            enhanced_primary.append(enhanced)
        
        enhanced_alternatives = []
        for rec in alternatives:
            enhanced = self._enhance_recommendation_format(rec)
            enhanced_alternatives.append(enhanced)
        
        return {
            "careers": enhanced_primary,
            "alternatives": enhanced_alternatives,
            "method": base_result["method"],
            "user_features": base_result["user_features"]
        }
    
    def _enhance_recommendation_format(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a single recommendation with confidence bands, explainability, and why narrative
        """
        score = rec.get("score", 0.0)
        confidence = rec.get("confidence", "Low")
        explanation = rec.get("explanation", {})
        
        # Add confidence band with score range
        confidence_band = self._get_confidence_band(score, confidence)
        
        # Extract top features from explainability
        top_features = explanation.get("top_contributing_skills", [])
        explainability = {
            "top_features": [
                {
                    "feature": feat.get("skill", ""),
                    "contribution": round(feat.get("contribution", 0.0), 3),
                    "user_value": round(feat.get("user_value", 0.0), 3),
                    "career_value": round(feat.get("occupation_value", 0.0), 3)
                }
                for feat in top_features[:5]  # Top 5 features
            ],
            "method": explanation.get("method", "unknown"),
            "similarity_breakdown": explanation.get("similarity_breakdown", {})
        }
        
        # Build "why" narrative
        why_narrative = self._build_why_narrative(rec, explanation, top_features)
        
        # Build enhanced recommendation
        enhanced = {
            "career_id": rec.get("career_id"),
            "name": rec.get("name"),
            "soc_code": rec.get("soc_code"),
            "score": round(score, 3),
            "confidence": confidence,
            "confidence_band": confidence_band,
            "explainability": explainability,
            "why": why_narrative,
            "outlook": rec.get("outlook", {}),
            "education": rec.get("education", {})
        }
        
        # OpenAI enhancement is already incorporated in _build_why_narrative
        # But we can add extra fields if needed
        if "openai_enhancement" in rec:
            openai_enhance = rec["openai_enhancement"]
            # Add any additional OpenAI fields that weren't captured in why narrative
            if openai_enhance.get("next_steps") and isinstance(enhanced.get("why"), dict):
                enhanced["why"]["next_steps"] = openai_enhance.get("next_steps")
        
        return enhanced
    
    def _get_confidence_band(self, score: float, confidence: str) -> Dict[str, Any]:
        """
        Get confidence band with score range
        Returns format compatible with frontend: score_range as [min, max] tuple array
        """
        # Define ranges based on confidence level
        if confidence == "High":
            score_range = (max(0.0, score - 0.05), min(1.0, score + 0.05))
        elif confidence == "Med" or confidence == "Medium":  # Support both for backwards compatibility
            score_range = (max(0.0, score - 0.1), min(1.0, score + 0.1))
        else:  # Low or Very Low
            score_range = (max(0.0, score - 0.15), min(1.0, score + 0.15))
        
        return {
            "level": confidence,
            "score_range": [round(score_range[0], 3), round(score_range[1], 3)]
        }
    
    def _build_why_narrative(self, rec: Dict[str, Any], explanation: Dict[str, Any], top_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build "why" narrative explaining why this career was recommended
        """
        why_points = explanation.get("why_points", [])
        
        # If we have OpenAI enhancement, use that
        if "openai_enhancement" in rec:
            openai_enhance = rec["openai_enhancement"]
            if openai_enhance.get("enhanced_explanation"):
                return {
                    "primary": openai_enhance.get("enhanced_explanation"),
                    "points": why_points,
                    "top_features": [feat.get("skill", "") for feat in top_features[:3]]
                }
        
        # Otherwise build from explainability data
        narrative_parts = []
        if top_features:
            top_skill_names = [feat.get("skill", "") for feat in top_features[:3]]
            if top_skill_names:
                narrative_parts.append(f"Strong alignment in: {', '.join(top_skill_names)}")
        
        if why_points:
            narrative_parts.extend(why_points[:2])  # Take top 2 points
        
        primary_text = ". ".join(narrative_parts) if narrative_parts else "This career matches your profile based on skill and interest alignment."
        
        return {
            "primary": primary_text,
            "points": why_points,
            "top_features": [feat.get("skill", "") for feat in top_features[:3]]
        }
    
    def save_model_artifacts(
        self,
        model,
        vectorizer=None,
        scaler=None,
        version: str = "1.0.0"
    ):
        """
        Save model artifacts to disk
        I'm saving the model, scaler, and vectorizer separately so I can load them later
        """
        model_dir = self.artifacts_dir / "models"
        model_dir.mkdir(exist_ok=True)
        
        # Save model
        model_path = model_dir / f"career_model_v{version}.pkl"
        joblib.dump(model, model_path)
        self.ml_model = model
        
        # Save scaler if provided
        if scaler:
            scaler_path = model_dir / f"scaler_v{version}.pkl"
            joblib.dump(scaler, scaler_path)
            self.scaler = scaler
        
        # Save vectorizer if provided
        if vectorizer:
            vectorizer_path = model_dir / f"vectorizer_v{version}.pkl"
            joblib.dump(vectorizer, vectorizer_path)
            self.skill_vectorizer = vectorizer
        
        # Save metadata
        metadata = {
            "version": version,
            "saved_date": datetime.now().isoformat(),
            "has_scaler": scaler is not None,
            "has_vectorizer": vectorizer is not None
        }
        metadata_path = model_dir / f"model_metadata_v{version}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.model_version = version
        print(f"Saved model artifacts to {model_dir} (version {version})")
    
    def load_model_artifacts(self, version: Optional[str] = None) -> bool:
        """
        Load model artifacts from disk
        Returns True if successful, False otherwise
        """
        model_dir = self.artifacts_dir / "models"
        
        if not model_dir.exists():
            return False
        
        # Find latest version if not specified
        if version is None:
            metadata_files = list(model_dir.glob("model_metadata_v*.json"))
            if not metadata_files:
                return False
            # Extract version from filename and get latest
            versions = []
            for f in metadata_files:
                version_str = f.stem.replace("model_metadata_v", "")
                versions.append((version_str, f))
            versions.sort(key=lambda x: x[0], reverse=True)
            version = versions[0][0]
        
        # Load metadata
        metadata_path = model_dir / f"model_metadata_v{version}.json"
        if not metadata_path.exists():
            return False
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Load model
        model_path = model_dir / f"career_model_v{version}.pkl"
        if not model_path.exists():
            return False
        
        self.ml_model = joblib.load(model_path)
        
        # Load scaler if it exists
        if metadata.get("has_scaler"):
            scaler_path = model_dir / f"scaler_v{version}.pkl"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
        
        # Load vectorizer if it exists
        if metadata.get("has_vectorizer"):
            vectorizer_path = model_dir / f"vectorizer_v{version}.pkl"
            if vectorizer_path.exists():
                self.skill_vectorizer = joblib.load(vectorizer_path)
        
        self.model_version = version
        print(f"Loaded model artifacts (version {version})")
        return True


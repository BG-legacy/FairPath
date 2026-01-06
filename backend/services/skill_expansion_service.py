"""
Skill Expansion Service
Uses OpenAI to map user's specific skills to O*NET skill taxonomy
This dramatically improves matching for modern tech skills
"""
import json
from typing import Dict, List, Optional
from services.openai_enhancement import OpenAIEnhancementService


class SkillExpansionService:
    """
    Expands user skills to O*NET skills using OpenAI
    
    Example:
        User skill: "Python"
        O*NET mappings: {
            "Programming": 0.95,
            "Systems Analysis": 0.75,
            "Technology Design": 0.60
        }
    """
    
    def __init__(self):
        self.openai_service = OpenAIEnhancementService()
        self.cache: Dict[str, Dict[str, float]] = {}
    
    def expand_user_skills(
        self, 
        user_skills: List[str], 
        onet_skills: List[str],
        use_cache: bool = True
    ) -> Dict[str, Dict[str, float]]:
        """
        Expand multiple user skills to O*NET skills with confidence weights
        
        Args:
            user_skills: List of skills provided by user (e.g., ["Python", "React"])
            onet_skills: List of O*NET skill names to map to
            use_cache: Whether to use cached expansions
            
        Returns:
            Dict mapping each user skill to O*NET skills with weights
            {
                "Python": {"Programming": 0.9, "Systems Analysis": 0.7},
                "React": {"Programming": 0.8, "Technology Design": 0.6}
            }
        """
        if not self.openai_service.is_available():
            # Fallback to empty expansion if OpenAI unavailable
            return {skill: {} for skill in user_skills}
        
        expansions = {}
        skills_to_expand = []
        
        # Check cache first
        for skill in user_skills:
            if use_cache and skill.lower() in self.cache:
                expansions[skill] = self.cache[skill.lower()]
            else:
                skills_to_expand.append(skill)
        
        # Expand uncached skills in batch
        if skills_to_expand:
            batch_expansions = self._expand_skills_batch(skills_to_expand, onet_skills)
            for skill, mapping in batch_expansions.items():
                expansions[skill] = mapping
                if use_cache:
                    self.cache[skill.lower()] = mapping
        
        return expansions
    
    def _expand_skills_batch(
        self, 
        user_skills: List[str], 
        onet_skills: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Expand multiple skills in one OpenAI API call (more efficient)
        """
        if not user_skills:
            return {}
        
        # Format O*NET skills for prompt
        onet_skills_text = '\n'.join([f"- {skill}" for skill in onet_skills])
        user_skills_text = ', '.join(user_skills)
        
        prompt = f"""You're a career skills taxonomy expert. Map these user skills to relevant O*NET skills.

User Skills: {user_skills_text}

Available O*NET Skills:
{onet_skills_text}

For EACH user skill, identify which O*NET skills are relevant and assign a confidence score (0.0-1.0).
- 1.0 = Perfect match or primary skill
- 0.7-0.9 = Strong relationship
- 0.5-0.6 = Moderate relationship
- 0.3-0.4 = Weak but relevant relationship
- < 0.3 = Not relevant (don't include)

Return ONLY valid JSON in this EXACT format:
{{
  "user_skill_name": {{
    "onet_skill_name": confidence_score,
    "another_onet_skill": confidence_score
  }},
  "another_user_skill": {{
    "onet_skill_name": confidence_score
  }}
}}

Example:
{{
  "Python": {{
    "Programming": 0.95,
    "Systems Analysis": 0.70,
    "Mathematics": 0.50
  }},
  "Project Management": {{
    "Management of Personnel Resources": 0.85,
    "Time Management": 0.80,
    "Coordination": 0.75
  }}
}}

Return ONLY the JSON, no explanations."""

        try:
            response = self.openai_service._call_with_retry(
                lambda: self.openai_service.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Cheaper and sufficient for this task
                    messages=[
                        {
                            "role": "system", 
                            "content": "You're a career skills expert. Return only valid JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.3,  # Lower temperature for more consistent mappings
                    response_format={"type": "json_object"}
                )
            )
            
            if response is None:
                return {skill: {} for skill in user_skills}
            
            result_text = response.choices[0].message.content.strip()
            expansions = json.loads(result_text)
            
            # Validate and clean results
            cleaned_expansions = {}
            for skill in user_skills:
                if skill in expansions:
                    # Filter out low-confidence mappings and validate skill names
                    valid_mappings = {
                        onet_skill: confidence
                        for onet_skill, confidence in expansions[skill].items()
                        if onet_skill in onet_skills and confidence >= 0.3
                    }
                    cleaned_expansions[skill] = valid_mappings
                else:
                    cleaned_expansions[skill] = {}
            
            return cleaned_expansions
            
        except (json.JSONDecodeError, KeyError, Exception) as e:
            print(f"OpenAI skill expansion failed: {e}")
            return {skill: {} for skill in user_skills}
    
    def expand_single_skill(
        self, 
        user_skill: str, 
        onet_skills: List[str]
    ) -> Dict[str, float]:
        """
        Expand a single skill (convenience method)
        
        Returns:
            Dict of O*NET skills with confidence weights
            {"Programming": 0.9, "Systems Analysis": 0.7}
        """
        result = self.expand_user_skills([user_skill], onet_skills)
        return result.get(user_skill, {})
    
    def clear_cache(self):
        """Clear the expansion cache"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cached_skills": len(self.cache),
            "total_mappings": sum(len(mappings) for mappings in self.cache.values())
        }



"""
Career Generation Service
Uses OpenAI to suggest careers that make sense for user profile
Can suggest modern careers not in O*NET database
"""
import json
from typing import Dict, List, Optional, Any
from services.openai_enhancement import OpenAIEnhancementService


class CareerGenerationService:
    """
    Generate career recommendations using OpenAI
    Can suggest modern careers that may not exist in O*NET
    """
    
    def __init__(self):
        self.openai_service = OpenAIEnhancementService()
    
    def generate_career_recommendations(
        self,
        user_profile: Dict[str, Any],
        num_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Use OpenAI to generate career recommendations from scratch
        Not limited to O*NET database - can suggest ANY career
        
        Args:
            user_profile: {
                "skills": ["Python", "React", ...],
                "interests": {"Investigative": 7.0, ...},
                "values": {"impact": 6.0, ...},
                "constraints": {"min_wage": 80000, ...}
            }
            num_recommendations: Number of careers to generate
            
        Returns:
            List of career recommendations with explanations
        """
        if not self.openai_service.is_available():
            return []
        
        # Build context from user profile
        skills = user_profile.get('skills', [])
        interests = user_profile.get('interests', {})
        values = user_profile.get('values', {})
        constraints = user_profile.get('constraints', {})
        
        skills_text = ', '.join(skills[:10]) if skills else "various skills"
        
        interests_text = ""
        if interests:
            top_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)[:3]
            interests_text = f"\\nInterests (RIASEC): {', '.join([f'{k} ({v:.1f})' for k, v in top_interests])}"
        
        values_text = ""
        if values:
            values_list = [f"{k}: {v:.1f}" for k, v in values.items()]
            values_text = f"\\nWork Values: {', '.join(values_list)}"
        
        constraints_text = ""
        if constraints:
            parts = []
            if constraints.get('min_wage'):
                parts.append(f"Min wage: ${constraints['min_wage']:,.0f}")
            if constraints.get('remote_preferred'):
                parts.append("Remote work preferred")
            if parts:
                constraints_text = f"\\nConstraints: {', '.join(parts)}"
        
        prompt = f"""You're an expert career advisor. Based on this person's profile, recommend {num_recommendations} careers that would be EXCELLENT matches.

User Profile:
Skills: {skills_text}{interests_text}{values_text}{constraints_text}

Recommend careers that:
1. Actually USE these specific skills (e.g., if they know Python, suggest developer/data roles)
2. Match their interest profile
3. Align with their work values
4. Meet their constraints
5. Can be MODERN careers (not limited to traditional O*NET taxonomy)

For each career, provide:
- Job title (be specific - "Frontend Developer" not just "Developer")
- Score (0.0-1.0 based on match quality)
- SOC code if it exists, or "MODERN" for newer roles
- Why it's a good match (2-3 sentences, be specific about skills)

Return ONLY valid JSON:
{{
  "careers": [
    {{
      "name": "Career Title",
      "score": 0.85,
      "soc_code": "15-1252.00",
      "why": "Detailed explanation...",
      "key_skills_used": ["skill1", "skill2"],
      "salary_range": "70k-120k",
      "growth_outlook": "Excellent"
    }}
  ]
}}

Be honest about fit - don't force matches. Prioritize careers that actually USE their technical skills."""

        try:
            response = self.openai_service._call_with_retry(
                lambda: self.openai_service.client.chat.completions.create(
                    model="gpt-4o",  # Use GPT-4o (supports JSON mode, faster, cheaper than GPT-4)
                    messages=[
                        {
                            "role": "system", 
                            "content": "You're an expert career advisor who understands modern tech careers, traditional careers, and emerging roles. Provide honest, specific recommendations. Return ONLY valid JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_completion_tokens=1500,
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
            )
            
            if response is None:
                return []
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            careers = result.get('careers', [])
            
            # Format for our system
            formatted_careers = []
            for career in careers:
                # Extract key skills from the career data
                key_skills = career.get("key_skills_used", [])
                
                # Build top_contributing_skills structure for explainability
                top_contributing_skills = []
                for skill in key_skills[:5]:  # Top 5 skills
                    top_contributing_skills.append({
                        "skill": skill,
                        "user_value": 0.7,  # Estimated - OpenAI determined this is relevant
                        "occupation_value": 0.8,  # Estimated
                        "contribution": 0.56  # 0.7 * 0.8
                    })
                
                formatted_careers.append({
                    "career_id": career.get("soc_code", "AI_GENERATED"),
                    "name": career.get("name", ""),
                    "soc_code": career.get("soc_code", "MODERN"),
                    "score": float(career.get("score", 0.75)),
                    "confidence": self._score_to_confidence(float(career.get("score", 0.75))),
                    "why": career.get("why", ""),
                    "key_skills_used": key_skills,
                    "salary_range": career.get("salary_range", "Varies"),
                    "growth_outlook": career.get("growth_outlook", "Good"),
                    "source": "openai_generated",
                    "explanation": {
                        "method": "openai_career_generation",
                        "confidence": self._score_to_confidence(float(career.get("score", 0.75))),
                        "why_points": [career.get("why", "")],
                        "top_contributing_skills": top_contributing_skills  # Add this!
                    }
                })
            
            return formatted_careers
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"OpenAI career generation failed: {e}")
            return []
    
    def _score_to_confidence(self, score: float) -> str:
        """Convert score to confidence level"""
        if score >= 0.8:
            return "High"
        elif score >= 0.6:
            return "Med"
        elif score >= 0.4:
            return "Low"
        else:
            return "Very Low"
    
    def merge_with_onet_careers(
        self,
        openai_careers: List[Dict[str, Any]],
        onet_careers: List[Dict[str, Any]],
        max_total: int = 8,
        user_skills: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Merge OpenAI-generated careers with O*NET careers
        Filter out nonsensical O*NET matches when OpenAI has better options
        
        Returns:
            {
                "primary": [top 5 careers],
                "alternatives": [next 3 careers]
            }
        """
        # If OpenAI generated good careers (high scores), filter out nonsensical O*NET matches
        filtered_onet_careers = []
        if openai_careers and len(openai_careers) > 0:
            best_openai_score = max(c.get("score", 0) for c in openai_careers)
            
            # If OpenAI found excellent matches (≥0.85), be strict about O*NET careers
            if best_openai_score >= 0.85:
                for onet_career in onet_careers:
                    career_name = onet_career.get("name", "").lower()
                    
                    # Filter out generic production/manufacturing/technician roles
                    # when user has specialized professional skills
                    is_generic = any(
                        word in career_name
                        for word in ['production manager', 'industrial production', 
                                   'manufacturing', 'mechanical technician', 
                                   'mechanical engineering technician',
                                   'electro-mechanical technician', 'operator',
                                   'assembler', 'inspector', 'fabricator']
                    )
                    
                    # Check if user has specialized skills that don't match generic roles
                    has_specialized_skills = False
                    if user_skills:
                        specialized_keywords = [
                            'medical', 'clinical', 'research', 'scientist', 'data science',
                            'analytics', 'statistics', 'biostatistics', 'epidemiology',
                            'laboratory', 'healthcare', 'programming', 'software',
                            'developer', 'engineering design', 'finance', 'consulting',
                            'marketing', 'strategy', 'design', 'creative', 'ux'
                        ]
                        has_specialized_skills = any(
                            any(kw in skill.lower() for kw in specialized_keywords)
                            for skill in user_skills
                        )
                    
                    # Skip generic roles if user has specialized skills AND OpenAI found great matches
                    if is_generic and has_specialized_skills and best_openai_score >= 0.85:
                        print(f"Filtering out generic O*NET match: {onet_career.get('name')} (user has specialized skills)")
                        continue
                    
                    filtered_onet_careers.append(onet_career)
            else:
                # OpenAI didn't find great matches, keep all O*NET careers
                filtered_onet_careers = onet_careers
        else:
            # No OpenAI careers, keep all O*NET
            filtered_onet_careers = onet_careers
        
        # Combine and sort by score
        all_careers = openai_careers + filtered_onet_careers
        all_careers.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # De-duplicate by name (case-insensitive)
        seen_names = set()
        unique_careers = []
        for career in all_careers:
            name_lower = career.get("name", "").lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_careers.append(career)
        
        # Take top careers
        top_careers = unique_careers[:max_total]
        
        # Split into primary and alternatives
        primary = top_careers[:5]
        alternatives = top_careers[5:8] if len(top_careers) > 5 else []
        
        return {
            "primary": primary,
            "alternatives": alternatives
        }


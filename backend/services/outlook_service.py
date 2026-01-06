"""
5-10 Year Outlook Model
I'm analyzing long-term career outlooks based on BLS projections, automation risk, and stability signals
Trying to give a realistic view of what the next 5-10 years might look like for a career
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
from services.data_processing import DataProcessingService
from services.openai_enhancement import OpenAIEnhancementService


class OutlookService:
    """
    Analyzes 5-10 year career outlooks
    I'm combining BLS projections, automation risk, and stability metrics to give a comprehensive view
    """
    
    def __init__(self):
        self.data_service = DataProcessingService()
        self._processed_data = None
        self.openai_service = OpenAIEnhancementService()
    
    def load_processed_data(self) -> Dict[str, Any]:
        """Load processed data - caching it so I don't reload constantly"""
        if self._processed_data is None:
            self._processed_data = self.data_service.load_processed_data()
            if not self._processed_data:
                raise ValueError("Processed data not found. Run process_data.py first.")
        return self._processed_data
    
    def get_occupation_data(self, career_id: str) -> Optional[Dict[str, Any]]:
        """Get all processed data for a specific occupation"""
        processed_data = self.load_processed_data()
        
        for occ in processed_data["occupations"]:
            if occ["career_id"] == career_id:
                return occ
        
        return None
    
    def classify_growth_outlook(
        self,
        growth_rate: float,
        annual_openings: Optional[int],
        employment_2024: Optional[int],
        employment_2034: Optional[int]
    ) -> Dict[str, Any]:
        """
        Classify growth outlook as Strong, Moderate, or Uncertain
        I'm looking at growth rate, job openings, and employment trends
        """
        # If we don't have good data, it's uncertain
        if growth_rate is None or (employment_2024 is None and employment_2034 is None):
            return {
                "outlook": "Uncertain",
                "confidence": "Low",
                "reasoning": "Insufficient data to assess growth outlook. Missing growth rate or employment projections."
            }
        
        # Strong growth - high growth rate and/or lots of openings
        # I'm setting thresholds that seem reasonable based on typical job market data
        is_strong = False
        is_moderate = False
        
        # Check growth rate
        if growth_rate >= 10:
            is_strong = True
        elif growth_rate >= 5:
            is_moderate = True
        elif growth_rate < -5:
            # Declining - this is still "certain" but negative
            return {
                "outlook": "Declining",
                "confidence": "Medium",
                "reasoning": f"Projected decline of {abs(growth_rate):.1f}% over 10 years indicates shrinking job market."
            }
        
        # Check annual openings - lots of openings even with moderate growth can be strong
        if annual_openings and annual_openings > 50000:
            if growth_rate >= 5:
                is_strong = True
            elif growth_rate >= 0:
                is_moderate = True
        
        # Check employment change magnitude
        if employment_2024 and employment_2034:
            absolute_change = abs(employment_2034 - employment_2024)
            percent_change_abs = (absolute_change / employment_2024) * 100 if employment_2024 > 0 else 0
            
            if percent_change_abs > 15 and growth_rate > 0:
                is_strong = True
            elif percent_change_abs > 5:
                is_moderate = True
        
        # Classify
        if is_strong:
            return {
                "outlook": "Strong",
                "confidence": "Medium",
                "reasoning": f"Growth rate of {growth_rate:.1f}% indicates strong expansion. "
                           f"{f'{annual_openings:,} annual openings' if annual_openings else ''} "
                           f"suggests healthy job market."
            }
        elif is_moderate or growth_rate >= 0:
            return {
                "outlook": "Moderate",
                "confidence": "Medium",
                "reasoning": f"Growth rate of {growth_rate:.1f}% indicates steady but moderate expansion. "
                           f"Job market appears stable with {annual_openings:,} annual openings." if annual_openings else 
                           f"Job market appears stable."
            }
        else:
            # Negative growth but not severe enough to be "Declining"
            return {
                "outlook": "Uncertain",
                "confidence": "Low",
                "reasoning": f"Mixed signals - growth rate of {growth_rate:.1f}% is low or negative, "
                           f"making future outlook unclear."
            }
    
    def classify_automation_risk(
        self,
        automation_proxy: float,
        task_complexity: float,
        num_core_tasks: int,
        num_tasks: int
    ) -> Dict[str, Any]:
        """
        Classify automation risk as Low, Medium, or High
        I'm deriving this from task complexity and automation proxy, not using any "magic" numbers
        The idea is: more complex tasks, more core tasks, higher automation_proxy = lower automation risk
        """
        # If we don't have task data, can't really assess automation risk
        if num_tasks == 0 or automation_proxy == 0:
            return {
                "risk": "Uncertain",
                "confidence": "Low",
                "reasoning": "Insufficient task data to assess automation risk. Need task complexity and variety metrics."
            }
        
        # Automation proxy is already calculated in data_processing
        # Higher proxy = less automatable (more complex, more core tasks)
        # I'm converting this to risk levels
        
        # Low risk = high automation_proxy (job is complex, hard to automate)
        # High risk = low automation_proxy (job is simple, easier to automate)
        
        # Thresholds - these are based on the proxy calculation but I'm making them reasonable
        # The proxy ranges roughly 0-1, with higher = less automatable
        if automation_proxy >= 0.6:
            risk_level = "Low"
            confidence = "Medium"
            reasoning = f"High task complexity (proxy: {automation_proxy:.2f}) and {num_core_tasks} core tasks suggest this role requires human judgment and adaptability that's difficult to automate."
        elif automation_proxy >= 0.3:
            risk_level = "Medium"
            confidence = "Medium"
            reasoning = f"Moderate task complexity (proxy: {automation_proxy:.2f}) with {num_core_tasks} core tasks. Some aspects may be automatable, but core functions likely require human involvement."
        else:
            risk_level = "High"
            confidence = "Medium"
            reasoning = f"Lower task complexity (proxy: {automation_proxy:.2f}) and fewer core tasks ({num_core_tasks}) suggest some functions could be automated or augmented by technology."
        
        return {
            "risk": risk_level,
            "confidence": confidence,
            "reasoning": reasoning,
            "automation_proxy": automation_proxy,
            "task_complexity": task_complexity
        }
    
    def assess_stability_signal(
        self,
        growth_rate: float,
        employment_2024: Optional[int],
        employment_2034: Optional[int],
        stability_score: float
    ) -> Dict[str, Any]:
        """
        Assess stability signal as Expanding, Shifting, or Declining
        I'm looking at growth trends and employment size changes
        """
        # Expanding = positive growth, increasing employment
        # Shifting = mixed signals, some change but not clear direction
        # Declining = negative growth, decreasing employment
        
        if growth_rate is None:
            return {
                "signal": "Uncertain",
                "confidence": "Low",
                "reasoning": "Cannot assess stability without growth rate data."
            }
        
        # Check employment change if available
        employment_change_pct = None
        if employment_2024 and employment_2034 and employment_2024 > 0:
            employment_change_pct = ((employment_2034 - employment_2024) / employment_2024) * 100
        
        # Expanding - clear positive growth
        if growth_rate > 5 and (employment_change_pct is None or employment_change_pct > 0):
            return {
                "signal": "Expanding",
                "confidence": "Medium",
                "reasoning": f"Strong growth rate ({growth_rate:.1f}%) and {f'increasing employment ({employment_change_pct:.1f}%)' if employment_change_pct else 'positive trend'} indicate expanding job market."
            }
        
        # Declining - clear negative growth
        if growth_rate < -3:
            return {
                "signal": "Declining",
                "confidence": "Medium",
                "reasoning": f"Negative growth rate ({growth_rate:.1f}%) indicates shrinking job market. "
                           f"{f'Employment projected to decrease by {abs(employment_change_pct):.1f}%' if employment_change_pct and employment_change_pct < 0 else ''}"
            }
        
        # Shifting - moderate change, could go either way
        # Or stable but with some uncertainty
        if -3 <= growth_rate <= 5:
            if growth_rate > 0:
                signal_desc = "modest growth"
            elif growth_rate < 0:
                signal_desc = "slight decline"
            else:
                signal_desc = "stable"
            
            return {
                "signal": "Shifting",
                "confidence": "Medium",
                "reasoning": f"Moderate change ({growth_rate:.1f}% growth) suggests the field is evolving. "
                           f"Job market shows {signal_desc}, indicating some transition rather than clear expansion or decline."
            }
        
        # Fallback
        return {
            "signal": "Uncertain",
            "confidence": "Low",
            "reasoning": "Insufficient data to determine stability signal."
        }
    
    def calculate_confidence(
        self,
        has_bls_data: bool,
        has_task_data: bool,
        growth_outlook: Dict[str, Any],
        automation_risk: Dict[str, Any],
        stability_signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall confidence indicator with reasoning
        I'm looking at data completeness and consistency of signals
        """
        confidence_factors = []
        confidence_levels = []
        
        # Data completeness
        if has_bls_data:
            confidence_factors.append("BLS projection data available")
            confidence_levels.append("Medium")
        else:
            confidence_factors.append("Missing BLS projection data - limits growth and stability assessment")
            confidence_levels.append("Low")
        
        if has_task_data:
            confidence_factors.append("Task data available for automation risk assessment")
            confidence_levels.append("Medium")
        else:
            confidence_factors.append("Missing task data - cannot assess automation risk reliably")
            confidence_levels.append("Low")
        
        # Signal consistency
        growth_conf = growth_outlook.get("confidence", "Low")
        automation_conf = automation_risk.get("confidence", "Low")
        stability_conf = stability_signal.get("confidence", "Low")
        
        # Overall confidence - take the "lowest common denominator" approach
        # If any component has low confidence, overall is lower
        if "Low" in [growth_conf, automation_conf, stability_conf]:
            overall_confidence = "Low"
        elif all(c == "Medium" for c in [growth_conf, automation_conf, stability_conf]):
            overall_confidence = "Medium"
        else:
            overall_confidence = "Medium"  # Default to medium if mixed
        
        # Build reasoning
        why = "Confidence assessment based on: " + "; ".join(confidence_factors)
        why += f". Individual component confidence: Growth ({growth_conf}), Automation Risk ({automation_conf}), Stability ({stability_conf})."
        
        return {
            "level": overall_confidence,
            "why": why,
            "factors": confidence_factors
        }
    
    def get_assumptions_and_limitations(self) -> Dict[str, Any]:
        """
        Document assumptions and limitations
        I'm being transparent about what the model can and can't do
        """
        return {
            "dataset_coverage": {
                "description": "Analysis based on O*NET 30.1 database and BLS Employment Projections 2024-2034",
                "occupation_coverage": "Limited to occupations with complete O*NET and BLS data",
                "time_horizon": "Projections cover 2024-2034 (10 year window), not full 5-10 year range",
                "geographic_scope": "National-level projections, regional variations not accounted for"
            },
            "assumptions": [
                "BLS projections are accurate predictors of future employment trends",
                "Task complexity and variety are good proxies for automation risk (not based on actual automation studies)",
                "Growth rates and employment changes follow linear trends (reality may be non-linear)",
                "Current skill requirements remain relatively stable over 10 years",
                "Economic conditions and technological changes follow historical patterns"
            ],
            "limitations": [
                "Cannot predict black swan events (pandemics, major economic disruptions, breakthrough technologies)",
                "Automation risk is a proxy based on task characteristics, not actual automation feasibility studies",
                "Does not account for industry-specific disruptions or regulatory changes",
                "Regional job markets may differ significantly from national projections",
                "Education and training trends may shift faster than projected",
                "Wage data is from 2024 baseline, does not project future wage changes",
                "Does not consider part-time vs full-time employment shifts"
            ],
            "data_quality_notes": [
                "Some occupations may have incomplete task data, affecting automation risk assessment",
                "BLS projections updated periodically - current analysis uses 2024-2034 projections",
                "O*NET data reflects current job requirements, may not capture emerging skill needs"
            ]
        }
    
    def analyze_outlook(
        self,
        career_id: str
    ) -> Dict[str, Any]:
        """
        Main method - analyze 5-10 year outlook for a career
        Returns growth outlook, automation risk, stability signal, confidence, and assumptions
        """
        occ_data = self.get_occupation_data(career_id)
        
        if not occ_data:
            return {
                "error": f"Occupation with career_id {career_id} not found"
            }
        
        # Get outlook features
        outlook_features = occ_data.get("outlook_features", {})
        task_features = occ_data.get("task_features", {})
        
        has_bls_data = outlook_features.get("has_projection", False)
        has_task_data = task_features.get("num_tasks", 0) > 0
        
        # Classify growth outlook
        growth_outlook = self.classify_growth_outlook(
            growth_rate=outlook_features.get("growth_rate", 0),
            annual_openings=outlook_features.get("annual_openings"),
            employment_2024=outlook_features.get("employment_2024"),
            employment_2034=outlook_features.get("employment_2034")
        )
        
        # Classify automation risk
        automation_risk = self.classify_automation_risk(
            automation_proxy=task_features.get("automation_proxy", 0),
            task_complexity=task_features.get("task_complexity_score", 0),
            num_core_tasks=task_features.get("num_core_tasks", 0),
            num_tasks=task_features.get("num_tasks", 0)
        )
        
        # Assess stability signal
        stability_signal = self.assess_stability_signal(
            growth_rate=outlook_features.get("growth_rate", 0),
            employment_2024=outlook_features.get("employment_2024"),
            employment_2034=outlook_features.get("employment_2034"),
            stability_score=outlook_features.get("stability_score", 0)
        )
        
        # Calculate confidence
        confidence = self.calculate_confidence(
            has_bls_data=has_bls_data,
            has_task_data=has_task_data,
            growth_outlook=growth_outlook,
            automation_risk=automation_risk,
            stability_signal=stability_signal
        )
        
        # Get assumptions and limitations
        assumptions = self.get_assumptions_and_limitations()
        
        # Get certifications using OpenAI
        certifications = self.openai_service.get_career_certifications(
            career_name=occ_data.get("name"),
            career_data=occ_data
        )
        
        return {
            "career": {
                "career_id": career_id,
                "name": occ_data.get("name"),
                "soc_code": occ_data.get("soc_code")
            },
            "growth_outlook": growth_outlook,
            "automation_risk": automation_risk,
            "stability_signal": stability_signal,
            "confidence": confidence,
            "certifications": certifications,
            "data_quality": {
                "has_bls_data": has_bls_data,
                "has_task_data": has_task_data,
                "completeness": "High" if (has_bls_data and has_task_data) else "Partial" if (has_bls_data or has_task_data) else "Low"
            },
            "assumptions_and_limitations": assumptions,
            "raw_metrics": {
                "growth_rate": outlook_features.get("growth_rate"),
                "employment_2024": outlook_features.get("employment_2024"),
                "employment_2034": outlook_features.get("employment_2034"),
                "annual_openings": outlook_features.get("annual_openings"),
                "automation_proxy": task_features.get("automation_proxy"),
                "stability_score": outlook_features.get("stability_score")
            }
        }



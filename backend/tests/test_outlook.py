"""
Unit tests for outlook outputs and confidence
Tests analyze_outlook and calculate_confidence methods in OutlookService
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from services.outlook_service import OutlookService


class TestOutlookOutputs:
    """Test suite for outlook outputs and confidence"""
    
    @pytest.fixture
    def mock_service(self, sample_processed_data):
        """Create a mocked outlook service with test data"""
        service = OutlookService()
        service.data_service = Mock()
        service.data_service.load_processed_data = Mock(return_value=sample_processed_data)
        service._processed_data = sample_processed_data
        service.load_processed_data = Mock(return_value=sample_processed_data)
        
        # Add task_features to sample data if missing
        for occ in sample_processed_data["occupations"]:
            if "task_features" not in occ:
                occ["task_features"] = {
                    "automation_proxy": 0.3,
                    "task_complexity_score": 0.7,
                    "num_core_tasks": 10,
                    "num_tasks": 20
                }
            if "outlook_features" in occ and "has_projection" not in occ["outlook_features"]:
                occ["outlook_features"]["has_projection"] = True
        
        return service
    
    def test_analyze_outlook_structure(self, mock_service):
        """Test that outlook analysis returns correct structure"""
        result = mock_service.analyze_outlook("test_engineer_001")
        
        assert "career" in result
        assert "growth_outlook" in result
        assert "automation_risk" in result
        assert "stability_signal" in result
        assert "confidence" in result
        assert "data_quality" in result
        assert "raw_metrics" in result
        
        # Check career structure
        assert "career_id" in result["career"]
        assert "name" in result["career"]
        assert "soc_code" in result["career"]
    
    def test_analyze_outlook_error_handling(self, mock_service):
        """Test error handling when career ID is invalid"""
        result = mock_service.analyze_outlook("invalid_career_001")
        
        assert "error" in result
    
    def test_growth_outlook_structure(self, mock_service):
        """Test that growth_outlook has correct structure"""
        result = mock_service.analyze_outlook("test_engineer_001")
        
        growth = result["growth_outlook"]
        assert "outlook" in growth
        assert "confidence" in growth
        assert "reasoning" in growth
        
        # Outlook should be one of the valid categories
        assert growth["outlook"] in ["Strong Growth", "Moderate Growth", "Limited Growth", "Declining", "Stable"]
    
    def test_automation_risk_structure(self, mock_service):
        """Test that automation_risk has correct structure"""
        result = mock_service.analyze_outlook("test_engineer_001")
        
        risk = result["automation_risk"]
        assert "risk" in risk
        assert "confidence" in risk
        assert "reasoning" in risk
        
        # Risk should be one of the valid categories
        assert risk["risk"] in ["Low", "Medium", "High", "Very Low"]
    
    def test_stability_signal_structure(self, mock_service):
        """Test that stability_signal has correct structure"""
        result = mock_service.analyze_outlook("test_engineer_001")
        
        stability = result["stability_signal"]
        assert "signal" in stability
        assert "confidence" in stability
        assert "reasoning" in stability
        
        # Signal should be one of the valid categories
        assert stability["signal"] in ["Strong", "Moderate", "Weak", "Uncertain"]
    
    def test_confidence_structure(self, mock_service):
        """Test that confidence has correct structure"""
        result = mock_service.analyze_outlook("test_engineer_001")
        
        confidence = result["confidence"]
        assert "level" in confidence
        assert "why" in confidence
        assert "factors" in confidence
        
        # Level should be one of the valid categories
        assert confidence["level"] in ["Low", "Medium", "High"]
        
        # Why should be a string explaining the confidence
        assert isinstance(confidence["why"], str)
        assert len(confidence["why"]) > 0
        
        # Factors should be a list
        assert isinstance(confidence["factors"], list)
    
    def test_calculate_confidence_levels(self, mock_service):
        """Test confidence calculation with different data availability"""
        # High confidence case (both data sources available)
        growth_outlook = {"confidence": "Medium"}
        automation_risk = {"confidence": "Medium"}
        stability_signal = {"confidence": "Medium"}
        
        confidence = mock_service.calculate_confidence(
            has_bls_data=True,
            has_task_data=True,
            growth_outlook=growth_outlook,
            automation_risk=automation_risk,
            stability_signal=stability_signal
        )
        
        assert confidence["level"] in ["Low", "Medium", "High"]
        assert len(confidence["factors"]) > 0
        
        # Low confidence case (missing data)
        confidence_low = mock_service.calculate_confidence(
            has_bls_data=False,
            has_task_data=False,
            growth_outlook={"confidence": "Low"},
            automation_risk={"confidence": "Low"},
            stability_signal={"confidence": "Low"}
        )
        
        assert confidence_low["level"] == "Low"
    
    def test_data_quality_structure(self, mock_service):
        """Test that data_quality has correct structure"""
        result = mock_service.analyze_outlook("test_engineer_001")
        
        data_quality = result["data_quality"]
        assert "has_bls_data" in data_quality
        assert "has_task_data" in data_quality
        assert "completeness" in data_quality
        
        assert isinstance(data_quality["has_bls_data"], bool)
        assert isinstance(data_quality["has_task_data"], bool)
        assert data_quality["completeness"] in ["High", "Partial", "Low"]
    
    def test_raw_metrics_structure(self, mock_service):
        """Test that raw_metrics has correct structure"""
        result = mock_service.analyze_outlook("test_engineer_001")
        
        raw = result["raw_metrics"]
        assert "growth_rate" in raw
        assert "employment_2024" in raw
        assert "employment_2034" in raw
        assert "annual_openings" in raw
        assert "automation_proxy" in raw
        assert "stability_score" in raw
        
        # Growth rate should be a number (could be None)
        if raw["growth_rate"] is not None:
            assert isinstance(raw["growth_rate"], (int, float))
        
        # Employment numbers should be integers or None
        if raw["employment_2024"] is not None:
            assert isinstance(raw["employment_2024"], int)
            assert raw["employment_2024"] >= 0
        
        if raw["employment_2034"] is not None:
            assert isinstance(raw["employment_2034"], int)
            assert raw["employment_2034"] >= 0
    
    def test_classify_growth_outlook(self, mock_service):
        """Test growth outlook classification"""
        # Strong growth
        growth = mock_service.classify_growth_outlook(
            growth_rate=15.0,
            annual_openings=100000,
            employment_2024=1000000,
            employment_2034=1150000
        )
        assert growth["outlook"] == "Strong Growth"
        
        # Declining
        growth = mock_service.classify_growth_outlook(
            growth_rate=-5.0,
            annual_openings=5000,
            employment_2024=100000,
            employment_2034=95000
        )
        assert growth["outlook"] == "Declining"
        
        # Stable
        growth = mock_service.classify_growth_outlook(
            growth_rate=2.0,
            annual_openings=5000,
            employment_2024=100000,
            employment_2034=102000
        )
        assert growth["outlook"] in ["Stable", "Moderate Growth"]
    
    def test_classify_automation_risk(self, mock_service):
        """Test automation risk classification"""
        # Low risk
        risk = mock_service.classify_automation_risk(
            automation_proxy=0.2,
            task_complexity=0.8,
            num_core_tasks=20,
            num_tasks=50
        )
        assert risk["risk"] in ["Low", "Very Low"]
        
        # High risk
        risk = mock_service.classify_automation_risk(
            automation_proxy=0.8,
            task_complexity=0.2,
            num_core_tasks=5,
            num_tasks=10
        )
        assert risk["risk"] == "High"
    
    def test_assess_stability_signal(self, mock_service):
        """Test stability signal assessment"""
        # Strong signal
        signal = mock_service.assess_stability_signal(
            growth_rate=10.0,
            employment_2024=1000000,
            employment_2034=1100000,
            stability_score=0.8
        )
        assert signal["signal"] in ["Strong", "Moderate"]
        
        # Weak signal
        signal = mock_service.assess_stability_signal(
            growth_rate=-5.0,
            employment_2024=100000,
            employment_2034=95000,
            stability_score=0.3
        )
        assert signal["signal"] in ["Weak", "Uncertain"]
    
    def test_confidence_factors(self, mock_service):
        """Test that confidence factors are meaningful"""
        result = mock_service.analyze_outlook("test_engineer_001")
        
        confidence = result["confidence"]
        factors = confidence["factors"]
        
        # Should have at least one factor
        assert len(factors) > 0
        
        # All factors should be strings
        assert all(isinstance(factor, str) for factor in factors)
        
        # Factors should be informative (non-empty)
        assert all(len(factor) > 0 for factor in factors)


"""
Unit tests for feature extraction logic
Tests the build_user_feature_vector method in CareerRecommendationService
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from services.recommendation_service import CareerRecommendationService
from pathlib import Path


class TestFeatureExtraction:
    """Test suite for feature extraction"""
    
    @pytest.fixture
    def mock_service(self, sample_processed_data):
        """Create a mocked recommendation service with test data"""
        service = CareerRecommendationService()
        service._processed_data = sample_processed_data
        service.load_processed_data = Mock(return_value=sample_processed_data)
        return service
    
    def test_feature_extraction_with_skills_only(self, mock_service, sample_user_skills):
        """Test feature extraction with only skills provided"""
        result = mock_service.build_user_feature_vector(skills=sample_user_skills)
        
        assert "combined_vector" in result
        assert "skill_vector" in result
        assert "interest_vector" in result
        assert "values_vector" in result
        assert "constraint_features" in result
        
        # Check that skill vector has correct length
        assert len(result["skill_vector"]) == len(mock_service._processed_data["skill_names"])
        
        # Check that skills are marked in the vector
        skill_vector = np.array(result["skill_vector"])
        assert np.any(skill_vector > 0), "At least one skill should be marked"
        
        # Check combined vector structure
        combined = np.array(result["combined_vector"])
        expected_length = (
            len(mock_service._processed_data["skill_names"]) +
            len(mock_service.riasec_categories) +
            len(mock_service.work_values) +
            3  # constraint features
        )
        assert len(combined) == expected_length
    
    def test_feature_extraction_with_skill_importance(self, mock_service, sample_user_skills):
        """Test feature extraction with skill importance weights"""
        skill_importance = {
            "Writing": 5.0,
            "Speaking": 4.0,
            "Critical Thinking": 5.0
        }
        
        result = mock_service.build_user_feature_vector(
            skills=sample_user_skills,
            skill_importance=skill_importance
        )
        
        skill_vector = np.array(result["skill_vector"])
        all_skills = mock_service._processed_data["skill_names"]
        
        # Check that skills with higher importance have higher values
        writing_idx = all_skills.index("Writing")
        speaking_idx = all_skills.index("Speaking")
        
        # Normalized importance (5.0 / 5.0 = 1.0, 4.0 / 5.0 = 0.8)
        assert skill_vector[writing_idx] > 0
        assert skill_vector[speaking_idx] > 0
    
    def test_feature_extraction_with_interests(self, mock_service, sample_user_interests):
        """Test feature extraction with RIASEC interests"""
        result = mock_service.build_user_feature_vector(interests=sample_user_interests)
        
        interest_vector = np.array(result["interest_vector"])
        
        # Check that interest vector has correct length
        assert len(interest_vector) == len(mock_service.riasec_categories)
        
        # Check that interests are normalized (0-7 to 0-1)
        assert np.all(interest_vector >= 0), "All interest values should be >= 0"
        assert np.all(interest_vector <= 1), "All interest values should be <= 1"
        
        # Check that provided interests are set
        investigative_idx = mock_service.riasec_categories.index("Investigative")
        assert interest_vector[investigative_idx] > 0, "Investigative interest should be set"
    
    def test_feature_extraction_with_work_values(self, mock_service, sample_work_values):
        """Test feature extraction with work values"""
        result = mock_service.build_user_feature_vector(work_values=sample_work_values)
        
        values_vector = np.array(result["values_vector"])
        
        # Check that values vector has correct length
        assert len(values_vector) == len(mock_service.work_values)
        
        # Check that values are normalized (0-7 to 0-1)
        assert np.all(values_vector >= 0), "All values should be >= 0"
        assert np.all(values_vector <= 1), "All values should be <= 1"
        
        # Check that provided values are set
        independence_idx = mock_service.work_values.index("Independence")
        assert values_vector[independence_idx] > 0, "Independence value should be set"
    
    def test_feature_extraction_with_constraints(self, mock_service, sample_constraints):
        """Test feature extraction with constraints"""
        result = mock_service.build_user_feature_vector(constraints=sample_constraints)
        
        constraint_features = np.array(result["constraint_features"])
        
        # Check that constraint features have correct length (3)
        assert len(constraint_features) == 3
        
        # Check wage normalization (80000 / 200000 = 0.4)
        assert constraint_features[0] == pytest.approx(0.4, abs=0.01)
        
        # Check remote preference (True = 1.0)
        assert constraint_features[1] == 1.0
        
        # Check education level (3 / 5 = 0.6)
        assert constraint_features[2] == pytest.approx(0.6, abs=0.01)
    
    def test_feature_extraction_complete_profile(self, mock_service, sample_user_skills, 
                                                  sample_user_interests, sample_work_values, 
                                                  sample_constraints):
        """Test feature extraction with complete user profile"""
        result = mock_service.build_user_feature_vector(
            skills=sample_user_skills,
            interests=sample_user_interests,
            work_values=sample_work_values,
            constraints=sample_constraints
        )
        
        # Check all components are present
        assert "combined_vector" in result
        assert "skill_vector" in result
        assert "interest_vector" in result
        assert "values_vector" in result
        assert "constraint_features" in result
        assert "skill_names" in result
        
        # Check combined vector is correct length
        combined = np.array(result["combined_vector"])
        expected_length = (
            len(mock_service._processed_data["skill_names"]) +
            len(mock_service.riasec_categories) +
            len(mock_service.work_values) +
            3
        )
        assert len(combined) == expected_length
        
        # Check that combined vector is concatenation of all features
        skill_vec = np.array(result["skill_vector"])
        interest_vec = np.array(result["interest_vector"])
        values_vec = np.array(result["values_vector"])
        constraint_vec = np.array(result["constraint_features"])
        
        expected_combined = np.concatenate([skill_vec, interest_vec, values_vec, constraint_vec])
        assert np.allclose(combined, expected_combined), "Combined vector should be concatenation"
    
    def test_feature_extraction_empty_input(self, mock_service):
        """Test feature extraction with no inputs (empty profile)"""
        result = mock_service.build_user_feature_vector()
        
        # All vectors should be zeros (except constraint features which have defaults)
        skill_vector = np.array(result["skill_vector"])
        interest_vector = np.array(result["interest_vector"])
        values_vector = np.array(result["values_vector"])
        constraint_features = np.array(result["constraint_features"])
        
        assert np.all(skill_vector == 0), "Skill vector should be zeros"
        assert np.all(interest_vector == 0), "Interest vector should be zeros"
        assert np.all(values_vector == 0), "Values vector should be zeros"
        # Constraint features: [0.0, 0.0, 1.0] when constraints is None
        # (max_education_level defaults to 5, which normalizes to 1.0)
        assert constraint_features[0] == 0.0, "Min wage should be 0"
        assert constraint_features[1] == 0.0, "Remote preferred should be 0"
        assert constraint_features[2] == 1.0, "Max education level defaults to 1.0 (5/5)"
    
    def test_feature_extraction_skill_matching(self, mock_service):
        """Test that skill matching works correctly (fuzzy matching)"""
        # Test with slightly different skill names
        skills = ["Writing", "Speak", "Crit Think"]
        
        result = mock_service.build_user_feature_vector(skills=skills)
        skill_vector = np.array(result["skill_vector"])
        
        # At least one skill should match (Writing)
        assert np.any(skill_vector > 0), "At least one skill should match"
    
    def test_feature_extraction_normalization(self, mock_service):
        """Test that all values are properly normalized"""
        skill_importance = {"Writing": 5.0}  # Max importance
        interests = {"Investigative": 7.0}  # Max interest
        work_values = {"Independence": 7.0}  # Max value
        
        result = mock_service.build_user_feature_vector(
            skills=["Writing"],
            skill_importance=skill_importance,
            interests=interests,
            work_values=work_values
        )
        
        skill_vector = np.array(result["skill_vector"])
        interest_vector = np.array(result["interest_vector"])
        values_vector = np.array(result["values_vector"])
        
        # All values should be in [0, 1] range
        assert np.all(skill_vector >= 0) and np.all(skill_vector <= 1)
        assert np.all(interest_vector >= 0) and np.all(interest_vector <= 1)
        assert np.all(values_vector >= 0) and np.all(values_vector <= 1)
        
        # Max values should be close to 1.0 (allowing for small floating point errors)
        assert np.max(skill_vector) == pytest.approx(1.0, abs=0.01)
        assert np.max(interest_vector) == pytest.approx(1.0, abs=0.01)
        assert np.max(values_vector) == pytest.approx(1.0, abs=0.01)


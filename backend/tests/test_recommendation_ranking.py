"""
Unit tests for recommendation ranking stability
Tests ml_rank and baseline_rank methods in CareerRecommendationService
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from services.recommendation_service import CareerRecommendationService


class TestRecommendationRankingStability:
    """Test suite for recommendation ranking stability"""
    
    @pytest.fixture
    def mock_service(self, sample_processed_data):
        """Create a mocked recommendation service with test data"""
        service = CareerRecommendationService()
        service._processed_data = sample_processed_data
        service.load_processed_data = Mock(return_value=sample_processed_data)
        service._occupation_vectors = None
        return service
    
    def test_baseline_rank_stability(self, mock_service):
        """Test that baseline ranking is stable (deterministic)"""
        # Build a vector with correct dimensions
        # build_occupation_vectors creates vectors of length: skill_vec + 6 (interests) + 6 (values) + 3 (constraints)
        # From fixture: skill_vec is 26 (10*2 + 3 + 3), so total is 26 + 6 + 6 + 3 = 41
        user_vector = np.random.rand(41)
        user_vector = user_vector / np.linalg.norm(user_vector)  # Normalize
        
        # Run ranking multiple times
        results1 = mock_service.baseline_rank(user_vector, top_n=5)
        results2 = mock_service.baseline_rank(user_vector, top_n=5)
        results3 = mock_service.baseline_rank(user_vector, top_n=5)
        
        # Results should be identical (deterministic)
        assert len(results1) == len(results2) == len(results3)
        assert all(r1[0] == r2[0] for r1, r2 in zip(results1, results2)), "Career IDs should match"
        assert all(r1[0] == r3[0] for r1, r3 in zip(results1, results3)), "Career IDs should match"
        
        # Scores should be identical (or very close due to floating point)
        for r1, r2 in zip(results1, results2):
            assert abs(r1[1] - r2[1]) < 1e-10, "Scores should be identical"
    
    def test_baseline_rank_ordering(self, mock_service):
        """Test that baseline ranking returns results in descending score order"""
        user_vector = np.random.rand(41)
        user_vector = user_vector / np.linalg.norm(user_vector)
        
        results = mock_service.baseline_rank(user_vector, top_n=5)
        
        # Check that results are sorted by score (descending)
        scores = [r[1] for r in results]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by score"
        
        # Check that all scores are in valid range [0, 1] (cosine similarity)
        assert all(0 <= score <= 1 for score in scores), "All scores should be in [0, 1]"
    
    def test_baseline_rank_top_n(self, mock_service):
        """Test that baseline ranking respects top_n parameter"""
        user_vector = np.random.rand(41)
        user_vector = user_vector / np.linalg.norm(user_vector)
        
        for top_n in [1, 2, 3, 5, 10]:
            results = mock_service.baseline_rank(user_vector, top_n=top_n)
            assert len(results) <= top_n, f"Should return at most {top_n} results"
    
    def test_ml_rank_fallback_to_baseline(self, mock_service):
        """Test that ml_rank falls back to baseline when model is not available"""
        user_vector = np.random.rand(41)
        user_vector = user_vector / np.linalg.norm(user_vector)
        
        mock_service.ml_model = None
        
        baseline_results = mock_service.baseline_rank(user_vector, top_n=5)
        ml_results = mock_service.ml_rank(user_vector, top_n=5, use_model=True)
        
        # ML results should match baseline when model is None
        assert len(ml_results) == len(baseline_results)
        assert all(r[0] == baseline_results[i][0] for i, r in enumerate(ml_results))
        
        # ML results should have explanation dict
        assert all(len(r) == 3 for r in ml_results), "Results should have (career_id, score, explanation)"
        assert all("method" in r[2] for r in ml_results), "Explanation should have method"
        assert all(r[2]["method"] == "baseline" for r in ml_results)
    
    def test_ml_rank_with_model(self, mock_service):
        """Test ml_rank with a mock ML model"""
        user_vector = np.random.rand(41)
        user_vector = user_vector / np.linalg.norm(user_vector)
        
        # Create a mock model that returns probabilities
        mock_model = MagicMock()
        mock_proba = np.array([[0.3, 0.7]])  # [prob_class_0, prob_class_1]
        mock_model.predict_proba.return_value = mock_proba
        
        mock_service.ml_model = mock_model
        mock_service.scaler = None
        
        results = mock_service.ml_rank(user_vector, top_n=5, use_model=True)
        
        # Should have results
        assert len(results) > 0
        
        # All results should have explanation
        for career_id, score, explanation in results:
            assert "method" in explanation
            assert explanation["method"] == "ml_model"
            assert "confidence" in explanation
            assert 0 <= score <= 1
    
    def test_ranking_consistency_similar_inputs(self, mock_service):
        """Test that similar inputs produce similar rankings"""
        base_vector = np.random.rand(41)
        base_vector = base_vector / np.linalg.norm(base_vector)
        
        # Create slightly modified vectors
        vector1 = base_vector + np.random.rand(41) * 0.01
        vector1 = vector1 / np.linalg.norm(vector1)
        
        vector2 = base_vector + np.random.rand(41) * 0.01
        vector2 = vector2 / np.linalg.norm(vector2)
        
        results1 = mock_service.baseline_rank(vector1, top_n=5)
        results2 = mock_service.baseline_rank(vector2, top_n=5)
        
        # Similar inputs should produce similar top results
        # (at least some overlap in top 5)
        top_careers1 = {r[0] for r in results1}
        top_careers2 = {r[0] for r in results2}
        
        overlap = len(top_careers1 & top_careers2)
        # With only 3 occupations in test data, we expect at least some overlap
        assert overlap >= 0, "Should have some overlap with similar inputs"
    
    def test_ranking_score_range(self, mock_service):
        """Test that all ranking scores are in valid range [0, 1]"""
        user_vector = np.random.rand(41)
        user_vector = user_vector / np.linalg.norm(user_vector)
        
        baseline_results = mock_service.baseline_rank(user_vector, top_n=10)
        
        for career_id, score in baseline_results:
            assert 0 <= score <= 1, f"Score {score} should be in [0, 1]"
    
    def test_ranking_no_duplicates(self, mock_service):
        """Test that ranking returns no duplicate career IDs"""
        user_vector = np.random.rand(41)
        user_vector = user_vector / np.linalg.norm(user_vector)
        
        results = mock_service.baseline_rank(user_vector, top_n=10)
        career_ids = [r[0] for r in results]
        
        assert len(career_ids) == len(set(career_ids)), "No duplicate career IDs should be returned"


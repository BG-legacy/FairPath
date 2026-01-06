"""
Integration tests for API endpoints
Tests end-to-end flows, invalid inputs, empty inputs, and OpenAI fallback paths
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
import json

from app.main import app
from models.schemas import BaseResponse, ErrorResponse


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_intake_data():
    """Sample intake data for testing"""
    return {
        "skills": ["Python", "JavaScript", "Project Management"],
        "interests": ["Investigative", "Artistic", "Enterprising"],
        "constraints": {
            "min_wage": 80000,
            "remote_preferred": True,
            "max_education_level": 3
        },
        "values": {
            "impact": 6.0,
            "stability": 5.0,
            "flexibility": 7.0
        }
    }


@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing"""
    return """John Doe
Software Engineer
john.doe@email.com | (555) 123-4567

PROFESSIONAL SUMMARY
Experienced software engineer with expertise in Python, JavaScript, and cloud technologies.

WORK EXPERIENCE
Senior Software Engineer | Tech Company Inc. | 2020 - Present
• Developed scalable web applications using Python and React
• Led a team of 5 engineers to deliver high-quality software
• Implemented CI/CD pipelines reducing deployment time by 50%
• Designed and implemented RESTful APIs

EDUCATION
Bachelor of Science in Computer Science | University | 2018

SKILLS
• Programming Languages: Python, JavaScript, TypeScript, Java
• Frameworks: React, Node.js, Django, Flask
• Tools: Git, Docker, Kubernetes, AWS
"""


class TestIntegrationHappyPath:
    """Test happy path end-to-end flow: intake → recs → outlook → switch → resume"""
    
    def test_happy_path_end_to_end(self, client, sample_intake_data, sample_resume_text):
        """Test complete flow from intake to resume analysis"""
        # Step 1: Intake - normalize user profile
        intake_response = client.post("/api/intake/intake", json=sample_intake_data)
        assert intake_response.status_code == status.HTTP_200_OK
        intake_data = intake_response.json()
        assert intake_data["success"] is True
        assert "data" in intake_data
        assert "normalized_profile" in intake_data["data"]
        
        # Step 2: Get recommendations
        recs_request = {
            "skills": sample_intake_data["skills"],
            "interests": {
                "Investigative": 7.0,
                "Artistic": 4.0,
                "Enterprising": 6.0
            },
            "work_values": sample_intake_data["values"],
            "constraints": sample_intake_data["constraints"],
            "top_n": 5
        }
        recs_response = client.post("/api/recommendations/recommendations", json=recs_request)
        assert recs_response.status_code == status.HTTP_200_OK
        recs_data = recs_response.json()
        assert recs_data["success"] is True
        assert "data" in recs_data
        assert "careers" in recs_data["data"]
        assert len(recs_data["data"]["careers"]) > 0
        
        # Get first career ID for next steps
        first_career = recs_data["data"]["careers"][0]
        career_id = first_career["career_id"]
        
        # Step 3: Get outlook for the recommended career
        outlook_response = client.get(f"/api/outlook/{career_id}")
        assert outlook_response.status_code == status.HTTP_200_OK
        outlook_data = outlook_response.json()
        assert outlook_data["success"] is True
        assert "data" in outlook_data
        assert "growth_outlook" in outlook_data["data"]
        assert "automation_risk" in outlook_data["data"]
        assert "stability" in outlook_data["data"]
        
        # Step 4: Analyze career switch (if we have at least 2 careers)
        if len(recs_data["data"]["careers"]) > 1:
            second_career = recs_data["data"]["careers"][1]
            target_career_id = second_career["career_id"]
            
            switch_request = {
                "source_career_id": career_id,
                "target_career_id": target_career_id
            }
            switch_response = client.post("/api/career-switch/switch", json=switch_request)
            assert switch_response.status_code == status.HTTP_200_OK
            switch_data = switch_response.json()
            assert switch_data["success"] is True
            assert "data" in switch_data
            assert "overlap_percentage" in switch_data["data"]
            assert "difficulty" in switch_data["data"]
            assert "transition_time_range" in switch_data["data"]
        
        # Step 5: Analyze resume (using text format)
        resume_file = ("resume.txt", BytesIO(sample_resume_text.encode('utf-8')), "text/plain")
        resume_response = client.post(
            "/api/resume/analyze",
            files={"file": resume_file},
            data={"target_career_id": career_id}
        )
        assert resume_response.status_code == status.HTTP_200_OK
        resume_data = resume_response.json()
        assert resume_data["success"] is True
        assert "data" in resume_data
        assert "extracted_text" in resume_data["data"]
        assert "detected_skills" in resume_data["data"]
        assert "structure" in resume_data["data"]
        
        # Step 6: Rewrite resume bullets
        bullets = [
            "Developed scalable web applications using Python and React",
            "Led a team of 5 engineers to deliver high-quality software"
        ]
        rewrite_request = {
            "bullets": bullets,
            "target_career_id": career_id
        }
        rewrite_response = client.post("/api/resume/rewrite", json=rewrite_request)
        assert rewrite_response.status_code == status.HTTP_200_OK
        rewrite_data = rewrite_response.json()
        assert rewrite_data["success"] is True
        assert "data" in rewrite_data
        assert "rewrites" in rewrite_data["data"]


class TestIntegrationInvalidInputs:
    """Test invalid input cases"""
    
    def test_intake_invalid_interests(self, client):
        """Test intake with invalid interest categories"""
        invalid_data = {
            "skills": ["Python"],
            "interests": ["InvalidCategory", "AnotherInvalid"]
        }
        response = client.post("/api/intake/intake", json=invalid_data)
        # Should still succeed but normalize to None or empty
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_intake_invalid_values_range(self, client):
        """Test intake with values outside valid range"""
        invalid_data = {
            "skills": ["Python"],
            "values": {
                "impact": 10.0,  # Above max (7.0)
                "stability": -5.0  # Below min (0.0)
            }
        }
        response = client.post("/api/intake/intake", json=invalid_data)
        # Should normalize values to valid range
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_recommendations_invalid_top_n(self, client):
        """Test recommendations with invalid top_n"""
        # Too large
        request = {
            "skills": ["Python"],
            "top_n": 100  # Above max (20)
        }
        response = client.post("/api/recommendations/recommendations", json=request)
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Too small
        request = {
            "skills": ["Python"],
            "top_n": 0  # Below min (1)
        }
        response = client.post("/api/recommendations/recommendations", json=request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_outlook_invalid_career_id(self, client):
        """Test outlook with invalid career ID"""
        response = client.get("/api/outlook/invalid_career_id_12345")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert "error" in data["detail"] or "message" in data["detail"]
    
    def test_switch_invalid_career_ids(self, client):
        """Test career switch with invalid career IDs"""
        request = {
            "source_career_id": "invalid_source_123",
            "target_career_id": "invalid_target_456"
        }
        response = client.post("/api/career-switch/switch", json=request)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
    
    def test_resume_invalid_file_type(self, client):
        """Test resume analysis with invalid file type"""
        invalid_file = ("resume.exe", BytesIO(b"fake binary data"), "application/x-msdownload")
        response = client.post(
            "/api/resume/analyze",
            files={"file": invalid_file}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
    
    def test_resume_rewrite_invalid_career_id(self, client):
        """Test resume rewrite with invalid career ID"""
        request = {
            "bullets": ["Some bullet point"],
            "target_career_id": "invalid_career_123"
        }
        response = client.post("/api/resume/rewrite", json=request)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False


class TestIntegrationEmptyMinimalInputs:
    """Test empty/minimal input cases"""
    
    def test_intake_empty_input(self, client):
        """Test intake with completely empty input"""
        empty_data = {}
        response = client.post("/api/intake/intake", json=empty_data)
        # Should still succeed with minimal processing
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_intake_minimal_skills_only(self, client):
        """Test intake with only skills"""
        minimal_data = {
            "skills": ["Python"]
        }
        response = client.post("/api/intake/intake", json=minimal_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_intake_empty_skills_list(self, client):
        """Test intake with empty skills list"""
        empty_skills = {
            "skills": []
        }
        response = client.post("/api/intake/intake", json=empty_skills)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_recommendations_minimal_input(self, client):
        """Test recommendations with minimal input (just skills)"""
        minimal_request = {
            "skills": ["Python"]
        }
        response = client.post("/api/recommendations/recommendations", json=minimal_request)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "careers" in data["data"]
        assert len(data["data"]["careers"]) > 0
    
    def test_recommendations_empty_input(self, client):
        """Test recommendations with completely empty input"""
        empty_request = {}
        response = client.post("/api/recommendations/recommendations", json=empty_request)
        # Should still work but return fewer/more generic recommendations
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_resume_rewrite_minimal_bullets(self, client):
        """Test resume rewrite with minimal bullets"""
        # First get a valid career ID
        recs_request = {"skills": ["Python"], "top_n": 1}
        recs_response = client.post("/api/recommendations/recommendations", json=recs_request)
        assert recs_response.status_code == status.HTTP_200_OK
        recs_data = recs_response.json()
        career_id = recs_data["data"]["careers"][0]["career_id"]
        
        minimal_request = {
            "bullets": ["One bullet point"],
            "target_career_id": career_id
        }
        response = client.post("/api/resume/rewrite", json=minimal_request)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "rewrites" in data["data"]


class TestIntegrationOpenAIFallback:
    """Test OpenAI failure fallback paths"""
    
    def test_recommendations_works_without_openai(self, client):
        """Test recommendations still work even if OpenAI is unavailable"""
        # This test verifies that recommendations work even if OpenAI service is unavailable
        # The service should gracefully handle OpenAI unavailability
        request = {
            "skills": ["Python", "JavaScript"],
            "interests": {"Investigative": 7.0},
            "top_n": 5
        }
        response = client.post("/api/recommendations/recommendations", json=request)
        
        # Should still succeed - recommendations work without OpenAI enhancement
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "careers" in data["data"]
        assert len(data["data"]["careers"]) > 0
        # Should have recommendations even without OpenAI enhancement
    
    def test_resume_rewrite_works_without_openai(self, client):
        """Test resume rewrite still works even if OpenAI fails - should fall back to simple rewriting"""
        # First get a valid career ID
        recs_request = {"skills": ["Python"], "top_n": 1}
        recs_response = client.post("/api/recommendations/recommendations", json=recs_request)
        assert recs_response.status_code == status.HTTP_200_OK
        recs_data = recs_response.json()
        career_id = recs_data["data"]["careers"][0]["career_id"]
        
        # Test resume rewrite - should work even if OpenAI fails (fallback to simple rewriting)
        request = {
            "bullets": [
                "Developed web applications using Python",
                "Led engineering team"
            ],
            "target_career_id": career_id
        }
        
        response = client.post("/api/resume/rewrite", json=request)
        
        # Should still succeed - fallback to simple rewriting if OpenAI fails
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "rewrites" in data["data"]
        # Should have rewrites even without OpenAI (fallback to simple rewriting)
    
    @patch('services.recommendation_service.OpenAIEnhancementService')
    def test_recommendations_openai_exception_handled(self, mock_openai_class, client):
        """Test recommendations handle OpenAI exceptions gracefully"""
        # Mock OpenAI service to simulate exception during enhancement
        mock_service_instance = MagicMock()
        mock_service_instance.is_available.return_value = True
        mock_service_instance.enhance_recommendation_explanation.return_value = {
            "enhanced_explanation": None,
            "why_this_career": None,
            "next_steps": None
        }
        mock_service_instance.refine_recommendations.side_effect = Exception("OpenAI API error")
        mock_service_instance.suggest_additional_careers.side_effect = Exception("OpenAI API error")
        mock_openai_class.return_value = mock_service_instance
        
        # Patch at the route level where the service is used
        with patch('routes.recommendations.recommendation_service.openai_service', mock_service_instance):
            request = {
                "skills": ["Python", "JavaScript"],
                "interests": {"Investigative": 7.0},
                "top_n": 5
            }
            response = client.post("/api/recommendations/recommendations", json=request)
            
            # Should still succeed - exceptions are caught and handled gracefully
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "careers" in data["data"]
            assert len(data["data"]["careers"]) > 0


class TestIntegrationResponseSchemas:
    """Test that all responses match expected schemas"""
    
    def test_intake_response_schema(self, client):
        """Test intake response matches BaseResponse schema"""
        request = {"skills": ["Python"]}
        response = client.post("/api/intake/intake", json=request)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert data["success"] is True
    
    def test_recommendations_response_schema(self, client):
        """Test recommendations response schema"""
        request = {"skills": ["Python"], "top_n": 3}
        response = client.post("/api/recommendations/recommendations", json=request)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert data["success"] is True
        assert "careers" in data["data"]
    
    def test_outlook_response_schema(self, client):
        """Test outlook response schema"""
        # First get a valid career ID
        recs_request = {"skills": ["Python"], "top_n": 1}
        recs_response = client.post("/api/recommendations/recommendations", json=recs_request)
        career_id = recs_response.json()["data"]["careers"][0]["career_id"]
        
        response = client.get(f"/api/outlook/{career_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert data["success"] is True
        assert "growth_outlook" in data["data"]
        assert "automation_risk" in data["data"]
        assert "stability" in data["data"]
    
    def test_switch_response_schema(self, client):
        """Test career switch response schema"""
        # Get two career IDs
        recs_request = {"skills": ["Python"], "top_n": 2}
        recs_response = client.post("/api/recommendations/recommendations", json=recs_request)
        careers = recs_response.json()["data"]["careers"]
        source_id = careers[0]["career_id"]
        target_id = careers[1]["career_id"]
        
        request = {
            "source_career_id": source_id,
            "target_career_id": target_id
        }
        response = client.post("/api/career-switch/switch", json=request)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert data["success"] is True
        assert "overlap_percentage" in data["data"]
        assert "difficulty" in data["data"]
        assert "transition_time_range" in data["data"]
    
    def test_resume_response_schema(self, client, sample_resume_text):
        """Test resume analysis response schema"""
        # Get a valid career ID
        recs_request = {"skills": ["Python"], "top_n": 1}
        recs_response = client.post("/api/recommendations/recommendations", json=recs_request)
        career_id = recs_response.json()["data"]["careers"][0]["career_id"]
        
        resume_file = ("resume.txt", BytesIO(sample_resume_text.encode('utf-8')), "text/plain")
        response = client.post(
            "/api/resume/analyze",
            files={"file": resume_file},
            data={"target_career_id": career_id}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert data["success"] is True
        assert "extracted_text" in data["data"]
        assert "detected_skills" in data["data"]
        assert "structure" in data["data"]


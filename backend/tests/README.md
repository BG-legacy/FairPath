# Test Suite Documentation

This directory contains comprehensive unit tests for the FairPath backend with **90%+ coverage target** (hackathon realistic, excluding framework internals).

## Test Organization

Tests are organized by feature/component:

- `test_feature_extraction.py` - Feature extraction logic tests
- `test_recommendation_ranking.py` - Recommendation ranking stability tests
- `test_explainability.py` - Explainability output tests
- `test_career_switch.py` - Career switch overlap and translation map tests
- `test_outlook.py` - Outlook outputs and confidence tests
- `test_resume_parsing.py` - Resume parsing with fixtures tests
- `test_guardrails.py` - No-fabrication enforcement checks tests
- `test_endpoint_schemas.py` - Schema validation for all endpoint responses tests
- `conftest.py` - Shared pytest fixtures

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=. --cov-report=html --cov-report=term --cov-fail-under=90
```

### Run tests in CI mode
```bash
pytest --cov=. --cov-report=xml --cov-report=term --cov-fail-under=90
```

### Run specific test file
```bash
pytest tests/test_feature_extraction.py
```

### Run specific test class
```bash
pytest tests/test_feature_extraction.py::TestFeatureExtraction
```

### Run specific test
```bash
pytest tests/test_feature_extraction.py::TestFeatureExtraction::test_feature_extraction_with_skills_only
```

### Run with verbose output
```bash
pytest -v
```

## Test Coverage

All tests are designed to achieve 100% code coverage for:

1. **Feature Extraction** - `build_user_feature_vector` method
2. **Recommendation Ranking** - `ml_rank` and `baseline_rank` methods
3. **Explainability** - `_explain_prediction` method
4. **Career Switch** - `compute_skill_overlap`, `classify_difficulty`, `estimate_transition_time`
5. **Outlook** - `analyze_outlook`, `calculate_confidence`, classification methods
6. **Resume Parsing** - `extract_text_from_file`, `parse_resume_structure`, `detect_skills`
7. **Guardrails** - `check_demographic_features`, `ensure_multiple_recommendations`, `add_uncertainty_ranges`
8. **Endpoint Schemas** - All API endpoint response schema validation

## Test Fixtures

Fixtures are defined in `conftest.py`:

- `sample_processed_data` - Sample processed data structure
- `sample_resume_text` - Sample resume text
- `sample_resume_pdf_bytes` - Sample PDF bytes (simplified)
- `sample_resume_docx_bytes` - Sample DOCX bytes (simplified)
- `sample_user_skills` - Sample user skills list
- `sample_user_interests` - Sample RIASEC interests
- `sample_work_values` - Sample work values
- `sample_constraints` - Sample constraints

## Requirements

All test dependencies are in `requirements.txt`:

- `pytest==7.4.3`
- `pytest-asyncio==0.21.1`
- `pytest-cov==4.1.0`
- `httpx==0.25.2`

## Coverage Configuration

Coverage is configured in `pytest.ini`:

- Sources: All code in the project
- Omit: tests, `__pycache__`, venv, migrations, scripts
- Report: Shows missing lines, excludes standard patterns


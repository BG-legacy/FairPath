"""
Trust and transparency endpoints - trust panel and model cards
These functions can be used both as routes and imported directly
"""
from fastapi import APIRouter
from models.schemas import BaseResponse
from pathlib import Path
import json

router = APIRouter()


@router.get("/trust-panel", response_model=BaseResponse)
async def trust_panel():
    """
    Trust panel endpoint - returns information about data collection, retention, and limitations
    
    Provides transparency about:
    - What data is collected
    - What data is NOT collected
    - Retention policies
    - Known limitations
    """
    return await get_trust_panel_data()


async def get_trust_panel_data():
    """
    Trust panel data - returns information about data collection, retention, and limitations
    """
    return BaseResponse(
        success=True,
        message="Trust panel information",
        data={
            "what_is_collected": {
                "description": "User-provided profile information used for career recommendations",
                "data_types": [
                    {
                        "type": "Skills",
                        "description": "List of skill names provided by user",
                        "source": "User input via /api/intake/intake endpoint",
                        "usage": "Matching against occupation skill requirements"
                    },
                    {
                        "type": "Interests",
                        "description": "RIASEC interest categories (Realistic, Investigative, Artistic, Social, Enterprising, Conventional) or text descriptions",
                        "source": "User input via /api/intake/intake endpoint",
                        "usage": "Matching user interests to occupation characteristics"
                    },
                    {
                        "type": "Work Values",
                        "description": "User preferences for impact, stability, and flexibility (0-7 scale)",
                        "source": "User input via /api/intake/intake endpoint",
                        "usage": "Aligning user values with occupation characteristics"
                    },
                    {
                        "type": "Constraints",
                        "description": "User constraints including minimum wage, location preferences, education level, work hours",
                        "source": "User input via /api/intake/intake endpoint",
                        "usage": "Filtering and ranking recommendations based on user constraints"
                    }
                ],
                "note": "All collected data is used solely for generating career recommendations and is not shared with third parties"
            },
            "what_is_not_collected": {
                "resumes": {
                    "description": "Resume files are processed entirely in-memory and never stored",
                    "details": [
                        "Resume content is extracted and processed ephemerally during the request",
                        "No resume files are written to disk or stored in databases",
                        "Resume content is not logged (only metadata like filename and file type)",
                        "Resume text exists only in memory during the request/response cycle",
                        "All resume content is discarded immediately after processing"
                    ],
                    "endpoints": [
                        "/api/resume/analyze - Resume analysis",
                        "/api/resume/rewrite - Resume rewriting"
                    ]
                },
                "personal_identifying_information": {
                    "description": "No personal identifying information (PII) is collected",
                    "details": [
                        "No names, addresses, phone numbers, email addresses, or social security numbers",
                        "No demographic information (age, gender, race, ethnicity, etc.)",
                        "No employment history details beyond skills extracted",
                        "No location information beyond optional location preferences"
                    ]
                },
                "user_activity": {
                    "description": "No tracking or storage of user activity",
                    "details": [
                        "No session tracking",
                        "No click tracking or analytics",
                        "No recommendation feedback or rating storage",
                        "No user account information"
                    ]
                }
            },
            "retention_policy": {
                "resumes": {
                    "policy": "No retention - processed ephemerally",
                    "details": [
                        "Resume files are never stored",
                        "Resume content is processed in-memory only",
                        "All resume data is discarded immediately after the API response",
                        "No retention period applies because no data is retained"
                    ]
                },
                "user_profile_data": {
                    "policy": "Not persisted",
                    "details": [
                        "User-provided profile data (skills, interests, values, constraints) is not stored",
                        "Data exists only during the request/response cycle",
                        "No database persistence of user profiles",
                        "Each API call processes data independently without maintaining state"
                    ],
                    "note": "If user profile data is stored in the future, this policy will be updated"
                }
            },
            "limitations": {
                "data_coverage": {
                    "description": "Limitations related to data coverage and completeness",
                    "details": [
                        "Recommendations are limited to 150 occupations in the filtered catalog",
                        "Only occupations with complete O*NET and BLS data are included",
                        "Regional job market variations are not accounted for (national projections only)",
                        "Wage data reflects 2024 baseline, not projected future wages"
                    ]
                },
                "model_limitations": {
                    "description": "Limitations of the recommendation model",
                    "details": [
                        "Model accuracy: ~78% (trained on synthetic data)",
                        "Model cannot predict black swan events (pandemics, major disruptions)",
                        "Recommendations are based on current skill requirements (may change over time)",
                        "Automation risk assessments are proxies, not based on actual automation studies",
                        "Cannot account for industry-specific disruptions or regulatory changes"
                    ]
                },
                "processing_limitations": {
                    "description": "Limitations in processing capabilities",
                    "details": [
                        "Resume analysis accuracy depends on resume format and text extraction quality",
                        "Skill detection relies on keyword matching against O*NET skill database",
                        "Gap analysis is limited to skills available in O*NET database",
                        "Recommendations assume linear trends (reality may be non-linear)"
                    ]
                }
            }
        }
    )


# Export wrapper functions for backward compatibility with main.py
async def get_trust_panel():
    """Wrapper for backward compatibility"""
    return await get_trust_panel_data()


@router.get("/model-cards", response_model=BaseResponse)
async def model_cards():
    """
    Model cards endpoint - returns information about datasets, model types, evaluation metrics, and limitations
    
    Provides transparency about:
    - Datasets used for training
    - Model types and architectures
    - Evaluation metrics and performance
    - Known limitations and mitigation steps
    """
    return await get_model_cards_data()


async def get_model_cards_data():
    """
    Model cards data - returns information about datasets, model types, evaluation metrics, and limitations
    """
    try:
        # Try to load model version from metadata
        artifacts_dir = Path(__file__).parent.parent / "artifacts" / "models"
        model_version = "1.0.0"
        if artifacts_dir.exists():
            metadata_files = list(artifacts_dir.glob("model_metadata_v*.json"))
            if metadata_files:
                # Get latest version
                versions = []
                for f in metadata_files:
                    version_str = f.stem.replace("model_metadata_v", "")
                    versions.append((version_str, f))
                versions.sort(key=lambda x: x[0], reverse=True)
                metadata_path = versions[0][1]
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    model_version = metadata.get("version", "1.0.0")
    except Exception:
        pass
    
    return BaseResponse(
        success=True,
        message="Model cards information",
        data={
            "datasets_used": {
                "onet_database": {
                    "name": "O*NET Database 30.1",
                    "version": "30.1",
                    "release_date": "December 2025",
                    "source": "O*NET Resource Center (https://www.onetcenter.org/)",
                    "license": "Creative Commons Attribution 4.0 International License",
                    "description": "Comprehensive database of occupational information including skills, tasks, work activities, knowledge, and interests",
                    "files_used": [
                        "Occupation Data.txt - Occupation titles and descriptions",
                        "Skills.txt - Skill ratings (importance and level) for occupations",
                        "Task Statements.txt - Task descriptions for occupations",
                        "Interests.txt - RIASEC interest profiles for occupations",
                        "Work Values.txt - Work value profiles for occupations"
                    ],
                    "coverage": "1,000+ occupations, filtered to 150 for production use"
                },
                "bls_employment_projections": {
                    "name": "BLS Employment Projections",
                    "version": "2024-2034",
                    "release_date": "2024",
                    "source": "U.S. Bureau of Labor Statistics (https://www.bls.gov/emp/)",
                    "license": "Public domain (U.S. government data)",
                    "description": "Employment projections, wage data, and growth statistics for occupations",
                    "files_used": [
                        "occupation.xlsx - Employment projections, wages, growth rates",
                        "education.xlsx - Education requirements and outcomes",
                        "skills.xlsx - Top skills by occupation"
                    ],
                    "coverage": "National-level projections for 2024-2034 (10-year window)",
                    "time_horizon": "2024-2034 projections"
                },
                "training_data": {
                    "name": "Synthetic Training Data",
                    "description": "Model trained on synthetically generated user-career pairs",
                    "sample_size": "3,000 training samples (80/20 train/test split)",
                    "generation_method": "Synthetic data generation with 6 match types: strong match, moderate match, weak match, poor match, partial match, wrong interests",
                    "note": "Model performance may differ when evaluated on real user data"
                }
            },
            "model_types": {
                "career_recommendation_model": {
                    "name": "Career Recommendation Model",
                    "type": "Logistic Regression (Binary Classifier)",
                    "version": model_version,
                    "library": "scikit-learn",
                    "purpose": "Rank career recommendations based on user profile (skills, interests, values, constraints)",
                    "architecture": {
                        "algorithm": "LogisticRegression",
                        "solver": "lbfgs",
                        "max_iter": 1000,
                        "random_state": 42,
                        "features": "150 features per prediction (user vector + career vector + difference vector)",
                        "preprocessing": "StandardScaler for feature normalization"
                    },
                    "input_features": [
                        "User skill vector (normalized importance and level scores)",
                        "User interest vector (RIASEC categories)",
                        "User work values vector",
                        "Career skill vector (normalized importance and level scores)",
                        "Career interest vector (RIASEC categories)",
                        "Career work values vector",
                        "Difference vectors (user - career) for all feature types"
                    ],
                    "output": "Match score (probability of good match) and ranking"
                },
                "baseline_model": {
                    "name": "Baseline Similarity Model",
                    "type": "Cosine Similarity",
                    "description": "Fallback model used when ML model is not available",
                    "algorithm": "Cosine similarity between user and career feature vectors",
                    "usage": "Used as fallback when ML model fails to load or for comparison"
                }
            },
            "evaluation_metrics": {
                "performance_metrics": {
                    "training_accuracy": "78.58%",
                    "test_accuracy": "78.00%",
                    "precision": "79% (Good Match class)",
                    "recall": "87% (Good Match class)",
                    "f1_score": "83% (Good Match class)",
                    "evaluation_note": "Metrics calculated on synthetically generated test data. Real-world performance may differ."
                },
                "test_set_details": {
                    "test_size": "20% of training data (600 samples)",
                    "train_size": "80% of training data (2,400 samples)",
                    "stratification": "Stratified train/test split to maintain class balance",
                    "metrics_included": [
                        "Classification accuracy",
                        "Precision, Recall, F1-Score",
                        "Confusion matrix"
                    ]
                },
                "model_statistics": {
                    "total_features": "150",
                    "non_zero_coefficients": "137 (91.3% of features)",
                    "interpretation": "High feature utilization indicates model is learning meaningful patterns"
                }
            },
            "known_limitations": {
                "training_data_limitations": {
                    "issue": "Model trained on synthetic data, not real user-career matches",
                    "impact": "Performance on real user data may differ from test metrics",
                    "mitigation": [
                        "Model architecture allows for retraining with real user feedback data",
                        "Baseline similarity model available as fallback",
                        "Confidence scores provided to indicate prediction certainty"
                    ]
                },
                "coverage_limitations": {
                    "issue": "Limited to 150 occupations in filtered catalog",
                    "impact": "Recommendations may not include all relevant careers",
                    "mitigation": [
                        "Filtered catalog prioritizes occupations with complete data",
                        "Catalog can be expanded as more occupations meet quality criteria",
                        "Baseline similarity works with full O*NET dataset when needed"
                    ]
                },
                "data_quality_limitations": {
                    "issue": "BLS projections are national-level, not regional",
                    "impact": "Regional job market variations not reflected in recommendations",
                    "mitigation": [
                        "Users can specify location preferences in constraints",
                        "Recommendations include confidence scores indicating data completeness",
                        "Outlook analysis clearly states geographic scope limitations"
                    ]
                },
                "temporal_limitations": {
                    "issue": "Data reflects 2024 baseline, projections cover 2024-2034",
                    "impact": "Cannot predict beyond 2034 or account for unexpected disruptions",
                    "mitigation": [
                        "Clear documentation of projection time horizon",
                        "Outlook analysis includes confidence assessments",
                        "Recommendations emphasize data currency limitations"
                    ]
                },
                "model_assumptions": {
                    "issue": "Model assumes linear relationships and stable skill requirements",
                    "impact": "May not capture non-linear trends or rapidly changing skill needs",
                    "mitigation": [
                        "Model can be retrained with updated data",
                        "Baseline similarity provides alternative ranking method",
                        "Recommendations include explanation of top contributing features"
                    ]
                }
            },
            "mitigation_steps": {
                "model_improvement": [
                    "Model architecture supports retraining with real user feedback data",
                    "Synthetic training data generation can be enhanced with more realistic patterns",
                    "Hyperparameter tuning can be performed as more data becomes available"
                ],
                "transparency": [
                    "Model cards (this endpoint) provide detailed information about model capabilities",
                    "Recommendations include confidence scores and explanation of top features",
                    "Trust panel documents all limitations and data usage policies"
                ],
                "fallback_mechanisms": [
                    "Baseline cosine similarity model available when ML model fails",
                    "Recommendations can work with limited input (skills-only mode)",
                    "System gracefully degrades when model artifacts are unavailable"
                ],
                "data_quality": [
                    "Filtered catalog ensures high data completeness for included occupations",
                    "Data dictionary documents all data sources and quality metrics",
                    "Version tracking allows monitoring of data and model updates"
                ]
            }
        }
    )


# Export wrapper function for backward compatibility with main.py
async def get_model_cards():
    """Wrapper for backward compatibility"""
    return await get_model_cards_data()


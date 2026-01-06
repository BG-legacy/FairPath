"""
Simple test: Just shows the training process and user data
Keeping it straightforward - no fancy stuff, just the basics
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.recommendation_service import CareerRecommendationService
from services.data_processing import DataProcessingService


def show_training_data():
    """Show what the training data looks like"""
    print("="*80)
    print(" TRAINING DATA OVERVIEW")
    print("="*80)
    print()
    
    service = CareerRecommendationService()
    processed_data = service.load_processed_data()
    
    print("What we're training on:")
    print(f"  - Number of occupations: {len(processed_data['occupations'])}")
    print(f"  - Number of unique skills: {len(processed_data['skill_names'])}")
    print()
    
    print("Sample skills in the data:")
    for i, skill in enumerate(processed_data['skill_names'][:10], 1):
        print(f"  {i}. {skill}")
    print(f"  ... and {len(processed_data['skill_names']) - 10} more")
    print()
    
    print("Sample occupations:")
    for i, occ in enumerate(processed_data['occupations'][:5], 1):
        print(f"  {i}. {occ['name']}")
        print(f"     SOC Code: {occ['soc_code']}")
        outlook = occ.get('outlook_features', {})
        if outlook.get('median_wage_2024'):
            print(f"     Median Wage: ${outlook['median_wage_2024']:,.0f}/year")
        print()
    
    print("="*80)
    print()


def show_user_data_example():
    """Show what user input data looks like"""
    print("="*80)
    print(" USER DATA EXAMPLE")
    print("="*80)
    print()
    
    service = CareerRecommendationService()
    
    print("Example user profile:")
    print()
    print("Skills:")
    skills = ["Programming", "Mathematics", "Critical Thinking", "Systems Analysis"]
    for skill in skills:
        print(f"  - {skill}")
    print()
    
    print("Interests (RIASEC scale 0-7):")
    interests = {"Investigative": 7.0, "Enterprising": 5.0, "Realistic": 4.0}
    for interest, score in interests.items():
        print(f"  - {interest}: {score}")
    print()
    
    print("Work Values:")
    values = {"Achievement": 6.0, "Recognition": 5.0}
    for value, score in values.items():
        print(f"  - {value}: {score}")
    print()
    
    print("Constraints:")
    constraints = {"min_wage": 60000, "max_education_level": 3}
    print(f"  - Minimum wage: ${constraints['min_wage']:,}/year")
    print(f"  - Max education: Bachelor's level")
    print()
    
    print("Converting to feature vector...")
    user_features = service.build_user_feature_vector(
        skills=skills,
        interests=interests,
        work_values=values,
        constraints=constraints
    )
    
    print(f"  - Feature vector length: {len(user_features['combined_vector'])}")
    print(f"  - Skills portion: {len(user_features['skill_vector'])} features")
    print(f"  - Interests portion: {len(user_features['interest_vector'])} features")
    print(f"  - Values portion: {len(user_features['values_vector'])} features")
    print(f"  - Constraints portion: {len(user_features['constraint_features'])} features")
    print()
    
    print("Sample feature values:")
    combined = np.array(user_features['combined_vector'])
    non_zero = np.nonzero(combined)[0]
    print(f"  - Non-zero features: {len(non_zero)} out of {len(combined)}")
    print(f"  - Sample non-zero indices: {non_zero[:5].tolist()}")
    print()
    
    print("="*80)
    print()


def show_training_process():
    """Show the training process"""
    print("="*80)
    print(" TRAINING PROCESS")
    print("="*80)
    print()
    
    print("Step 1: Generate synthetic training data")
    print("  - Create 3,000 user-career pairs")
    print("  - Label them as good match (1) or bad match (0)")
    print("  - Use different match types for realism")
    print()
    
    print("Step 2: Feature engineering")
    print("  - For each pair, create feature vector:")
    print("    * User vector (skills, interests, values, constraints)")
    print("    * Career vector (same structure)")
    print("    * Difference vector (user - career)")
    print("  - Total: 150 features per training example")
    print()
    
    print("Step 3: Split data")
    print("  - Training set: 2,400 samples (80%)")
    print("  - Test set: 600 samples (20%)")
    print()
    
    print("Step 4: Scale features")
    print("  - Use StandardScaler to normalize")
    print("  - Mean = 0, Std = 1")
    print("  - Helps model learn better")
    print()
    
    print("Step 5: Train model")
    print("  - Algorithm: Logistic Regression")
    print("  - Solver: L-BFGS")
    print("  - Max iterations: 1000")
    print("  - Model learns 150 coefficients")
    print()
    
    print("Step 6: Evaluate")
    print("  - Training accuracy: ~78%")
    print("  - Test accuracy: ~78%")
    print("  - Good generalization (not overfitted)")
    print()
    
    print("Step 7: Save model")
    print("  - Save model to artifacts/models/career_model_v1.0.0.pkl")
    print("  - Save scaler to artifacts/models/scaler_v1.0.0.pkl")
    print("  - Save metadata to artifacts/models/model_metadata_v1.0.0.json")
    print()
    
    print("="*80)
    print()


def show_model_details():
    """Show what the trained model looks like"""
    print("="*80)
    print(" TRAINED MODEL DETAILS")
    print("="*80)
    print()
    
    service = CareerRecommendationService()
    loaded = service.load_model_artifacts()
    
    if not loaded:
        print("Model not found. Run training first:")
        print("  python3 scripts/train_recommendation_model_production.py")
        print()
        return
    
    model = service.ml_model
    
    print("Model Information:")
    print(f"  - Type: {type(model).__name__}")
    print(f"  - Features: {model.n_features_in_}")
    print(f"  - Classes: {len(model.classes_)}")
    print()
    
    if hasattr(model, 'coef_'):
        coef = model.coef_[0]
        print("Coefficients:")
        print(f"  - Total: {len(coef)}")
        print(f"  - Non-zero: {np.count_nonzero(coef)} ({np.count_nonzero(coef)/len(coef)*100:.1f}%)")
        print(f"  - Mean: {coef.mean():.6f}")
        print(f"  - Std: {coef.std():.6f}")
        print(f"  - Min: {coef.min():.6f}")
        print(f"  - Max: {coef.max():.6f}")
        print()
    
    if hasattr(model, 'intercept_'):
        print(f"Intercept: {model.intercept_[0]:.6f}")
        print()
    
    print("Scaler Information:")
    if service.scaler:
        print("  - Type: StandardScaler")
        print("  - Normalizes features to mean=0, std=1")
    else:
        print("  - No scaler found")
    print()
    
    print("="*80)
    print()


def main():
    """Run the simple test"""
    print("\n" + "="*80)
    print(" SIMPLE TRAINING AND USER DATA TEST")
    print("="*80)
    print()
    
    # Show training data
    show_training_data()
    
    # Show user data example
    show_user_data_example()
    
    # Show training process
    show_training_process()
    
    # Show model details
    show_model_details()
    
    print("="*80)
    print(" TEST COMPLETE")
    print("="*80)
    print()
    print("This shows:")
    print("  1. What data we're training on")
    print("  2. How user input is converted to features")
    print("  3. The training process step-by-step")
    print("  4. What the trained model looks like")
    print()
    print("="*80 + "\n")


if __name__ == "__main__":
    main()




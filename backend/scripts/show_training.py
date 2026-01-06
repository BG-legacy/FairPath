"""
Detailed training visualization - shows step-by-step what happens during ML training
"""
import numpy as np
from pathlib import Path
import sys
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.recommendation_service import CareerRecommendationService


def show_training_process():
    """Show detailed training process"""
    
    print("="*100)
    print("ML MODEL TRAINING PROCESS")
    print("="*100)
    print()
    
    # Initialize service
    print("STEP 1: Initializing Services")
    print("-" * 100)
    service = CareerRecommendationService()
    processed_data = service.load_processed_data()
    occupation_vectors = service.build_occupation_vectors()
    
    print(f"  - Loaded {len(processed_data['occupations'])} occupations")
    print(f"  - Found {len(processed_data['skill_names'])} unique skills")
    print(f"  - Built feature vectors for all occupations")
    print()
    
    # Generate training data
    print("STEP 2: Generating Training Data")
    print("-" * 100)
    num_samples = 2000
    print(f"  - Generating {num_samples} synthetic training samples...")
    print("  - Strategy: Create user-career pairs where similar vectors = good match (label 1)")
    print("            and different vectors = bad match (label 0)")
    print()
    
    np.random.seed(42)
    random.seed(42)
    
    X = []
    y = []
    careers_list = list(occupation_vectors.keys())
    
    positive_count = 0
    negative_count = 0
    
    for i in range(num_samples):
        target_career_id = random.choice(careers_list)
        target_vector = occupation_vectors[target_career_id]
        
        is_positive = random.random() > 0.5
        
        if is_positive:
            # Positive: user similar to career
            noise = np.random.normal(0, 0.1, size=target_vector.shape)
            user_vector = np.clip(target_vector + noise, 0, 1)
            positive_count += 1
        else:
            # Negative: user different from career
            user_vector = np.random.random(size=target_vector.shape)
            negative_count += 1
        
        # Feature vector: [user_vector, career_vector, difference]
        feature_vector = np.concatenate([
            user_vector,
            target_vector,
            user_vector - target_vector
        ])
        
        X.append(feature_vector)
        y.append(1 if is_positive else 0)
    
    X = np.array(X)
    y = np.array(y)
    
    print(f"  - Generated {len(X)} samples")
    print(f"  - Positive samples (good match): {positive_count}")
    print(f"  - Negative samples (bad match): {negative_count}")
    print(f"  - Feature vector dimension: {X.shape[1]} (user + career + difference)")
    print(f"  - Each feature vector contains:")
    print(f"      * User skills/interests/values: {len(user_vector)} features")
    print(f"      * Career skills/interests/values: {len(target_vector)} features")
    print(f"      * Difference vector: {len(user_vector)} features")
    print()
    
    # Split data
    print("STEP 3: Splitting Data")
    print("-" * 100)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"  - Training set: {len(X_train)} samples ({len(X_train)/len(X)*100:.1f}%)")
    print(f"  - Test set: {len(X_test)} samples ({len(X_test)/len(X)*100:.1f}%)")
    print(f"  - Using stratified split to maintain class balance")
    print()
    
    # Scale features
    print("STEP 4: Feature Scaling")
    print("-" * 100)
    print("  - Scaling features using StandardScaler (mean=0, std=1)")
    print("  - Why? Helps logistic regression converge faster and more accurately")
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"  - Training data before scaling: mean={X_train.mean():.4f}, std={X_train.std():.4f}")
    print(f"  - Training data after scaling: mean={X_train_scaled.mean():.4f}, std={X_train_scaled.std():.4f}")
    print()
    
    # Train model
    print("STEP 5: Training Logistic Regression Model")
    print("-" * 100)
    print("  - Algorithm: Logistic Regression (binary classifier)")
    print("  - Solver: L-BFGS (Limited-memory Broyden-Fletcher-Goldfarb-Shanno)")
    print("  - Max iterations: 1000")
    print("  - Random state: 42 (for reproducibility)")
    print()
    print("  Training in progress...")
    
    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
        solver='lbfgs'
    )
    
    model.fit(X_train_scaled, y_train)
    
    print("  - Training complete!")
    print()
    
    # Model details
    print("STEP 6: Model Details")
    print("-" * 100)
    print(f"  - Model type: {type(model).__name__}")
    print(f"  - Number of features: {model.n_features_in_}")
    print(f"  - Number of classes: {len(model.classes_)}")
    
    if hasattr(model, 'coef_'):
        coef = model.coef_[0]
        print(f"  - Number of coefficients: {len(coef)}")
        print(f"  - Coefficient statistics:")
        print(f"      Mean: {coef.mean():.6f}")
        print(f"      Std: {coef.std():.6f}")
        print(f"      Min: {coef.min():.6f}")
        print(f"      Max: {coef.max():.6f}")
        print(f"      Non-zero: {np.count_nonzero(coef)} ({np.count_nonzero(coef)/len(coef)*100:.1f}%)")
    
    if hasattr(model, 'intercept_'):
        print(f"  - Intercept: {model.intercept_[0]:.6f}")
    print()
    
    # Evaluate
    print("STEP 7: Model Evaluation")
    print("-" * 100)
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"  - Training accuracy: {train_score:.4f} ({train_score*100:.2f}%)")
    print(f"  - Test accuracy: {test_score:.4f} ({test_score*100:.2f}%)")
    
    # Get predictions for analysis
    train_pred = model.predict(X_train_scaled)
    test_pred = model.predict(X_test_scaled)
    
    train_pos_pred = np.sum((train_pred == 1) & (y_train == 1))
    train_neg_pred = np.sum((train_pred == 0) & (y_train == 0))
    test_pos_pred = np.sum((test_pred == 1) & (y_test == 1))
    test_neg_pred = np.sum((test_pred == 0) & (y_test == 0))
    
    print()
    print("  - Training set predictions:")
    print(f"      Correct positive predictions: {train_pos_pred}/{np.sum(y_train == 1)}")
    print(f"      Correct negative predictions: {train_neg_pred}/{np.sum(y_train == 0)}")
    print("  - Test set predictions:")
    print(f"      Correct positive predictions: {test_pos_pred}/{np.sum(y_test == 1)}")
    print(f"      Correct negative predictions: {test_neg_pred}/{np.sum(y_test == 0)}")
    print()
    
    # Save model
    print("STEP 8: Saving Model Artifacts")
    print("-" * 100)
    service.save_model_artifacts(
        model=model,
        scaler=scaler,
        vectorizer=None,
        version="1.0.0"
    )
    
    print("  - Model saved to: artifacts/models/career_model_v1.0.0.pkl")
    print("  - Scaler saved to: artifacts/models/scaler_v1.0.0.pkl")
    print("  - Metadata saved to: artifacts/models/model_metadata_v1.0.0.json")
    print()
    
    # Summary
    print("="*100)
    print("TRAINING SUMMARY")
    print("="*100)
    print()
    print("What was learned:")
    print("  - The model learned to distinguish between good and bad user-career matches")
    print("  - It learned patterns in 150-dimensional feature space")
    print("  - It can predict match probability for new user-career pairs")
    print()
    print("How it works:")
    print("  1. User provides skills, interests, values")
    print("  2. System builds feature vector (same format as training)")
    print("  3. Model predicts probability of good match (0-1)")
    print("  4. Higher probability = better career recommendation")
    print()
    print("Model characteristics:")
    print(f"  - {model.n_features_in_} features analyzed")
    print(f"  - {np.count_nonzero(model.coef_[0])} non-zero coefficients (learned patterns)")
    print(f"  - {test_score*100:.2f}% accuracy on unseen test data")
    print()
    print("="*100)


if __name__ == "__main__":
    show_training_process()


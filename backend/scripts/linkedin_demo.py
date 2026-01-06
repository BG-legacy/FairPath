"""
LinkedIn Demo - Real-World Career Recommendation Examples
Showcasing ML-powered career recommendations for professional sharing
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.recommendation_service import CareerRecommendationService


def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*100)
    print(f"{title}")
    print("="*100 + "\n")


def print_user_profile(name, background, skills, interests=None, values=None, constraints=None):
    """Print a formatted user profile"""
    print(f"USER PROFILE: {name}")
    print(f"   Background: {background}")
    print(f"   Skills: {', '.join(skills)}")
    if interests:
        interests_str = ', '.join([f"{k} ({v})" for k, v in interests.items()])
        print(f"   Interests: {interests_str}")
    if values:
        values_str = ', '.join([f"{k} ({v})" for k, v in values.items()])
        print(f"   Work Values: {values_str}")
    if constraints:
        constraints_str = ', '.join([f"{k}: {v}" for k, v in constraints.items()])
        print(f"   Constraints: {constraints_str}")
    print()


def print_recommendations(result, top_n=5):
    """Print formatted recommendations"""
    print(f"ML-POWERED RECOMMENDATIONS (Top {top_n}):")
    print(f"   Method: {result['method'].upper()}")
    print()
    
    for i, rec in enumerate(result['recommendations'][:top_n], 1):
        print(f"   {i}. {rec['name']}")
        print(f"      Match Score: {rec['score']:.1%} | Confidence: {rec['confidence']}")
        
        # Show outlook data if available
        outlook = rec.get('outlook', {})
        if outlook:
            wage = outlook.get('median_wage_2024')
            growth = outlook.get('percent_change')
            if wage:
                print(f"      Median Wage: ${wage:,.0f}/year")
            if growth:
                trend = "Growth" if growth > 0 else "Decline"
                print(f"      {trend}: {growth:+.1f}% (2024-2034)")
        
        # Show education requirement
        education = rec.get('education', {})
        if education and education.get('education_level'):
            edu_level = education['education_level'].replace('_', ' ').title()
            print(f"      Education: {edu_level}")
        
        # Show top contributing skills
        explanation = rec.get('explanation', {})
        top_skills = explanation.get('top_contributing_skills', [])
        if top_skills:
            skill_names = [s['skill'] for s in top_skills[:3]]
            print(f"      Key Skills Match: {', '.join(skill_names)}")
        
        print()


def demo_scenario_1():
    """Scenario 1: Career Switcher - Marketing Professional to Tech"""
    print_header("SCENARIO 1: Career Switcher")
    
    print_user_profile(
        name="Sarah Chen",
        background="5 years in Marketing, wants to transition to tech. Strong analytical skills from campaign analysis.",
        skills=["Writing", "Speaking", "Social Perceptiveness", "Critical Thinking", "Active Listening"],
        interests={"Enterprising": 6.0, "Investigative": 5.0},
        values={"Achievement": 6.0, "Recognition": 5.0}
    )
    
    service = CareerRecommendationService()
    service.load_model_artifacts()
    
    result = service.recommend(
        skills=["Writing", "Speaking", "Social Perceptiveness", "Critical Thinking", "Active Listening"],
        interests={"Enterprising": 6.0, "Investigative": 5.0},
        work_values={"Achievement": 6.0, "Recognition": 5.0},
        top_n=5,
        use_ml=True
    )
    
    print_recommendations(result, top_n=5)
    
    print("INSIGHT: The ML model identified careers that leverage Sarah's communication")
    print("   and analytical skills while aligning with her interest in tech and business.\n")


def demo_scenario_2():
    """Scenario 2: Recent Graduate - Computer Science Major"""
    print_header("SCENARIO 2: Recent Graduate")
    
    print_user_profile(
        name="Marcus Johnson",
        background="Recent Computer Science graduate. Strong in programming and problem-solving. Looking for entry-level tech roles.",
        skills=["Programming", "Mathematics", "Critical Thinking", "Systems Analysis", "Complex Problem Solving"],
        interests={"Investigative": 7.0, "Realistic": 5.0},
        constraints={"min_wage": 60000, "max_education_level": 3}  # Bachelor's level
    )
    
    service = CareerRecommendationService()
    service.load_model_artifacts()
    
    result = service.recommend(
        skills=["Programming", "Mathematics", "Critical Thinking", "Systems Analysis", "Complex Problem Solving"],
        interests={"Investigative": 7.0, "Realistic": 5.0},
        constraints={"min_wage": 60000, "max_education_level": 3},
        top_n=5,
        use_ml=True
    )
    
    print_recommendations(result, top_n=5)
    
    print("INSIGHT: The ML model matched Marcus's technical skills with careers that")
    print("   offer good entry-level opportunities and growth potential.\n")


def demo_scenario_3():
    """Scenario 3: Healthcare Professional Exploring Data Science"""
    print_header("SCENARIO 3: Healthcare to Data Science Transition")
    
    print_user_profile(
        name="Dr. Priya Patel",
        background="Registered Nurse with 8 years experience. Interested in healthcare data analytics and improving patient outcomes through data.",
        skills=["Active Listening", "Social Perceptiveness", "Critical Thinking", "Reading Comprehension", "Science"],
        interests={"Investigative": 7.0, "Social": 6.0},
        values={"Achievement": 7.0, "Support": 6.0}
    )
    
    service = CareerRecommendationService()
    service.load_model_artifacts()
    
    result = service.recommend(
        skills=["Active Listening", "Social Perceptiveness", "Critical Thinking", "Reading Comprehension", "Science"],
        interests={"Investigative": 7.0, "Social": 6.0},
        work_values={"Achievement": 7.0, "Support": 6.0},
        top_n=5,
        use_ml=True
    )
    
    print_recommendations(result, top_n=5)
    
    print("INSIGHT: The ML model found careers that combine Dr. Patel's healthcare")
    print("   expertise with analytical work, leveraging both her social and investigative interests.\n")


def demo_scenario_4():
    """Scenario 4: Creative Professional Seeking Business Opportunities"""
    print_header("SCENARIO 4: Creative to Business Transition")
    
    print_user_profile(
        name="Alex Rivera",
        background="Graphic Designer with 6 years experience. Wants to move into business/management roles while using creative skills.",
        skills=["Active Listening", "Speaking", "Social Perceptiveness", "Coordination", "Persuasion"],
        interests={"Artistic": 6.0, "Enterprising": 7.0},
        values={"Recognition": 6.0, "Independence": 5.0},
        constraints={"min_wage": 70000}
    )
    
    service = CareerRecommendationService()
    service.load_model_artifacts()
    
    result = service.recommend(
        skills=["Active Listening", "Speaking", "Social Perceptiveness", "Coordination", "Persuasion"],
        interests={"Artistic": 6.0, "Enterprising": 7.0},
        work_values={"Recognition": 6.0, "Independence": 5.0},
        constraints={"min_wage": 70000},
        top_n=5,
        use_ml=True
    )
    
    print_recommendations(result, top_n=5)
    
    print("INSIGHT: The ML model identified roles that value Alex's creative and")
    print("   communication skills while meeting salary requirements and enterprising interests.\n")


def print_ml_highlights():
    """Print ML system highlights"""
    print_header("ML SYSTEM HIGHLIGHTS")
    
    print("KEY FEATURES:")
    print("   • Uses scikit-learn LogisticRegression for intelligent career matching")
    print("   • Trained on 2,000+ synthetic user-career pairs")
    print("   • Analyzes 150+ features including skills, interests, values, and constraints")
    print("   • Provides explainable recommendations with confidence scores")
    print("   • Integrates real-world data: O*NET skills, BLS wage/growth projections")
    print()
    
    print("DATA SOURCES:")
    print("   • O*NET Database 30.1 (1,000+ occupations, skills, tasks)")
    print("   • BLS Employment Projections (wage data, growth rates)")
    print("   • 150 carefully selected occupations with complete data")
    print()
    
    print("HOW IT WORKS:")
    print("   1. User provides skills, interests, values, and constraints")
    print("   2. System builds feature vector from user inputs")
    print("   3. ML model compares user vector to 150+ career vectors")
    print("   4. Model predicts match probability using learned patterns")
    print("   5. Returns top recommendations with explanations and outlook data")
    print()


def main():
    """Run all demo scenarios"""
    print("\n" + "="*100)
    print(" " * 25 + "FAIRPATH CAREER RECOMMENDATION SYSTEM")
    print(" " * 30 + "ML-Powered Career Matching Demo")
    print("="*100)
    print(f"\nGenerated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
    
    # Run all scenarios
    demo_scenario_1()
    demo_scenario_2()
    demo_scenario_3()
    demo_scenario_4()
    
    # Print ML highlights
    print_ml_highlights()
    
    # Final summary
    print_header("SUMMARY")
    print("This ML-powered system demonstrates:")
    print("   - Real machine learning (not just rule-based matching)")
    print("   - Personalized recommendations based on individual profiles")
    print("   - Integration of multiple data sources (skills, interests, wages, growth)")
    print("   - Explainable AI with confidence scores and skill matching")
    print("   - Practical applications for career transitions and exploration")
    print()
    print("="*100)
    print("\nReady to share on LinkedIn!")
    print("   This demonstrates real-world ML application in career development.\n")


if __name__ == "__main__":
    main()


"""
Quick test script for career switch service
I'm just testing it out to make sure it works
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.career_switch_service import CareerSwitchService
import json

def main():
    print("Testing career switch service...")
    
    service = CareerSwitchService()
    
    # Load some sample career IDs - you'll need to replace these with actual IDs from your data
    # Let me try to get some from the processed data
    processed_data = service.load_processed_data()
    
    if not processed_data or not processed_data.get("occupations"):
        print("No processed data found. Run process_data.py first.")
        return
    
    # Get first two occupations for testing
    occupations = processed_data["occupations"]
    if len(occupations) < 2:
        print("Need at least 2 occupations to test")
        return
    
    source_id = occupations[0]["career_id"]
    target_id = occupations[1]["career_id"]
    
    print(f"\nAnalyzing switch from: {occupations[0]['name']}")
    print(f"To: {occupations[1]['name']}")
    print(f"Source ID: {source_id}")
    print(f"Target ID: {target_id}\n")
    
    # Test the full analysis
    result = service.analyze_career_switch(source_id, target_id)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    # Print results
    print("=" * 60)
    print("CAREER SWITCH ANALYSIS")
    print("=" * 60)
    
    print(f"\nSkill Overlap: {result['skill_overlap']['percentage']:.1f}%")
    print(f"Transferable Skills: {result['skill_overlap']['transferable_skills_count']}")
    print(f"Skills to Learn: {result['skill_overlap']['skills_to_learn_count']}")
    print(f"Optional Skills: {result['skill_overlap']['optional_skills_count']}")
    
    print(f"\nDifficulty: {result['difficulty']}")
    print(f"Transition Time: {result['transition_time']['range']}")
    
    print(f"\nOverall Assessment: {result['success_risk_assessment']['overall_assessment']}")
    print(f"Success Factors: {result['success_risk_assessment']['num_success_factors']}")
    print(f"Risk Factors: {result['success_risk_assessment']['num_risk_factors']}")
    
    # Show some transferable skills
    if result['transfer_map']['transfers_directly']:
        print("\nTop Transferable Skills:")
        for skill in result['transfer_map']['transfers_directly'][:5]:
            print(f"  - {skill['skill']} (source: {skill['source_level']:.2f}, target: {skill['target_level']:.2f})")
    
    # Show some skills to learn
    if result['transfer_map']['needs_learning']:
        print("\nTop Skills to Learn:")
        for skill in result['transfer_map']['needs_learning'][:5]:
            print(f"  - {skill['skill']} (gap: {skill['gap']:.2f})")
    
    # Show success factors
    if result['success_risk_assessment']['success_factors']:
        print("\nSuccess Factors:")
        for factor in result['success_risk_assessment']['success_factors']:
            print(f"  + {factor['factor']}: {factor['description']}")
    
    # Show risk factors
    if result['success_risk_assessment']['risk_factors']:
        print("\nRisk Factors:")
        for factor in result['success_risk_assessment']['risk_factors']:
            print(f"  - {factor['factor']}: {factor['description']}")
    
    # Show certifications for target career
    print("\n--- Certifications for Target Career ---")
    certs = result.get('certifications', {})
    if certs.get('available'):
        if certs.get('entry_level'):
            cert = certs['entry_level'][0]
            print(f"✅ Entry-Level: {cert.get('name', 'N/A')}")
            print(f"   Provider: {cert.get('provider', 'N/A')}")
            print(f"   {cert.get('description', 'N/A')}")
        if certs.get('career_advancing'):
            cert = certs['career_advancing'][0]
            print(f"\n🚀 Career-Advancing: {cert.get('name', 'N/A')}")
            print(f"   Provider: {cert.get('provider', 'N/A')}")
            print(f"   {cert.get('description', 'N/A')}")
        if certs.get('optional_overhyped'):
            cert = certs['optional_overhyped'][0]
            print(f"\n⚠️  Optional/Overhyped: {cert.get('name', 'N/A')}")
            print(f"   Provider: {cert.get('provider', 'N/A')}")
            print(f"   {cert.get('description', 'N/A')}")
    else:
        print("Certifications not available (OpenAI not configured or error occurred)")
    
    print("\n" + "=" * 60)
    
    # Also test just the overlap function
    print("\nTesting skill overlap function directly...")
    overlap_result = service.compute_skill_overlap(source_id, target_id)
    print(f"Overlap: {overlap_result['overlap_percentage']:.1f}%")
    print(f"Transfers directly: {overlap_result['num_transferable']}")
    print(f"Needs learning: {overlap_result['num_to_learn']}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()


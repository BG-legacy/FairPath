"""
Quick test script for outlook service
I'm just testing it out to make sure it works
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.outlook_service import OutlookService


def main():
    print("Testing outlook service...")
    
    service = OutlookService()
    
    # Load some sample career IDs
    processed_data = service.load_processed_data()
    
    if not processed_data or not processed_data.get("occupations"):
        print("No processed data found. Run process_data.py first.")
        return
    
    # Get a few occupations for testing
    occupations = processed_data["occupations"]
    if len(occupations) < 1:
        print("Need at least 1 occupation to test")
        return
    
    # Test with first occupation
    test_career_id = occupations[0]["career_id"]
    test_name = occupations[0]["name"]
    
    print(f"\nAnalyzing outlook for: {test_name}")
    print(f"Career ID: {test_career_id}\n")
    
    # Test the full analysis
    result = service.analyze_outlook(test_career_id)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    # Print results
    print("=" * 60)
    print("5-10 YEAR OUTLOOK ANALYSIS")
    print("=" * 60)
    
    print(f"\nCareer: {result['career']['name']}")
    print(f"Career ID: {result['career']['career_id']}")
    
    print(f"\n--- Growth Outlook ---")
    print(f"Outlook: {result['growth_outlook']['outlook']}")
    print(f"Confidence: {result['growth_outlook']['confidence']}")
    print(f"Reasoning: {result['growth_outlook']['reasoning']}")
    
    print(f"\n--- Automation Risk ---")
    print(f"Risk Level: {result['automation_risk']['risk']}")
    print(f"Confidence: {result['automation_risk']['confidence']}")
    print(f"Reasoning: {result['automation_risk']['reasoning']}")
    
    print(f"\n--- Stability Signal ---")
    print(f"Signal: {result['stability_signal']['signal']}")
    print(f"Confidence: {result['stability_signal']['confidence']}")
    print(f"Reasoning: {result['stability_signal']['reasoning']}")
    
    print(f"\n--- Overall Confidence ---")
    print(f"Level: {result['confidence']['level']}")
    print(f"Why: {result['confidence']['why']}")
    
    print(f"\n--- Data Quality ---")
    print(f"Has BLS Data: {result['data_quality']['has_bls_data']}")
    print(f"Has Task Data: {result['data_quality']['has_task_data']}")
    print(f"Completeness: {result['data_quality']['completeness']}")
    
    print(f"\n--- Raw Metrics ---")
    raw = result['raw_metrics']
    print(f"Growth Rate: {raw.get('growth_rate', 'N/A')}%")
    print(f"Employment 2024: {raw.get('employment_2024', 'N/A'):,}" if raw.get('employment_2024') else "Employment 2024: N/A")
    print(f"Employment 2034: {raw.get('employment_2034', 'N/A'):,}" if raw.get('employment_2034') else "Employment 2034: N/A")
    print(f"Annual Openings: {raw.get('annual_openings', 'N/A'):,}" if raw.get('annual_openings') else "Annual Openings: N/A")
    print(f"Automation Proxy: {raw.get('automation_proxy', 'N/A'):.3f}" if raw.get('automation_proxy') else "Automation Proxy: N/A")
    
    print(f"\n--- Certifications That Matter ---")
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
    
    print(f"\n--- Assumptions & Limitations ---")
    assumptions = result['assumptions_and_limitations']
    print(f"\nDataset Coverage:")
    for key, value in assumptions['dataset_coverage'].items():
        print(f"  {key}: {value}")
    
    print(f"\nAssumptions:")
    for assumption in assumptions['assumptions']:
        print(f"  - {assumption}")
    
    print(f"\nLimitations:")
    for limitation in assumptions['limitations']:
        print(f"  - {limitation}")
    
    print("\n" + "=" * 60)
    
    # Test with a few more occupations if available
    if len(occupations) > 1:
        print("\n\nTesting with additional occupations...")
        for i, occ in enumerate(occupations[1:4], 1):  # Test up to 3 more
            print(f"\n{i}. {occ['name']} ({occ['career_id']})")
            result = service.analyze_outlook(occ['career_id'])
            if "error" not in result:
                print(f"   Growth: {result['growth_outlook']['outlook']}")
                print(f"   Automation Risk: {result['automation_risk']['risk']}")
                print(f"   Stability: {result['stability_signal']['signal']}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()



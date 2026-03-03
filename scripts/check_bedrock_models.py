"""
Script to check which Bedrock models we have access to
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.bedrock_model_checker import print_available_models, get_available_models, get_recommended_models_for_task

if __name__ == "__main__":
    print("Checking your Bedrock model access...")
    print()
    
    # Get region from environment or use default
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    print(f"Region: {region}")
    print()
    
    try:
        print_available_models(region=region)
        
        # Also save recommendations to a config suggestion
        print()
        print("=" * 70)
        print("CONFIGURATION SUGGESTIONS")
        print("=" * 70)
        
        translation_models = get_recommended_models_for_task("translation", region)
        summarization_models = get_recommended_models_for_task("summarization", region)
        
        if translation_models and summarization_models:
            print()
            print("Add these to your .env file:")
            print()
            print(f"BEDROCK_TRANSLATION_MODEL={translation_models[0]}")
            print(f"BEDROCK_SUMMARIZATION_MODEL={summarization_models[0]}")
            print()
            print("Or use the first available model from each category:")
            print(f"  Translation: {translation_models[0]}")
            print(f"  Summarization: {summarization_models[0]}")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


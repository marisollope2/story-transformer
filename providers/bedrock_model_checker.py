"""
Bedrock Model Access Checker
Checks which models are available in your AWS Bedrock account
"""
import boto3
import os
from typing import List, Dict, Optional
from botocore.config import Config
from botocore.exceptions import ClientError


def get_bedrock_client(region_name: Optional[str] = None):
    """Get Bedrock client for checking model access"""
    region = region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    config = Config(
        retries={
            'max_attempts': 3,
            'mode': 'standard'
        }
    )
    return boto3.client('bedrock', region_name=region, config=config)


def get_available_models(region: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Get list of all available foundation models in your Bedrock account.
    
    Returns:
        Dictionary with model categories and their model IDs
    """
    client = get_bedrock_client(region_name=region)
    
    try:
        response = client.list_foundation_models()
        models = response.get('modelSummaries', [])
        
        # Organize by provider
        organized = {
            'openai': [],
            'amazon': [],
            'meta': [],
            'cohere': [],
            'mistral': [],
            'ai21': [],
            'stability': [],
            'other': []
        }
        
        for model in models:
            model_id = model.get('modelId', '')
            provider = model.get('providerName', '').lower()
            
            # Only include ACTIVE models
            lifecycle = model.get('modelLifecycle', {})
            if lifecycle.get('status') != 'ACTIVE':
                continue
            
            if 'openai' in provider or 'gpt-oss' in model_id.lower():
                organized['openai'].append(model_id)
            elif 'amazon' in provider or 'nova' in model_id.lower() or 'titan' in model_id.lower():
                organized['amazon'].append(model_id)
            elif 'meta' in provider or 'llama' in model_id.lower():
                organized['meta'].append(model_id)
            elif 'cohere' in provider:
                organized['cohere'].append(model_id)
            elif 'mistral' in provider:
                organized['mistral'].append(model_id)
            elif 'ai21' in provider or 'jamba' in model_id.lower():
                organized['ai21'].append(model_id)
            elif 'stability' in provider:
                organized['stability'].append(model_id)
            else:
                organized['other'].append(model_id)
        
        return organized
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'AccessDeniedException':
            raise Exception("Access denied. Make sure you have permissions to list Bedrock models.")
        else:
            raise Exception(f"Error checking model access: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to check available models: {str(e)}")


def check_model_access(model_id: str, region: Optional[str] = None) -> bool:
    """
    Check if a specific model is available in your account.
    
    Args:
        model_id: Model ID to check (e.g., 'openai.gpt-oss-120b-1:0')
        region: AWS region (optional)
    
    Returns:
        True if model is available, False otherwise
    """
    try:
        available = get_available_models(region=region)
        all_models = []
        for category in available.values():
            all_models.extend(category)
        return model_id in all_models
    except Exception:
        return False


def get_recommended_models_for_task(
    task: str = "translation",
    region: Optional[str] = None
) -> List[str]:
    """
    Get recommended models for a specific task from your available models.
    
    Args:
        task: 'translation' or 'summarization'
        region: AWS region (optional)
    
    Returns:
        List of recommended model IDs that you have access to
    """
    available = get_available_models(region=region)
    
    if task == "translation":
        # Priority order for translation models
        priority_models = [
            # OpenAI models (support on-demand, no inference profiles needed)
            "openai.gpt-oss-120b-1:0",
            "openai.gpt-oss-20b-1:0",
            # Meta Llama models (good for less common languages)
            "meta.llama3-3-70b-instruct-v1:0",
            "meta.llama3-2-90b-instruct-v1:0",
            "meta.llama3-1-70b-instruct-v1:0",
            "meta.llama3-70b-instruct-v1:0",
            # Cohere models
            "cohere.command-r-plus-v1:0",
            "cohere.command-r-v1:0",
            # Amazon Nova
            "amazon.nova-pro-v1:0",
            "amazon.nova-lite-v1:0",
            # Mistral
            "mistral.mistral-large-2402-v1:0",
        ]
    else:  # summarization
        priority_models = [
            "amazon.nova-pro-v1:0",
            "openai.gpt-oss-120b-1:0",
            "openai.gpt-oss-20b-1:0",
            "amazon.nova-lite-v1:0",
            "meta.llama3-3-70b-instruct-v1:0",
        ]
    
    # Get all available models
    all_available = []
    for category in available.values():
        all_available.extend(category)
    
    # Return models in priority order that are available
    recommended = []
    for model_id in priority_models:
        if model_id in all_available:
            recommended.append(model_id)
    
    return recommended


def print_available_models(region: Optional[str] = None):
    """Print a formatted list of available models"""
    try:
        available = get_available_models(region=region)
        
        print("=" * 70)
        print("AVAILABLE BEDROCK MODELS IN YOUR ACCOUNT")
        print("=" * 70)
        print()
        
        categories = {
            'openai': 'OpenAI (GPT OSS)',
            'amazon': 'Amazon (Nova/Titan)',
            'meta': 'Meta (Llama)',
            'cohere': 'Cohere',
            'mistral': 'Mistral AI',
            'ai21': 'AI21 Labs',
            'stability': 'Stability AI',
            'other': 'Other'
        }
        
        total = 0
        for category, models in available.items():
            if models:
                print(f"{categories.get(category, category.upper())}:")
                for model in sorted(models):
                    print(f"  • {model}")
                print()
                total += len(models)
        
        print(f"Total: {total} models available")
        print("=" * 70)
        
        # Show recommendations
        print()
        print("RECOMMENDED MODELS FOR TRANSLATION:")
        translation_models = get_recommended_models_for_task("translation", region)
        if translation_models:
            for i, model in enumerate(translation_models[:5], 1):
                print(f"  {i}. {model}")
        else:
            print("  No recommended translation models available")
        
        print()
        print("RECOMMENDED MODELS FOR SUMMARIZATION:")
        summarization_models = get_recommended_models_for_task("summarization", region)
        if summarization_models:
            for i, model in enumerate(summarization_models[:5], 1):
                print(f"  {i}. {model}")
        else:
            print("  No recommended summarization models available")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("  1. AWS credentials are configured (aws configure)")
        print("  2. You have permissions to list Bedrock models")
        print("  3. You're using the correct AWS region")


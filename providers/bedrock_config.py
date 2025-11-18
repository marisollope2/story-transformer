"""
Bedrock Model Configuration
Configure which models to use for translation and summarization
"""
import os
from typing import Dict, Optional

# Default model configuration
# Using OpenAI models through Bedrock (no inference profiles required)
DEFAULT_MODELS = {
    "translation": "openai.gpt-oss-120b-1:0",  # OpenAI GPT OSS 120B - excellent for translation, supports on-demand
    "summarization": "amazon.nova-pro-v1:0"  # Nova Pro - excellent for summarization
}

# Alternative model options (you can switch these in your .env file)
ALTERNATIVE_MODELS = {
    "translation": {
        # OpenAI models - excellent for translation, support on-demand
        "openai_gpt_oss_120b": "openai.gpt-oss-120b-1:0",  # Large model, best quality
        "openai_gpt_oss_20b": "openai.gpt-oss-20b-1:0",  # Smaller, faster, cheaper
        
        # Meta Llama models - good multilingual support, including less common languages
        "llama_3_3_70b": "meta.llama3-3-70b-instruct-v1:0",  # Best for less common languages
        "llama_3_2_90b": "meta.llama3-2-90b-instruct-v1:0",  # Large model, good multilingual
        "llama_3_1_70b": "meta.llama3-1-70b-instruct-v1:0",  # Good balance
        "llama_3_70b": "meta.llama3-70b-instruct-v1:0",  # Solid option
        
        # Cohere models - optimized for 10 languages including less common ones
        "cohere_command_r_plus": "cohere.command-r-plus-v1:0",  # Best for less common languages
        "cohere_command_r": "cohere.command-r-v1:0",  # Good alternative
        
        # Mistral models - good for European languages
        "mistral_large": "mistral.mistral-large-2402-v1:0",
        "mistral_small": "mistral.mistral-small-2402-v1:0",
        
        # Amazon models
        "nova_pro": "amazon.nova-pro-v1:0",
        "nova_lite": "amazon.nova-lite-v1:0"
    },
    "summarization": {
        "nova_pro": "amazon.nova-pro-v1:0",
        "openai_gpt_oss_120b": "openai.gpt-oss-120b-1:0",
        "openai_gpt_oss_20b": "openai.gpt-oss-20b-1:0",
        "nova_lite": "amazon.nova-lite-v1:0"  # Faster, cheaper
    }
}

# Recommended models for less common languages (Swahili, African languages, etc.)
LOW_RESOURCE_LANGUAGE_MODELS = {
    "meta_llama_3_3_70b": "meta.llama3-3-70b-instruct-v1:0",  # Best overall for less common languages
    "cohere_command_r_plus": "cohere.command-r-plus-v1:0",  # Optimized for 10 languages
    "openai_gpt_oss_120b": "openai.gpt-oss-120b-1:0",  # Large OpenAI model, good multilingual
    "meta_llama_3_2_90b": "meta.llama3-2-90b-instruct-v1:0"  # Large multilingual model
}


def get_model_config(check_access: bool = False) -> Dict[str, str]:
    """
    Get model configuration from environment variables or use defaults.
    Optionally checks if models are actually available in your account.
    
    Args:
        check_access: If True, verify models are available before returning
    
    Environment variables:
        BEDROCK_TRANSLATION_MODEL: Model ID for translation
        BEDROCK_SUMMARIZATION_MODEL: Model ID for summarization
    
    Returns:
        Dictionary with 'translation' and 'summarization' model IDs
    """
    translation_model = os.getenv(
        "BEDROCK_TRANSLATION_MODEL",
        DEFAULT_MODELS["translation"]
    )
    summarization_model = os.getenv(
        "BEDROCK_SUMMARIZATION_MODEL",
        DEFAULT_MODELS["summarization"]
    )
    
    # Check model access if requested
    if check_access:
        try:
            from .bedrock_model_checker import check_model_access, get_recommended_models_for_task
            
            # Check translation model
            if not check_model_access(translation_model):
                print(f"Warning: Translation model {translation_model} not available.")
                recommended = get_recommended_models_for_task("translation")
                if recommended:
                    print(f"  Using recommended model: {recommended[0]}")
                    translation_model = recommended[0]
                else:
                    print(f"  No alternative translation models available. Using default: {DEFAULT_MODELS['translation']}")
            
            # Check summarization model
            if not check_model_access(summarization_model):
                print(f"Warning: Summarization model {summarization_model} not available.")
                recommended = get_recommended_models_for_task("summarization")
                if recommended:
                    print(f"  Using recommended model: {recommended[0]}")
                    summarization_model = recommended[0]
                else:
                    print(f"  No alternative summarization models available. Using default: {DEFAULT_MODELS['summarization']}")
        except Exception as e:
            print(f"Warning: Could not verify model access: {e}")
            print("  Using configured models anyway. Run 'python scripts/check_bedrock_models.py' to check access.")
    
    return {
        "translation": translation_model,
        "summarization": summarization_model
    }


def get_region() -> str:
    """Get AWS region from environment or use default"""
    return os.getenv("AWS_DEFAULT_REGION", "us-east-1")


def get_translation_model_for_language(language: str) -> str:
    """
    Get recommended translation model based on target language.
    For less common languages (Swahili, African languages, etc.), 
    recommends models with better multilingual support.
    
    Args:
        language: Target language name (e.g., "Swahili", "Spanish")
    
    Returns:
        Recommended model ID
    """
    # Less common languages that may need specialized models
    less_common_languages = [
        "swahili", "kiswahili", "hindi", "bengali", "urdu", "tamil", 
        "telugu", "marathi", "gujarati", "kannada", "malayalam", "punjabi",
        "amharic", "hausa", "yoruba", "igbo", "zulu", "xhosa", "afrikaans",
        "indonesian", "malay", "thai", "vietnamese", "tagalog", "filipino"
    ]
    
    language_lower = language.lower()
    
    # Check if it's a less common language
    if any(lang in language_lower for lang in less_common_languages):
        # Use model from environment or default to best multilingual model
        return os.getenv(
            "BEDROCK_TRANSLATION_MODEL",
            LOW_RESOURCE_LANGUAGE_MODELS["meta_llama_3_3_70b"]
        )
    else:
        # Use standard translation model
        return get_model_config()["translation"]


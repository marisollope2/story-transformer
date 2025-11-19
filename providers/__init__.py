"""
Bedrock Providers Package
Multi-model support for translation and summarization using AWS Bedrock
"""
from .bedrock_translation import translate_structured_text, translate_simple_text
from .bedrock_summarization import summarize_text_narrative, summarize_and_translate
from .bedrock_client import get_bedrock_client, invoke_bedrock_model
from .bedrock_config import (
    get_model_config, 
    get_region, 
    get_translation_model_for_language,
    DEFAULT_MODELS, 
    ALTERNATIVE_MODELS,
    LOW_RESOURCE_LANGUAGE_MODELS
)
from .bedrock_model_checker import (
    get_available_models,
    check_model_access,
    get_recommended_models_for_task,
    print_available_models
)

__all__ = [
    'translate_structured_text',
    'translate_simple_text',
    'summarize_text_narrative',
    'summarize_and_translate',
    'get_bedrock_client',
    'invoke_bedrock_model',
    'get_model_config',
    'get_region',
    'get_translation_model_for_language',
    'get_available_models',
    'check_model_access',
    'get_recommended_models_for_task',
    'print_available_models',
    'DEFAULT_MODELS',
    'ALTERNATIVE_MODELS',
    'LOW_RESOURCE_LANGUAGE_MODELS'
]


"""
Bedrock Summarization Module
Handles text summarization using AWS Bedrock models
"""
import os
from typing import Optional
from dotenv import load_dotenv

from .bedrock_client import get_bedrock_client, invoke_bedrock_model
from .bedrock_config import get_model_config, get_region
from .bedrock_model_checker import check_model_access, get_recommended_models_for_task
from .text_normalization import normalize_for_bedrock

load_dotenv()


def summarize_text_narrative(
    text: str,
    word_limit: int = 200,
    region: Optional[str] = None,
    model_id: Optional[str] = None
) -> str:
    """
    Summarizes text in a clear, narrative style using Bedrock.
    Preserves the logical flow and tone of the original text.
    
    Args:
        text: Text to summarize
        word_limit: Target word count for summary
        region: AWS region (optional, uses config default)
        model_id: Specific model to use (optional, uses config default)
    
    Returns:
        Summarized text
    """
    if not text.strip():
        return ""

    # Normalize text for Bedrock compatibility
    text = normalize_for_bedrock(text)

    # Get model configuration
    config = get_model_config()
    summarization_model = model_id or config["summarization"]
    aws_region = region or get_region()
    
    # Verify model access
    if not check_model_access(summarization_model, region=aws_region):
        # Try to find an available alternative
        recommended = get_recommended_models_for_task("summarization", region=aws_region)
        if recommended:
            print(f"Model {summarization_model} not available. Using {recommended[0]} instead.")
            summarization_model = recommended[0]
        else:
            raise Exception(
                f"Model {summarization_model} is not available in your account. "
                f"Run 'python scripts/check_bedrock_models.py' to see available models."
            )

    # Initialize Bedrock client
    client = get_bedrock_client(region_name=aws_region)

    # Build prompts
    system_prompt = (
        "You are a skilled writer who summarizes text in a clear and narrative style. "
        "Preserve the logical flow and tone of the original text. Use transitions to make "
        "the summary feel cohesive. Keep the summary concise but comprehensive. "
        "Provide ONLY the summary text without any reasoning, analysis, or explanation of your process."
    )

    prompt = f"""Summarize the following text in approximately {word_limit} words. 
Maintain a narrative style that preserves the logical flow and key information.

IMPORTANT: Provide ONLY the summary. Do not include any reasoning, thinking process, or explanation of how you created the summary.

Text to summarize:
{text}
"""

    try:
        summary = invoke_bedrock_model(
            client=client,
            model_id=summarization_model,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=2048,
            temperature=0.5  # Moderate temperature for balanced creativity and accuracy
        )
        
        return summary.strip()
    
    except Exception as e:
        raise Exception(f"Summarization failed: {str(e)}")



def summarize_and_translate(
    text: str,
    word_limit: int = 200,
    language: str = "english",
    region: Optional[str] = None,
    translation_model_id: Optional[str] = None,
    summarization_model_id: Optional[str] = None
) -> str:
    """
    Summarizes text and optionally translates it using separate Bedrock models.
    Uses different models for summarization and translation.
    
    Args:
        text: Text to summarize
        word_limit: Target word count for summary
        language: Target language (if "english", skip translation)
        region: AWS region (optional)
        translation_model_id: Specific translation model (optional)
        summarization_model_id: Specific summarization model (optional)
    
    Returns:
        Summarized (and optionally translated) text
    """
    from .bedrock_translation import translate_simple_text
    from .text_normalization import normalize_for_bedrock

    # First, summarize using the summarization model
    summary = summarize_text_narrative(
        text=text,
        word_limit=word_limit,
        region=region,
        model_id=summarization_model_id
    )
    summary = normalize_for_bedrock(summary)

    # Then, translate if needed using the translation model
    if language.lower() != "english":
        summary = translate_simple_text(
            text=summary,
            target_language=language,
            region=region,
            model_id=translation_model_id
        )
        summary = normalize_for_bedrock(summary)

    return summary


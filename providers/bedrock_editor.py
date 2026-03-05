"""
Bedrock Editor Module
Handles iterative editing and refinement using AWS Bedrock models.

Originally this module attempted to route requests to specialized
translation/summarization functions based on keyword detection.
It now uses a single smart refinement call that lets the model
interpret the user's instructions (translate, summarize, both, edit, etc.).
"""
import os
import re
from typing import Optional
from dotenv import load_dotenv

from .bedrock_client import get_bedrock_client, invoke_bedrock_model
from .bedrock_config import get_model_config, get_region
from .bedrock_model_checker import check_model_access, get_recommended_models_for_task
from .text_normalization import normalize_for_bedrock, remove_reasoning

load_dotenv()


def refine_with_chat(
    original_text: str,
    current_text: str,
    user_request: str,
    region: Optional[str] = None,
    model_id: Optional[str] = None
) -> str:
    """
    Refines text based on a user chat request.

    This now uses a single generic refinement call that lets the model
    interpret the user's intent (translate, summarize, both, or general edits)
    instead of hard-coding routing logic.

    Args:
        original_text: The original source text
        current_text: Current version of the text (may be translated/summarized)
        user_request: User's editing request
        region: AWS region (optional)
        model_id: Specific model to use (optional)
    
    Returns:
        Refined text
    """
    if not user_request.strip():
        return current_text

    aws_region = region or get_region()

    # Single smart refinement call: let the model interpret the request.
    return _generic_refine(
        original_text=original_text,
        current_text=current_text,
        user_request=user_request,
        region=aws_region,
        model_id=model_id,
    )


def _generic_refine(
    original_text: str,
    current_text: str,
    user_request: str,
    region: Optional[str] = None,
    model_id: Optional[str] = None
) -> str:
    """
    Generic refinement function for all editing/translation/summarization
    requests. The model is responsible for interpreting the user's intent
    (translate, summarize, both, style changes, etc.) from the request.
    """
    # Get model configuration
    config = get_model_config()
    if model_id:
        editor_model = model_id
    else:
        # Use translation model (good for general editing)
        editor_model = config.get("translation", config.get("summarization"))
    
    aws_region = region or get_region()
    
    # Verify model access
    if not check_model_access(editor_model, region=aws_region):
        recommended = get_recommended_models_for_task("translation", region=aws_region)
        if recommended:
            editor_model = recommended[0]
        else:
            raise Exception(
                f"Model {editor_model} is not available in your account. "
                f"Run 'python scripts/check_bedrock_models.py' to see available models."
            )
    
    client = get_bedrock_client(region_name=aws_region)
    
    system_prompt = (
        "You are a professional editor, translator, and summarizer - specializing in environmental journalism. "
        "Given an article and a user request, you must decide whether to translate, "
        "summarize, both, or perform other edits (tone, style, length, etc.). "
        "Always follow explicit constraints in the request, such as target language, "
        "word count (for example 'under 200 words'), and structural preferences "
        "(for example whether to keep or remove labels like 'Title:' or 'Section Header:'). "
        "When translating, you must follow the punctuation, spacing, and orthographic "
        "conventions of the target language (including quote styles and decimal separators) "
        "and lightly copy-edit for clarity and correctness without changing the meaning. "
        "CRITICAL: Output ONLY the final user-facing text, with no explanations or reasoning."
    )
    
    prompt = f"""You are helping refine and transform text based on user instructions.

ORIGINAL SOURCE TEXT:
{original_text[:2000]}

CURRENT TEXT (may be translated/summarized):
{current_text}

USER REQUEST:
{user_request}

Decide what operation to perform based on the user request. This could be:
- Translation to a specific language
- Summarization to a requested length
- Both translation and summarization
- General editing/refinement (tone, clarity, length, style)

Respect all explicit constraints in the user request, including:
- Target language
- Word or character limits
- Whether to preserve or remove structural labels (such as 'Title:', 'Section Header:', 'Body:')

CRITICAL: Output ONLY the final refined text. Do not include:
- Any explanation of your changes
- Any reasoning or thinking process
- Any commentary or analysis
- Phrases like "Here's the translation" or "I've summarized it"

Start directly with the refined output."""
    
    try:
        refined = invoke_bedrock_model(
            client=client,
            model_id=editor_model,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=4096,
            temperature=0.5
        )
        
        # Remove any chain-of-thought reasoning
        refined = remove_reasoning(refined)
        
        return refined.strip()
    
    except Exception as e:
        raise Exception(f"Refinement failed: {str(e)}")

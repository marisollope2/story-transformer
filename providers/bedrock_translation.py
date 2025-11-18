"""
Bedrock Translation Module
Handles translation using AWS Bedrock models
"""
import re
import os
from typing import Optional
from dotenv import load_dotenv

from .bedrock_client import get_bedrock_client, invoke_bedrock_model
from .bedrock_config import get_model_config, get_region, get_translation_model_for_language
from .bedrock_model_checker import check_model_access, get_recommended_models_for_task

load_dotenv()


def translate_structured_text(
    text: str,
    target_language: str = "French",
    region: Optional[str] = None,
    model_id: Optional[str] = None
) -> str:
    """
    Translates a structured article into target_language using Bedrock.
    Preserves English labels (e.g. "Title:", "Key Ideas:", etc.) but translates
    everything that follows each colon, plus all other paragraphs/bullets.
    
    Args:
        text: Text to translate
        target_language: Target language name (e.g., "French", "Spanish")
        region: AWS region (optional, uses config default)
        model_id: Specific model to use (optional, uses config default)
    
    Returns:
        Translated text
    """
    if target_language.lower() == "english" or not text.strip():
        return text

    # Get model configuration - use language-specific model if available
    if model_id:
        translation_model = model_id
    else:
        # Automatically select best model for the target language
        translation_model = get_translation_model_for_language(target_language)
    
    # Verify model access
    aws_region = region or get_region()
    if not check_model_access(translation_model, region=aws_region):
        # Try to find an available alternative
        recommended = get_recommended_models_for_task("translation", region=aws_region)
        if recommended:
            print(f"Model {translation_model} not available. Using {recommended[0]} instead.")
            translation_model = recommended[0]
        else:
            raise Exception(
                f"Model {translation_model} is not available in your account. "
                f"Run 'python scripts/check_bedrock_models.py' to see available models."
            )
    
    # Initialize Bedrock client
    client = get_bedrock_client(region_name=aws_region)

    # Define labels and placeholders
    label_to_ph = {
        "Title:": "<__TITLE__>",
        "Key Ideas:": "<__KEY_IDEAS__>",
        "Body:": "<__BODY__>",
        "Section Header:": "<__SECTION_HEADER__>",
        "Banner image:": "<__BANNER_IMAGE__>",
        "Image Captions:": "<__IMAGE_CAPTIONS__>",
    }

    # Replace labels with placeholders
    safe_text = text
    for label, ph in label_to_ph.items():
        safe_text = re.sub(rf"(?m)^{re.escape(label)}", ph, safe_text)

    # Build the prompt
    prompt = f"""
Translate the following text into {target_language}.  

🛑 DO NOT translate or alter any of these placeholders:
  {', '.join(label_to_ph.values())}

For any line beginning with a placeholder like <__TITLE__>, translate only what comes *after* it,
and leave the placeholder itself unchanged.

For all other lines (paragraph text, bullets), translate normally.
Preserve ALL line breaks, bullets, and overall formatting. 
Do NOT add Markdown or extra symbols.

🔤 STYLE AND FORMATTING RULES:
- Use natural sentence structure for the target language (avoid copying English word order).
- Ensure gender and number agreement between nouns and adjectives.
- Keep correct spacing for punctuation and symbols:
  • A space before the "%" sign in Spanish and French (e.g., "20 %").
  • No punctuation for 4-digit numbers (e.g., "3000", not "3,000" or "3.000").
  • Use commas as decimal separators only when appropriate for the target language.
- Keep quotation marks appropriate for the target language ("…" in English, « … » in French, "…" in Spanish).
- Maintain metric units only (omit imperial conversions like pounds, miles, or °F).
- Do NOT capitalize adjectives indicating regions or directions (e.g., "África occidental" not "África Occidental").
- In Spanish, retain definite articles in headlines when grammatically required (e.g., "la pesca").
- In French, italicize foreign words if they appear in the source text.
- Do not use symbols such as "+" for approximations; spell them out (e.g., "más de 5500").
- Avoid literal translations that sound unnatural (e.g., "jugar un papel" → "desempeñar un papel"; "etiquetar" → "llamar").
- Verify all official names of laws, directives, and institutions using their standard or most common translations.
- If translation fails or encounters unknown language segments, leave them unchanged rather than producing garbled output.

BEGIN TEXT
{safe_text}
END TEXT
""".strip()

    # System prompt for translation quality
    system_prompt = (
        f"You are a professional {target_language}-language translator specializing in "
        "environmental and scientific journalism. You produce accurate, natural translations "
        "that maintain the original meaning while adapting to the target language's conventions."
    )

    try:
        # Invoke the model
        translated = invoke_bedrock_model(
            client=client,
            model_id=translation_model,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=8192,
            temperature=0.3  # Lower temperature for more consistent translation
        )

        # Restore placeholders back to English labels
        for label, ph in label_to_ph.items():
            translated = translated.replace(ph, label)

        return translated.strip()
    
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")


def translate_simple_text(
    text: str,
    target_language: str = "Spanish",
    region: Optional[str] = None,
    model_id: Optional[str] = None
) -> str:
    """
    Simple translation function for plain text (no structured labels).
    
    Args:
        text: Text to translate
        target_language: Target language name
        region: AWS region (optional)
        model_id: Specific model to use (optional)
    
    Returns:
        Translated text
    """
    if target_language.lower() == "english" or not text.strip():
        return text

    # Get model configuration - use language-specific model if available
    if model_id:
        translation_model = model_id
    else:
        # Automatically select best model for the target language
        translation_model = get_translation_model_for_language(target_language)
    
    # Verify model access
    aws_region = region or get_region()
    if not check_model_access(translation_model, region=aws_region):
        # Try to find an available alternative
        recommended = get_recommended_models_for_task("translation", region=aws_region)
        if recommended:
            print(f"Model {translation_model} not available. Using {recommended[0]} instead.")
            translation_model = recommended[0]
        else:
            raise Exception(
                f"Model {translation_model} is not available in your account. "
                f"Run 'python scripts/check_bedrock_models.py' to see available models."
            )
    
    client = get_bedrock_client(region_name=aws_region)

    prompt = f"Translate the following text to {target_language}. Preserve the original formatting, line breaks, and structure.\n\n{text}"

    system_prompt = (
        f"You are a professional {target_language}-language translator. "
        "Provide accurate, natural translations that maintain the original meaning and tone."
    )

    try:
        translated = invoke_bedrock_model(
            client=client,
            model_id=translation_model,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=4096,
            temperature=0.3
        )
        return translated.strip()
    
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")


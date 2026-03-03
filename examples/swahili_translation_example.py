"""
Example: Translating to Swahili and other less common languages
Demonstrates automatic model selection for less common languages
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.bedrock_translation import translate_structured_text, translate_simple_text
from providers.bedrock_config import get_translation_model_for_language, LOW_RESOURCE_LANGUAGE_MODELS

# Sample text about environmental conservation
sample_text = """
Title: Protecting the Amazon Rainforest

Key Ideas:
- Deforestation threatens biodiversity
- Indigenous communities need protection
- Climate change impacts are severe

Body:
The Amazon rainforest is one of the most biodiverse regions on Earth. 
It plays a crucial role in regulating global climate patterns and 
providing habitat for millions of species. However, deforestation 
rates have increased dramatically in recent years, threatening this 
vital ecosystem.
"""

print("=" * 70)
print("TRANSLATING TO LESS COMMON LANGUAGES")
print("=" * 70)
print()

# Show which model will be used for Swahili
swahili_model = get_translation_model_for_language("Swahili")
print(f"Model selected for Swahili: {swahili_model}")
print("(Automatically uses Llama 3.3 70B for better support)")
print()

print("=" * 70)
print("EXAMPLE 1: Translate to Swahili (Automatic Model Selection)")
print("=" * 70)
try:
    translated = translate_structured_text(
        text=sample_text,
        target_language="Swahili"
    )
    print("Translated to Swahili:")
    print(translated)
    print()
except Exception as e:
    print(f"Translation error: {e}")
    print("Make sure you have:")
    print("  1. AWS credentials configured")
    print("  2. Model access granted for Meta Llama 3.3 70B in Bedrock Console")
    print()

print("=" * 70)
print("EXAMPLE 2: Translate to Swahili (Using Cohere Command R+)")
print("=" * 70)
try:
    translated = translate_structured_text(
        text=sample_text,
        target_language="Swahili",
        model_id="cohere.command-r-plus-v1:0"  # Explicitly use Cohere
    )
    print("Translated to Swahili using Cohere:")
    print(translated)
    print()
except Exception as e:
    print(f"Translation error: {e}")
    print()

print("=" * 70)
print("EXAMPLE 3: Translate to Hindi (Another Less Common Language)")
print("=" * 70)
try:
    translated = translate_structured_text(
        text=sample_text,
        target_language="Hindi"
    )
    print("Translated to Hindi:")
    print(translated)
    print()
except Exception as e:
    print(f"Translation error: {e}")
    print()

print("=" * 70)
print("AVAILABLE MODELS FOR LESS COMMON LANGUAGES")
print("=" * 70)
for name, model_id in LOW_RESOURCE_LANGUAGE_MODELS.items():
    print(f"  {name}: {model_id}")
print()

print("=" * 70)
print("SUPPORTED LESS COMMON LANGUAGES")
print("=" * 70)
languages = [
    "Swahili (Kiswahili)", "Hindi", "Bengali", "Urdu", "Tamil", "Telugu",
    "Marathi", "Gujarati", "Kannada", "Malayalam", "Punjabi",
    "Amharic", "Hausa", "Yoruba", "Igbo", "Zulu", "Xhosa", "Afrikaans",
    "Indonesian", "Malay", "Thai", "Vietnamese", "Tagalog", "Filipino"
]
for lang in languages:
    print(f"  • {lang}")
print()

print("=" * 70)
print("Note: The system automatically selects the best model for these languages.")
print("You can override by explicitly specifying a model_id parameter.")
print("=" * 70)


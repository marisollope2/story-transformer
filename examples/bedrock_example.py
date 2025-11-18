"""
Example script demonstrating Bedrock multi-model usage
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.bedrock_translation import translate_structured_text, translate_simple_text
from providers.bedrock_summarization import summarize_text_narrative, summarize_and_translate
from providers.bedrock_config import get_model_config

# Display current model configuration
config = get_model_config()
print("Current Model Configuration:")
print(f"  Translation Model: {config['translation']}")
print(f"  Summarization Model: {config['summarization']}")
print()

# Example text
sample_text = """
Title: Climate Change Impact on Amazon Rainforest

Key Ideas:
- Deforestation rates have increased by 20% in the past decade
- Biodiversity loss affects over 3,000 species
- Indigenous communities face displacement

Body:
The Amazon rainforest, often called the "lungs of the Earth," is facing unprecedented challenges due to climate change and human activities. Recent studies show that deforestation rates have reached alarming levels, with over 10,000 square kilometers lost annually. This destruction not only threatens the rich biodiversity of the region but also impacts global climate patterns.
"""

print("=" * 60)
print("EXAMPLE 1: Translation")
print("=" * 60)
try:
    translated = translate_structured_text(
        text=sample_text,
        target_language="Spanish"
    )
    print("Translated to Spanish:")
    print(translated)
    print()
except Exception as e:
    print(f"Translation error: {e}")
    print()

print("=" * 60)
print("EXAMPLE 2: Summarization")
print("=" * 60)
try:
    summary = summarize_text_narrative(
        text=sample_text,
        word_limit=100
    )
    print("Summary (100 words):")
    print(summary)
    print()
except Exception as e:
    print(f"Summarization error: {e}")
    print()

print("=" * 60)
print("EXAMPLE 3: Summarize and Translate (Multi-Model)")
print("=" * 60)
print("This uses the summarization model first, then the translation model.")
try:
    result = summarize_and_translate(
        text=sample_text,
        word_limit=100,
        language="French"
    )
    print("Summary translated to French:")
    print(result)
    print()
except Exception as e:
    print(f"Summarize and translate error: {e}")
    print()

print("=" * 60)
print("Note: Make sure you have:")
print("  1. AWS credentials configured (aws configure)")
print("  2. Model access granted in AWS Bedrock Console")
print("  3. Region set correctly (default: us-east-1)")
print("=" * 60)


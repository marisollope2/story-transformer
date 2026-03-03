import sys
import os

# Add parent directory to path to import providers
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.bedrock_summarization import summarize_text_narrative as bedrock_summarize_text_narrative
from providers.bedrock_summarization import summarize_and_translate as bedrock_summarize_and_translate

# Keep OpenAI version for backward compatibility
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def get_openai_client(api_key):
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI package not installed. Please use Bedrock instead.")
    return OpenAI(api_key=api_key)

def summarize_text_narrative(text, word_limit=200, client=None, use_bedrock: bool = True):
    if not text.strip():
        return ""
    
    # Use Bedrock by default
    if use_bedrock:
        return bedrock_summarize_text_narrative(text, word_limit)
    
    # OpenAI fallback (for backward compatibility)
    if client is None:
        raise ValueError("Client required for OpenAI summarization")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a skilled writer who summarizes text in a clear and narrative style. "
                    "Preserve the logical flow and tone of the original text. Use transitions to make the summary feel cohesive. "
                    f"Keep the summary around {word_limit} words."
                )
            },
            {
                "role": "user",
                "content": f"Summarize this text:\n\n{text}"
            }
        ]
    )
    return response.choices[0].message.content.strip()

def translate(text, language="Spanish", client=None):
    if not text.strip():
        return ""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a professional {language}-language science and environmental journalist. "
                    "You write with clarity and impact for general Latin American audiences. "
                    "Use natural phrasing and journalistic tone."
                )
            },
            {
                "role": "user",
                "content": f"Translate the following English text to {language}:\n\n{text}"
            }
        ]
    )
    return response.choices[0].message.content.strip()

def summarize_and_translate(text, word_limit=200, language="english", api_key=None, use_bedrock: bool = True):
    # Use Bedrock by default (uses separate models for summarization and translation)
    if use_bedrock:
        return bedrock_summarize_and_translate(text, word_limit, language)
    
    # OpenAI fallback (for backward compatibility)
    if not api_key:
        raise ValueError("API key required for OpenAI")
    client = get_openai_client(api_key)
    summary = summarize_text_narrative(text, word_limit=word_limit, client=client, use_bedrock=False)
    if language.lower() != "english":
        summary = translate(summary, language, client=client)
    return summary
# AWS Bedrock Multi-Model Setup Guide

This guide explains how to use the multi-model Bedrock setup for translation and summarization.

## Overview

The project now supports using **different AWS Bedrock models** for translation and summarization:

- **Translation Model**: `anthropic.claude-sonnet-4-5-20250929-v1:0` (Claude Sonnet 4.5)
- **Summarization Model**: `amazon.nova-pro-v1:0` (Nova Pro)

## Prerequisites

1. **AWS Account** with Bedrock access
2. **AWS Credentials** configured (via `aws configure` or environment variables)
3. **Model Access**: Request access to the models in AWS Bedrock Console

## Check Your Model Access

**IMPORTANT**: Before using the system, check which models you actually have access to:

```bash
python scripts/check_bedrock_models.py
```

This will:
- List all available models in your account
- Show recommended models for translation and summarization
- Provide configuration suggestions based on your available models

The system will **automatically use only models you have access to** and will fall back to available alternatives if your configured model isn't accessible.

### Requesting Model Access

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to "Model access" in the left sidebar
3. Request access to:
   - Anthropic Claude Sonnet 4.5
   - Amazon Nova Pro

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

This will install `boto3` and `botocore` for AWS Bedrock access.

## Configuration

### Option 1: Environment Variables (Recommended)

Create a `.env` file in the project root:

```env
AWS_DEFAULT_REGION=us-east-1
BEDROCK_TRANSLATION_MODEL=anthropic.claude-sonnet-4-5-20250929-v1:0
BEDROCK_SUMMARIZATION_MODEL=amazon.nova-pro-v1:0
```

### Option 2: AWS Config File

The models will use your default AWS region from `~/.aws/config` or the `AWS_DEFAULT_REGION` environment variable.

## Usage

### In Python Scripts

```python
from providers.bedrock_translation import translate_structured_text
from providers.bedrock_summarization import summarize_text_narrative, summarize_and_translate

# Translation
translated = translate_structured_text(
    text="Your text here",
    target_language="Spanish"
)

# Summarization
summary = summarize_text_narrative(
    text="Your long text here",
    word_limit=200
)

# Summarize and translate (uses both models)
result = summarize_and_translate(
    text="Your text here",
    word_limit=200,
    language="Spanish"
)
```

### In Existing Scripts

The existing `scripts/translation_pipeline.py` and `scripts/summarization_pipeline.py` have been updated to use Bedrock by default. They will automatically use the configured models.

### In Streamlit App

The `api/app.py` will continue to work as before, but now uses Bedrock models instead of OpenAI.

## Alternative Models

You can switch to different models by setting environment variables:

### Translation Models

**For Common Languages (Spanish, French, German, etc.):**
- `anthropic.claude-sonnet-4-5-20250929-v1:0` (default) - Best quality
- `anthropic.claude-haiku-4-5-20251001-v1:0` - Faster, cheaper
- `amazon.nova-pro-v1:0` - Amazon's latest
- `anthropic.claude-opus-4-1-20250805-v1:0` - Most capable

**For Less Common Languages (Swahili, African languages, Hindi, etc.):**
- `meta.llama3-3-70b-instruct-v1:0` ⭐ **RECOMMENDED** - Best for Swahili and less common languages
- `cohere.command-r-plus-v1:0` - Optimized for 10 languages including less common ones
- `meta.llama3-2-90b-instruct-v1:0` - Large multilingual model
- `anthropic.claude-opus-4-1-20250805-v1:0` - Most capable Claude model

**Other Options:**
- `meta.llama3-1-70b-instruct-v1:0` - Good balance
- `cohere.command-r-v1:0` - Good alternative
- `mistral.mistral-large-2402-v1:0` - Good for European languages

### Summarization Models
- `amazon.nova-pro-v1:0` (default) - Best for summarization
- `anthropic.claude-sonnet-4-5-20250929-v1:0` - Excellent quality
- `anthropic.claude-haiku-4-5-20251001-v1:0` - Faster, cheaper
- `amazon.nova-lite-v1:0` - Faster, cheaper

## Automatic Model Selection for Less Common Languages

The system **automatically selects the best model** when translating to less common languages like:
- Swahili (Kiswahili)
- Hindi, Bengali, Urdu, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi
- African languages: Amharic, Hausa, Yoruba, Igbo, Zulu, Xhosa, Afrikaans
- Southeast Asian: Indonesian, Malay, Thai, Vietnamese, Tagalog, Filipino

When you translate to these languages, it will automatically use **Meta Llama 3.3 70B** (or your configured model) instead of the default Claude model.

To override this behavior, explicitly set a model:
```python
translate_structured_text(text, target_language="Swahili", model_id="cohere.command-r-plus-v1:0")
```

Example for common languages:
```env
BEDROCK_TRANSLATION_MODEL=anthropic.claude-haiku-4-5-20251001-v1:0
BEDROCK_SUMMARIZATION_MODEL=amazon.nova-lite-v1:0
```

Example for less common languages (Swahili, etc.):
```env
BEDROCK_TRANSLATION_MODEL=meta.llama3-3-70b-instruct-v1:0
BEDROCK_SUMMARIZATION_MODEL=amazon.nova-pro-v1:0
```

Or use Cohere for less common languages:
```env
BEDROCK_TRANSLATION_MODEL=cohere.command-r-plus-v1:0
```

## Model Comparison

| Model | Speed | Cost | Quality | Best For | Less Common Languages |
|-------|-------|------|---------|----------|----------------------|
| Claude Sonnet 4.5 | Medium | Medium | Excellent | Translation, Complex tasks | Good |
| Claude Haiku 4.5 | Fast | Low | Good | Quick translations | Good |
| **Llama 3.3 70B** | Medium | Medium | Excellent | **Less common languages** | ⭐ **Best** |
| **Cohere Command R+** | Fast | Medium | Excellent | **Less common languages** | ⭐ **Best** |
| Llama 3.2 90B | Medium | Medium-High | Excellent | Large multilingual tasks | Excellent |
| Nova Pro | Fast | Medium | Excellent | Summarization, General tasks | Good |
| Nova Lite | Very Fast | Low | Good | Quick summarization | Good |

## Troubleshooting

### Error: "Model access not granted"
- Request access to the models in AWS Bedrock Console
- Wait a few minutes for access to be granted

### Error: "Region not supported"
- Check that your region supports the models
- Most models are available in `us-east-1`, `us-west-2`, `eu-west-1`

### Error: "Credentials not found"
- Run `aws configure` to set up credentials
- Or set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables

### Error: "boto3 not installed"
- Run `pip install boto3 botocore`

## Cost Considerations

- **Claude Sonnet 4.5**: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- **Nova Pro**: ~$0.50 per 1M input tokens, ~$2 per 1M output tokens
- **Claude Haiku 4.5**: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens

For cost optimization, consider using Haiku for translation and Nova Lite for summarization if quality requirements allow.

## Backward Compatibility

The code maintains backward compatibility with OpenAI. To use OpenAI instead of Bedrock:

```python
# In your code
translate_structured_text(text, target_language, api_key=api_key, use_bedrock=False)
```


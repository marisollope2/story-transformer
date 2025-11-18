import anthropic

client = anthropic.Anthropic()

def translate_text_with_claude(input_text: str, target_language: str) -> str:
    SYSTEM_TEXT = f"You are a professional {target_language}-language science and environmental journalist. You write with clarity and impact for general {target_language}-speaking audiences. Use natural phrasing and journalistic tone."

    TRANSLATE_TEXT = f"""
    Translate the following English text to {target_language}.
    Keep the same structure of the article. 
    Translate everything but these descriptors because when translated we want to see the same structure of the article: Title, Key Ideas, Body, Section Header(s), Banner image, Image Captions. 
    Make sure to translate all the text other than these words (text that comes before or after).
    Do not add any #s / do not bold the text. Return the text in the same format in which it is given.
    For example, in this: Section Header: Caught for its plumage --> Caught for its plumage should be translated but Section Header: should not. Another example: Title: Peru’s modern history of migration and settlement, Peru’s modern history of migration and settlement should be translated but Title: should not be.
    Make sure to translate the bullet points under the Image Captions section.
    To reiterate: every single word in the article should be translated to {target_language} except these phrases: Title, Key Ideas, Body, Section Header(s), Banner image, Image Captions. Everything before and after these phrases should be translated.
    Here is the English text:

    {input_text}
    """

    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=64000,
            temperature=1,
            stream=True,
            system=SYSTEM_TEXT,
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": TRANSLATE_TEXT}]
                }
            ]
        )

        translated_text = ""
        for chunk in response:
            if hasattr(chunk, "delta") and chunk.delta and hasattr(chunk.delta, "text"):
                translated_text += chunk.delta.text

        return translated_text

    except anthropic.AuthenticationError:
        return "Error: Missing or invalid Anthropic API Key."

    except anthropic.BadRequestError as e:
        return f"Error: Bad request - {str(e)}"

    except Exception as e:
        return f"Unexpected error: {str(e)}"



def summarize_text_with_claude(input_text: str, word_count: int) -> str:
    SYSTEM_TEXT = """You are a professional abstract writer. 
    Summarize the core arguments, objectives, findings, and conclusions of the input text in a concise and formal tone, similar to the abstract of a research paper.
    Avoid narrative storytelling or subjective interpretation. Focus on clarity, precision, and a logical structure. 
    Use formal language, passive voice where appropriate, and maintain a neutral tone.
    Ensure the summary is suitable for readers looking to quickly grasp the key points of the original content."""

    SUMMARIZE_TEXT = f"""
    Summarize the following text in approximately {word_count} words.
    
    Here is the text to summarize:

    {input_text}
    """

    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=64000,
            temperature=1,
            stream=True,
            system=SYSTEM_TEXT,
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": SUMMARIZE_TEXT}]
                }
            ]
        )

        summarized_text = ""
        for chunk in response:
            if hasattr(chunk, "delta") and chunk.delta and hasattr(chunk.delta, "text"):
                summarized_text += chunk.delta.text

        return summarized_text

    except anthropic.AuthenticationError:
        return "Error: Missing or invalid Anthropic API Key."

    except anthropic.BadRequestError as e:
        return f"Error: Bad request - {str(e)}"

    except Exception as e:
        return f"Unexpected error: {str(e)}"
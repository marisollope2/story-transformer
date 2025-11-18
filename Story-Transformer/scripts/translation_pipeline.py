import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def translate_structured_text(text: str, target_language: str = "French") -> str:
    """
    Translates a structured article into `target_language`, preserving
    the English labels (e.g. "Title:", "Key Ideas:", etc.) but translating
    everything that follows each colon, plus all other paragraphs/bullets.
    """

    # 1) If no translation needed, just return
    if target_language.lower() == "english" or not text.strip():
        return text

    # 2) Define your labels and corresponding placeholders
    label_to_ph = {
        "Title:":      "<__TITLE__>",
        "Key Ideas:":  "<__KEY_IDEAS__>",
        "Body:":       "<__BODY__>",
        "Section Header:": "<__SECTION_HEADER__>",
        "Banner image:":  "<__BANNER_IMAGE__>",
        "Image Captions:":"<__IMAGE_CAPTIONS__>",
    }

    # 3) Swap each label (only when it appears at start of a line) to its placeholder
    safe_text = text
    for label, ph in label_to_ph.items():
        safe_text = re.sub(rf"(?m)^{re.escape(label)}", ph, safe_text)

    # 4) Build the prompt
    prompt = f"""
Translate the following text into {target_language}.  

🛑 DO NOT translate or alter any of these placeholders:
  {', '.join(label_to_ph.values())}

For any line beginning with a placeholder like <__TITLE__>, translate only what comes *after* it,
and leave the placeholder itself unchanged.

For all other lines (paragraph text, bullets), translate normally.
Preserve ALL line breaks, bullets, and overall formatting. 
Do NOT add Markdown or extra symbols.

BEGIN TEXT
{safe_text}
END TEXT
""".strip()

    # 5) Call the API
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    translated = resp.choices[0].message.content.strip()

    # 6) Restore placeholders back to the English labels
    for label, ph in label_to_ph.items():
        translated = translated.replace(ph, label)

    return translated
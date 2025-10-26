import re
from openai import OpenAI

def get_openai_client(api_key):
    return OpenAI(api_key=api_key)

def translate_structured_text(text: str, target_language: str = "French", api_key=None) -> str:
    if target_language.lower() == "english" or not text.strip():
        return text

    client = get_openai_client(api_key)

    label_to_ph = {
        "Title:": "<__TITLE__>",
        "Key Ideas:": "<__KEY_IDEAS__>",
        "Body:": "<__BODY__>",
        "Section Header:": "<__SECTION_HEADER__>",
        "Banner image:": "<__BANNER_IMAGE__>",
        "Image Captions:": "<__IMAGE_CAPTIONS__>",
    }

    safe_text = text
    for label, ph in label_to_ph.items():
        safe_text = re.sub(rf"(?m)^{re.escape(label)}", ph, safe_text)

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
- Keep quotation marks appropriate for the target language (“…” in English, « … » in French, “…” in Spanish).
- Maintain metric units only (omit imperial conversions like pounds, miles, or °F).
- Do NOT capitalize adjectives indicating regions or directions (e.g., "África occidental" not "África Occidental").
- In Spanish, retain definite articles in headlines when grammatically required (e.g., “la pesca”).
- In French, italicize foreign words if they appear in the source text.
- Do not use symbols such as "+" for approximations; spell them out (e.g., “más de 5500”).
- Avoid literal translations that sound unnatural (e.g., “jugar un papel” → “desempeñar un papel”; “etiquetar” → “llamar”).
- Verify all official names of laws, directives, and institutions using their standard or most common translations.
- If translation fails or encounters unknown language segments, leave them unchanged rather than producing garbled output.

BEGIN TEXT
{safe_text}
END TEXT
""".strip()

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    translated = resp.choices[0].message.content.strip()

    for label, ph in label_to_ph.items():
        translated = translated.replace(ph, label)

    return translated
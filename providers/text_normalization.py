import unicodedata
import re

def normalize_for_bedrock(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    replacements = {
        '\u2018': "'",   # '
        '\u2019': "'",   # '
        '\u201c': '"',   # "
        '\u201d': '"',   # "
        '\u2010': '-',   # HYPHEN
        '\u2011': '-',   # non-breaking hyphen
        '\u2013': '-',   # –
        '\u2014': '-',   # —
        '\u00a0': ' ',   # non-breaking space
        '\u202f': ' ',   # narrow no-breaking space
        '\u2026': '...', # …
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)

    # Strip control chars but keep whitespace
    text = ''.join(
        ch for ch in text
        if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\r", "\t")
    )

    return text
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


def remove_reasoning(text: str) -> str:
    """
    Removes chain-of-thought reasoning from model outputs.
    This is a simpler, more aggressive version that removes common patterns.
    """
    if not text:
        return text
    
    # Remove XML-style tags and content
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<reasoning>.*?</reasoning>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<analysis>.*?</analysis>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove lines that start with common reasoning phrases
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line_lower = line.strip().lower()
        
        # Skip reasoning lines
        if any(phrase in line_lower for phrase in [
            'let me think', 'let me analyze', 'let me consider',
            'here\'s my reasoning', 'here\'s my analysis', 'here\'s my thinking',
            'thinking:', 'reasoning:', 'analysis:', 'thought:',
            'step 1:', 'step 2:', 'step 3:', 'step 4:',
            'first, i\'ll', 'to summarize', 'to translate',
            'i\'ll now', 'i\'ll start', 'before i', 'after analyzing',
            'let\'s think', 'let\'s analyze', 'let\'s consider',
        ]):
            continue
        
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Remove multiple consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
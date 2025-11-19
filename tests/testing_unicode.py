import os
import sys

# Make sure project root is on path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from providers.text_normalization import normalize_for_bedrock
from scripts.summarization_pipeline import summarize_and_translate

# String full of Unicode:
TEST_TEXT = (
    "“The most significant finding is that 50% of the conflicts with companies "
    "from the Global North occur in the Global South,” Llavero-Pasquina said — "
    "using curly quotes, an em dash — a non-breaking hyphen, ellipsis… and a non-breaking space:"
    "\u00a0"
    "END."
)

def main():
    print("=== RAW TEXT ===")
    print(TEST_TEXT)
    print("\nRAW repr() ===")
    print(repr(TEST_TEXT))

    print("\n=== NORMALIZED TEXT ===")
    normalized = normalize_for_bedrock(TEST_TEXT)
    print(normalized)
    print("\nNORMALIZED repr() ===")
    print(repr(normalized))

    print("\n=== BEDROCK SUMMARY (ENGLISH) ===")
    summary = summarize_and_translate(
        TEST_TEXT,
        word_limit=80,
        language="Spanish",
        use_bedrock=True,
    )
    print(summary)

if __name__ == "__main__":
    main()

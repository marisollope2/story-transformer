import os
import sys

# Make sure project root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from scripts.summarization_pipeline import summarize_and_translate
from providers.bedrock_translation import translate_simple_text, translate_structured_text


SAMPLE_TEXT = """
A recent study has found that just 104 companies, mostly multinational corporations
from high-income countries, are involved in a fifth of more than 3,000 environmental conflicts.
The analysis highlights disproportionate impacts on Indigenous and marginalized communities.
"""


def check_no_reasoning(label: str, text: str) -> None:
    """Utility to check and print whether <reasoning> appears."""
    has_reasoning = "<reasoning>" in text or "</reasoning>" in text
    if has_reasoning:
        print(f"❌ {label}: FOUND <reasoning> in output!")
    else:
        print(f"✅ {label}: no <reasoning> found.")


def main():
    print("=== TESTING SUMMARY (ENGLISH) ===")
    summary_en = summarize_and_translate(
        SAMPLE_TEXT,
        word_limit=120,
        language="English",
        use_bedrock=True,
    )
    check_no_reasoning("Summary EN", summary_en)

    print("\n=== TESTING SUMMARY (SPANISH) ===")
    summary_es = summarize_and_translate(
        SAMPLE_TEXT,
        word_limit=120,
        language="Spanish",
        use_bedrock=True,
    )
    check_no_reasoning("Summary ES", summary_es)

    print("\n=== TESTING SIMPLE TRANSLATION (SPANISH) ===")
    simple_es = translate_simple_text(
        SAMPLE_TEXT,
        target_language="Spanish",
    )
    check_no_reasoning("translate_simple_text ES", simple_es)

    print("\n=== TESTING STRUCTURED TRANSLATION (SPANISH) ===")
    structured_input = "Title: Test article\n\nBody:\n" + SAMPLE_TEXT
    structured_es = translate_structured_text(
        structured_input,
        target_language="Spanish",
    )
    check_no_reasoning("translate_structured_text ES", structured_es)

    print("\n=== SAMPLE OUTPUT (SPANISH SUMMARY) ===")
    print(summary_es[:600])  # show a snippet just to eyeball it


if __name__ == "__main__":
    main()

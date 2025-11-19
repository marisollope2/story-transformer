import os
import sys

# Make sure project root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from scripts.extract import extract_article
from scripts.summarization_pipeline import summarize_and_translate


def main():
    # Ask for the URL so you can reuse this script for any article
    url = input("Enter article URL: ").strip()
    if not url:
        print("No URL provided, exiting.")
        return

    print("\n=== FETCHING ARTICLE ===")
    article_text = extract_article(url)
    print(f"Article length: {len(article_text)} characters")

    print("\n=== ARTICLE SNIPPET (FIRST 500 CHARS) ===")
    print(article_text[:500])

    print("\n=== ENGLISH SUMMARY ===")
    summary_en = summarize_and_translate(
        article_text,
        word_limit=150,
        language="English",
        use_bedrock=True,   # important: this forces the Bedrock path
    )
    print(summary_en)

    print("\n=== SPANISH SUMMARY ===")
    summary_es = summarize_and_translate(
        article_text,
        word_limit=150,
        language="Spanish",
        use_bedrock=True,
    )
    print(summary_es)


if __name__ == "__main__":
    main()

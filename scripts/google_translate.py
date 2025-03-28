import os
import re
from deep_translator import GoogleTranslator

input_folder = "../extracted"
output_folder = "../translations-google"
os.makedirs(output_folder, exist_ok=True)

# Translate from English to Spanish
translator = GoogleTranslator(source="auto", target="spanish")

# GoogleTranslate api has 5000 characters limit. Split long text into smaller chunks
def split_and_translate(text):
    chunks = []
    max_len = 5000
    while len(text) > max_len:
        # Split on the last period to avoid breaking sentences
        split_index = text.rfind(". ", 0, max_len) + 1
        # Only if no periods are found
        if split_index <= 0:
            split_index = text.rfind(" ", 0, max_len)
            if split_index == -1:
                split_index = max_len
        chunks.append(text[:split_index].strip())
        text = text[split_index:].strip()
    if text:
        chunks.append(text)
    translations = [translator.translate(chunk) for chunk in chunks]
    return "\n".join(translations)

# Translate all files that has "English" in the filename
for filename in os.listdir(input_folder):
    if "English" in filename and filename.endswith(".txt"):
        input_path = os.path.join(input_folder, filename)
        spanish_filename = filename.replace("English", "Spanish").replace("_extracted", "")
        output_path = os.path.join(output_folder, spanish_filename)

        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        translated_lines = []
        heading = []

        for line in lines:
            stripped = line.strip()

            # Keep section headers in English and joins all body of section headers together
            if stripped.endswith(":") and not stripped.startswith("-"):
                if heading:
                    combined_text = " ".join(heading).strip()
                    if combined_text:
                        translated = split_and_translate(combined_text)
                        translated_lines.append(translated + "\n")
                    heading = []
                translated_lines.append(line)
            else:
                heading.append(stripped)

        if heading:
            combined_text = " ".join(heading).strip()
            if combined_text:
                translated = split_and_translate(combined_text)
                translated_lines.append(translated + "\n")

        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(translated_lines)

        print(f"Saved to: {os.path.basename(output_path)}")

import os
from deep_translator import GoogleTranslator

input_folder = "../extracted"
output_folder = "../translations-google"
os.makedirs(output_folder, exist_ok=True)

# Translate from English to Spanish
translator = GoogleTranslator(source="auto", target="spanish")

# GoogleTranslate API has a 5000-character limit. Split long text into smaller chunks.
def split_and_translate(text):
    chunks = []
    max_len = 5000
    while len(text) > max_len:
        # Split on the last period to avoid breaking sentences
        split_index = text.rfind(". ", 0, max_len) + 1
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

# Section headers to keep in English
section_headers_to_preserve = ["Title:", "Section:", "Section Header:"]

# Translate all files that have "English" in the filename
for filename in os.listdir(input_folder):
    if "English" in filename and filename.endswith(".txt"):
        input_path = os.path.join(input_folder, filename)
        spanish_filename = filename.replace("English", "Spanish").replace("_extracted", "")
        output_path = os.path.join(output_folder, spanish_filename)

        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        translated_lines = []
        heading = []
        previous_was_header = False  # Track whether the last line was a header

        for line in lines:
            stripped = line.strip()

            # Check if the line is a section header that should stay in English
            if any(stripped.startswith(header) for header in section_headers_to_preserve):
                if heading:
                    combined_text = " ".join(heading).strip()
                    if combined_text:
                        translated = split_and_translate(combined_text)
                        translated_lines.append(translated + "\n")
                    heading = []

                # Ensure proper spacing before section headers
                if translated_lines:
                    translated_lines.append("\n")
                translated_lines.append(line.strip() + "\n")
                translated_lines.append("\n")  # Extra space for readability
                previous_was_header = True

            # Check if it's another heading (e.g., "Title:", "Body:", etc.)
            elif stripped.endswith(":") and not stripped.startswith("-"):
                if heading:
                    combined_text = " ".join(heading).strip()
                    if combined_text:
                        translated = split_and_translate(combined_text)
                        translated_lines.append(translated + "\n")
                    heading = []

                # Ensure proper spacing before and after headings
                if translated_lines:
                    translated_lines.append("\n\n")  # Extra spacing for sections
                translated_lines.append(line.strip() + "\n")
                translated_lines.append("\n")  # Extra space for readability
                previous_was_header = True

            # Handle bullet points (keep "-" and translate content)
            elif stripped.startswith("-"):
                if heading:
                    combined_text = " ".join(heading).strip()
                    if combined_text:
                        translated = split_and_translate(combined_text)
                        translated_lines.append(translated + "\n")
                    heading = []

                translated_lines.append(f"- {split_and_translate(stripped[1:].strip())}\n")
                previous_was_header = False

            # Otherwise, it's body text that should be translated
            else:
                heading.append(stripped)
                previous_was_header = False

        # Translate any remaining body text at the end
        if heading:
            combined_text = " ".join(heading).strip()
            if combined_text:
                translated = split_and_translate(combined_text)
                translated_lines.append(translated + "\n")

        # Remove excessive blank lines for cleaner formatting
        formatted_output = "\n".join(line.strip() for line in translated_lines if line.strip()) + "\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_output)

        print(f"Saved to: {os.path.basename(output_path)}")

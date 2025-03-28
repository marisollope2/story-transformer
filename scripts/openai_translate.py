import os
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

input_folder = os.path.join("..", "extracted")
output_folder = os.path.join("..", "translations-openai")
os.makedirs(output_folder, exist_ok=True)

# Translate text using OpenAI's GPT model
def translate(text):
    if not text.strip():
        return ""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional Spanish-language science and environmental journalist. "
                    "You write with clarity and impact for general Latin American audiences. "
                    "Use natural phrasing and journalistic tone."
                )
            },
            {
                "role": "user",
                "content": f"Translate the following English text to Spanish:\n\n{text}"
            }
        ]
    )
    return response.choices[0].message.content.strip()

def parse_and_translate(filepath):
    sections = {
        "title": "",
        "key_ideas": [],
        "body_lines": [],
        "correction": "",
        "image_captions": []
    }

    # Split translations by section.
    header = None
    body_started = False # to check if current section is a body since it is long

    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            stripped = line.strip()
            if stripped.startswith("Title:"):
                header = "title"
                sections["title"] = stripped.replace("Title:", "").strip()
            elif stripped.startswith("Key Ideas:"):
                header = "key_ideas"
            elif stripped.startswith("Body:"):
                header = "body"
                body_started = True
                continue
            elif stripped.startswith("Image Captions:"):
                header = "image_captions"
                body_started = False
            elif "CORRECTION" in stripped:
                header = "correction"
                sections["correction"] = stripped
                body_started = False
            elif header == "key_ideas" and stripped.startswith("-"):
                sections["key_ideas"].append(stripped[1:].strip())
            elif header == "image_captions" and stripped.startswith("-"):
                sections["image_captions"].append(stripped[1:].strip())
            elif body_started:
                sections["body_lines"].append(stripped)

    # Translate each section
    translated = {
        "title": translate(sections["title"]),
        "key_ideas": [translate(k) for k in sections["key_ideas"]],
        "body": translate("\n\n".join(sections["body_lines"])),
        "correction": translate(sections["correction"]),
        "image_captions": [translate(c) for c in sections["image_captions"]]
    }

    return translated

# Put as .txt file
def write_translated_txt(translated, output_path):
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write(f"Title: {translated['title']}\n\n")

        out.write("Key Ideas:\n")
        for idea in translated["key_ideas"]:
            out.write(f"- {idea}\n")

        out.write("\nBody:\n")
        out.write(translated["body"] + "\n")

        if translated["correction"]:
            out.write(f"\n\n{translated['correction']}\n")

        if translated["image_captions"]:
            out.write("\nImage Captions:\n")
            for cap in translated["image_captions"]:
                out.write(f"- {cap}\n")

# Loop through all English files
for filename in os.listdir(input_folder):
    if "English" in filename and filename.endswith(".txt"):
        input_path = os.path.join(input_folder, filename)
        output_filename = filename.replace("English", "Spanish").replace("_extracted", "")
        output_path = os.path.join(output_folder, output_filename)

        translated_content = parse_and_translate(input_path)
        write_translated_txt(translated_content, output_path)
        print(f"Saved to: {output_filename}")

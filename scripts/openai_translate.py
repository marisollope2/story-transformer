import os
from dotenv import load_dotenv
from openai import OpenAI


# Load API key from .env file
load_dotenv()
client = OpenAI(api_key="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")


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


   header = None
   body_started = False 


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
           elif stripped.startswith("Section:") or stripped.startswith("Section Header:"):
               header_label = "Section:" if stripped.startswith("Section:") else "Section Header:"
               header_content = stripped[len(header_label):].strip()
               sections["body_lines"].append((header_label, header_content))  # Store as tuple
           elif header == "key_ideas" and stripped.startswith("-"):
               sections["key_ideas"].append(stripped[1:].strip())
           elif header == "image_captions" and stripped.startswith("-"):
               sections["image_captions"].append(stripped[1:].strip())
           elif body_started:
               sections["body_lines"].append(stripped)


   # Translate each section except section headers
   translated = {
       "title": translate(sections["title"]),
       "key_ideas": [translate(k) for k in sections["key_ideas"]],
       "body": [],  # We'll build this while preserving section headers
       "correction": translate(sections["correction"]),
       "image_captions": [translate(c) for c in sections["image_captions"]]
   }


   for line in sections["body_lines"]:
       if isinstance(line, tuple):  # This is a section header
           label, content = line
           translated_content = translate(content)
           translated["body"].append(f"{label} {translated_content}")
       else:
           translated["body"].append(translate(line))




   return translated


# Write translated content to .txt file
def write_translated_txt(translated, output_path):
   with open(output_path, 'w', encoding='utf-8') as out:
       out.write(f"Title: {translated['title']}\n\n")


       out.write("Key Ideas:\n")
       for idea in translated["key_ideas"]:
           out.write(f"- {idea}\n")


       out.write("\nBody:\n")
       for line in translated["body"]:
           out.write(line + "\n")


       if translated["correction"]:
           out.write(f"\n\n{translated['correction']}\n")


       if translated["image_captions"]:
           out.write("\nImage Captions:\n")
           for cap in translated["image_captions"]:
               out.write(f"- {cap}\n")


# Process all English files in the input folder
for filename in os.listdir(input_folder):
   if "English" in filename and filename.endswith(".txt"):
       input_path = os.path.join(input_folder, filename)
       output_filename = filename.replace("English", "Spanish").replace("_extracted", "")
       output_path = os.path.join(output_folder, output_filename)


       translated_content = parse_and_translate(input_path)
       write_translated_txt(translated_content, output_path)
       print(f"Saved to: {output_filename}")




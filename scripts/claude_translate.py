# HOW TO RUN: python3 claude_translate.py "file_name" (ex: python3 claude_translate.py claude_texts/file1.txt)
import anthropic
import os
import argparse

client = anthropic.Anthropic()

file_path = 'claude_texts/file1.txt'

parser = argparse.ArgumentParser(description="Process a text file.")
parser.add_argument("file_path", help="Path to the input text file")

args = parser.parse_args()
file_path = args.file_path

if not os.path.exists(file_path):
    print(f"Error: Input file '{file_path}' not found")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as file:
    text_data = file.read()

if not text_data.strip():
    print("Error: Input file is empty")
    exit(1)

print(f"Found input file with {len(text_data)} characters")

SYSTEM_TEXT = "You are a professional Spanish-language science and environmental journalist. You write with clarity and impact for general Latin American audiences. Use natural phrasing and journalistic tone."

TRANSLATE_TEXT = f"""
Translate the following English text to Spanish.
Keep the same structure of the article. 
Translate everything but these words: Title, Key Ideas, Body, Section Header(s), Banner image, Image Captions. 
Make sure to translate all the text other than these words (text that comes before or after). 
For example, in this: Section Header: Caught for its plumage --> Caught for its plumage should be translated but Section Header: should not. Another example: Title: Peru’s modern history of migration and settlement, Peru’s modern history of migration and settlement should be translated but Title: should not be.
Make sure to translate the bullet points under the Image Captions section.
Here is the English text:
{text_data}
"""

try:
    print("Starting API call...")
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=64000,
        stream=True,
        temperature=1,
        system=SYSTEM_TEXT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": TRANSLATE_TEXT
                    }
                ]
            }
        ]
    )

    translated_text = ""
    chunk_count = 0
    
    print("Processing streaming response...")
    for chunk in message:
        chunk_count += 1
        print(f"Chunk {chunk_count} type: {chunk.type}")
        
        if chunk.type == "content_block_delta" and hasattr(chunk.delta, 'text') and chunk.delta.text:
            translated_text += chunk.delta.text
            if chunk_count % 50 == 0:
                print(f"Processed {chunk_count} chunks, current text length: {len(translated_text)}")
    
    print(f"Finished processing {chunk_count} chunks")
    print(f"Final translated text length: {len(translated_text)}")
    
    if not translated_text.strip():
        print("Warning: Translated text is empty!")
        print("Trying non-streaming approach instead...")
        
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=64000,
            stream=False,
            temperature=1,
            system=SYSTEM_TEXT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": TRANSLATE_TEXT
                        }
                    ]
                }
            ]
        )
        
        translated_text = message.content[0].text
        print(f"Non-streaming approach result length: {len(translated_text)}")

    base_dir = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}_translated{ext}"
    new_file_path = os.path.join(base_dir, new_filename)

    with open(new_file_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)

    if os.path.exists(new_file_path):
        file_size = os.path.getsize(new_file_path)
        print(f"Translated text saved to: {new_file_path} (Size: {file_size} bytes)")
        
        with open(new_file_path, 'r', encoding='utf-8') as f:
            preview = f.read(100)
            print(f"File preview: {preview}...")
    else:
        print(f"Error: Failed to create output file {new_file_path}")

except Exception as e:
    print(f"Error during translation: {str(e)}")
    import traceback
    traceback.print_exc()
import anthropic
import os

client = anthropic.Anthropic()

file_path = 'english_texts/file1.txt'

if not os.path.exists(file_path):
    print(f"Error: Input file '{file_path}' not found")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as file:
    text_data = file.read()

if not text_data.strip():
    print("Error: Input file is empty")
    exit(1)

print(f"Found input file with {len(text_data)} characters")

SYSTEM_TEXT = "You are a professional abstract writer. Summarize the core arguments, objectives, findings, and conclusions of the input text in a concise and formal tone, similar to the abstract of a research paper. Avoid narrative storytelling or subjective interpretation. Focus on clarity, precision, and a logical structure. Use formal language, passive voice where appropriate, and maintain a neutral tone. Keep the summary around 200 words and suitable for readers looking to quickly grasp the key points of the original content."

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
                        "text": f"Summarize this text:\n{text_data}"
                    }
                ]
            }
        ]
    )

    summarized_text = ""
    chunk_count = 0
    
    print("Processing streaming response...")
    for chunk in message:
        chunk_count += 1
        print(f"Chunk {chunk_count} type: {chunk.type}")
        
        if chunk.type == "content_block_delta" and hasattr(chunk.delta, 'text') and chunk.delta.text:
            summarized_text += chunk.delta.text
            if chunk_count % 50 == 0:
                print(f"Processed {chunk_count} chunks, current text length: {len(summarized_text)}")
    
    print(f"Finished processing {chunk_count} chunks")
    print(f"Final Summarized text length: {len(summarized_text)}")
    
    if not summarized_text.strip():
        print("Warning: Summarized text is empty!")
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
                            "text": f"Summarize this text:\n{text_data}"
                        }
                    ]
                }
            ]
        )
        
        summarized_text = message.content[0].text
        print(f"Non-streaming approach result length: {len(summarized_text)}")

    base_dir = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}_summarized{ext}"
    new_file_path = os.path.join(base_dir, new_filename)

    with open(new_file_path, 'w', encoding='utf-8') as f:
        f.write(summarized_text)

    if os.path.exists(new_file_path):
        file_size = os.path.getsize(new_file_path)
        print(f"Summarized text saved to: {new_file_path} (Size: {file_size} bytes)")
        
        with open(new_file_path, 'r', encoding='utf-8') as f:
            preview = f.read(100)
            print(f"File preview: {preview}...")
    else:
        print(f"Error: Failed to create output file {new_file_path}")

except Exception as e:
    print(f"Error during summarization: {str(e)}")
    import traceback
    traceback.print_exc()
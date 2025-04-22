import os
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# input_folder = os.path.join("..", "extracted")
# output_folder = os.path.join("..", "summarizations-openai-narrative")
# os.makedirs(output_folder, exist_ok=True)

# Summarize text using OpenAI's GPT model
def summarize_text_simple(text, word_limit=200):
    if not text.strip():
        return ""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant that summarizes text clearly and concisely. Focus on capturing the main ideas and supporting details without copying exact phrasing."
                    f"Use natural, easy-to-understand language, and organize the summary in a logical flow. The summary should be around {word_limit} words."

                )
            },

            {
                "role": "user",
                "content": f"Summarize this text:\n\n{text}"
            }
        ]
    )
    return response.choices[0].message.content.strip()

def summarize_text_narrative(text, word_limit=200):
    if not text.strip():
        return ""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a skilled writer who summarizes text in a clear and narrative style. "
                    "Preserve the logical flow and tone of the original text. Use transitions to make the summary feel cohesive."
                    f"Keep the summary around {word_limit} words, while capturing the essence behind the content."
                )
            },

            {
                "role": "user",
                "content": f"Summarize this text:\n\n{text}"
            }
        ]
    )
    return response.choices[0].message.content.strip()


def summarize_text_abstract(text, word_limit=200):
    if not text.strip():
        return ""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional abstract writer. Summarize the core arguments, objectives, findings, and conclusions of the input text in a concise and formal tone, similar to the abstract of a research paper. "
                    "Avoid narrative storytelling or subjective interpretation. Focus on clarity, precision, and a logical structure. "
                    "Use formal language, passive voice where appropriate, and maintain a neutral tone. "
                    f"Keep the summary around {word_limit} words and suitable for readers looking to quickly grasp the key points of the original content."

                )
            },

            {
                "role": "user",
                "content": f"Summarize this text:\n\n{text}"
            }
        ]
    )
    return response.choices[0].message.content.strip()


# Summarize text
def main(word_limit=200):
    input_folder = os.path.join("..", "extracted")
    output_folder = os.path.join("..", f"summarizations-openai-narrative-{word_limit}")
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if "English" in filename and filename.endswith(".txt"):
            input_path = os.path.join(input_folder, filename)
            output_filename = filename.replace("_extracted", "")
            output_path = os.path.join(output_folder, output_filename)

            with open(input_path, 'r', encoding='utf-8') as file:
                text = file.read()
            summary = summarize_text_narrative(text, word_limit=word_limit)
            with open(output_path, 'w', encoding='utf-8') as out:
                out.write(summary)
            print(f"Saved to: {output_filename}")


if __name__ == "__main__":
    main(300)
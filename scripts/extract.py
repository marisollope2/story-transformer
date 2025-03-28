# Script that processes every text file in the texts folder and saves the extracted content into the extracted folder.
import os
import re
from bs4 import BeautifulSoup

input_folder = "/texts"
output_folder = "/extracted"

os.makedirs(output_folder, exist_ok=True)

# regexs to stop from capturing unwanted information
stop_patterns = [
    re.compile(r'^If you liked this story, share it with other people\.', re.IGNORECASE),
    re.compile(r'^Citations?:', re.IGNORECASE),
    re.compile(r'^Feedback:', re.IGNORECASE),
    re.compile(r'^Use this form', re.IGNORECASE),
    re.compile(r'^Documentary films', re.IGNORECASE),
    re.compile(r'^© ?\d{4}', re.IGNORECASE),
    re.compile(r'^You(’|\'|’)re currently offline', re.IGNORECASE),
    re.compile(r'^Share this article', re.IGNORECASE),
]

def is_stop_paragraph(text):
    """Checks if the paragraph matches any stop pattern."""
    return any(pattern.match(text) for pattern in stop_patterns)

# Loop through all .txt files in the texts folder
for filename in os.listdir(input_folder):
    if filename.endswith(".txt"):  # Process only text files
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_extracted.txt")

        with open(input_path, 'r', encoding='utf-8') as file:
            content = file.read()

        soup = BeautifulSoup(content, 'html.parser')

        # extracting title
        h1_tag = soup.find('h1')
        title = h1_tag.get_text(strip=True) if h1_tag else soup.title.string.strip()

        # extracting key ideas
        bullet_points = []
        bullet_wrapper = soup.find('div', class_='bulletpoints-wrapper')
        if bullet_wrapper:
            bullets = bullet_wrapper.find_all('li')
            bullet_points = [li.get_text(strip=True) for li in bullets]

        # extracting body + section headers
        article_body = soup.find('div', class_='article-body') or soup.find('article')
        if article_body:
            content_elements = article_body.find_all(['p', 'h3'])
        else:
            content_elements = soup.find_all(['p', 'h3'])

        body_paragraphs = []

        for i, element in enumerate(content_elements):
            text = element.get_text(strip=True)

            if not text or text in bullet_points:
                continue

            if is_stop_paragraph(text):
                break

            if element.name == 'h3':  
                body_paragraphs.append(f"Section Header: {text}")
            else:
                if i > len(content_elements) - 8:
                    word_count = len(text.split())
                    if word_count < 15 and not re.search(r'[.!?]$', text):
                        continue
                
                body_paragraphs.append(text)

        body_text = '\n\n'.join(body_paragraphs)

        # extract image captions
        captions = []
        for img in soup.find_all('img'):
            caption = None
            parent = img.find_parent()
            if parent:
                figcaption = parent.find('figcaption')
                if figcaption:
                    caption = figcaption.get_text(strip=True)
            if not caption:
                next_p = img.find_next_sibling('p')
                if next_p:
                    caption = next_p.get_text(strip=True)
            if caption:
                captions.append(caption)

        # save output to new file (og file name + _extracted)
        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(f"Title: {title}\n\n")

            out_file.write("Key Ideas:\n")
            for bp in bullet_points:
                out_file.write(f"- {bp}\n")
            out_file.write("\n")

            out_file.write("Body:\n")
            out_file.write(body_text if body_text.strip() else "No body found.\n")
            out_file.write("\n\n")

            out_file.write("Image Captions:\n")
            for cap in captions:
                out_file.write(f"- {cap}\n")

        print(f"Saved: {output_path}")  # Print progress
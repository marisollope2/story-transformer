import re
import requests
from bs4 import BeautifulSoup

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
    return any(pattern.match(text) for pattern in stop_patterns)

def extract_article(url):
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/123.0.0.0 Safari/537.36'
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch article: {e}")

    content = response.text
    soup = BeautifulSoup(content, 'html.parser')

    h1_tag = soup.find('h1')
    title = h1_tag.get_text(strip=True) if h1_tag else soup.title.string.strip() if soup.title else "No title found"

    bullet_points = []
    bullet_wrapper = soup.find('div', class_='bulletpoints-wrapper')
    if bullet_wrapper:
        bullets = bullet_wrapper.find_all('li')
        bullet_points = [li.get_text(strip=True) for li in bullets]

    article_containers = [
        'article-body', 'article', 'content', 'post-content', 
        'entry-content', 'main-content', 'story', 'post', 
        'article-content', 'story-body'
    ]
    
    article_body = None
    for container in article_containers:
        article_body = soup.find('div', class_=container) or soup.find('article', class_=container)
        if article_body:
            break

    if not article_body:
        article_body = soup.find('article') or soup.find('main')
    
    if not article_body:
        article_body = soup.body

    all_elements = []
    for element in article_body.find_all(['h2', 'h3', 'p']) if article_body else soup.find_all(['h2', 'h3', 'p']):
        all_elements.append(element)

    body_paragraphs = []
    for i, element in enumerate(all_elements):
        text = element.get_text(strip=True)
        if not text or text in bullet_points or is_stop_paragraph(text):
            continue

        if element.name in ['h2', 'h3']:
            body_paragraphs.append(f"Section Header: {text}")
        else:
            if i > len(all_elements) - 8:
                word_count = len(text.split())
                if word_count < 15 and not re.search(r'[.!?]$', text):
                    continue
            body_paragraphs.append(text)

    list_items = []
    for ul in article_body.find_all('ul') if article_body else soup.find_all('ul'):
        parent_classes = ' '.join(ul.parent.get('class', []) if ul.parent else [])
        if (ul.find_parent('nav') or 
            'menu' in ul.get('class', []) or 
            'nav' in ul.get('class', []) or
            'footer' in parent_classes or
            'menu' in parent_classes):
            continue
        
        for li in ul.find_all('li'):
            item_text = li.get_text(strip=True)
            if item_text and len(item_text) > 10:
                list_items.append(f"- {item_text}")

    captions = []
    for img in article_body.find_all('img') if article_body else soup.find_all('img'):
        caption = None
        parent = img.find_parent('figure')
        if parent:
            figcaption = parent.find('figcaption')
            if figcaption:
                caption = figcaption.get_text(strip=True)
        
        if not caption:
            for sibling in img.next_siblings:
                if sibling.name in ['p', 'div', 'span'] and sibling.get_text(strip=True):
                    sibling_classes = ' '.join(sibling.get('class', []))
                    if ('caption' in sibling_classes or 
                        'figcaption' in sibling_classes or
                        len(sibling.get_text(strip=True)) < 100):
                        caption = sibling.get_text(strip=True)
                        break
        
        if caption:
            captions.append(caption)

    output_text = f"Title: {title}\n\n"
    if bullet_points:
        output_text += "Key Ideas:\n" + "\n".join(f"- {bp}" for bp in bullet_points) + "\n\n"
    
    if list_items and not bullet_points:
        output_text += "Key Points:\n" + "\n".join(list_items) + "\n\n"
    
    output_text += "Body:\n" + '\n\n'.join(body_paragraphs)
    
    if captions:
        output_text += "\n\nImage Captions:\n" + "\n".join(f"- {cap}" for cap in captions)

    return output_text
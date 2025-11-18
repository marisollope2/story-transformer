"""
File extraction utilities for various file formats
Supports .txt, .docx, and Google Docs
"""
import io
import re
from typing import Optional


def extract_text_from_file(uploaded_file) -> str:
    """
    Extract text from uploaded file based on file extension.
    
    Args:
        uploaded_file: Streamlit uploaded file object
    
    Returns:
        Extracted text as string
    """
    filename = uploaded_file.name.lower()
    
    if filename.endswith('.txt'):
        return extract_text_from_txt(uploaded_file)
    elif filename.endswith('.docx'):
        return extract_text_from_docx(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Supported types: .txt, .docx")


def extract_text_from_txt(uploaded_file) -> str:
    """Extract text from .txt file"""
    return uploaded_file.read().decode("utf-8")


def extract_text_from_docx(uploaded_file) -> str:
    """Extract text from .docx file"""
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "python-docx is required for .docx files. Install it with: pip install python-docx"
        )
    
    # Read the file into memory
    file_bytes = uploaded_file.read()
    doc = Document(io.BytesIO(file_bytes))
    
    # Extract text with structure
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            # Check if it's a heading
            if para.style.name.startswith('Heading'):
                level = para.style.name.replace('Heading', '').strip()
                if level.isdigit():
                    paragraphs.append(f"Section Header: {text}")
                else:
                    paragraphs.append(f"Title: {text}")
            else:
                paragraphs.append(text)
    
    # Extract tables
    tables_text = []
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                tables_text.append(row_text)
    
    # Combine all text
    full_text = "\n\n".join(paragraphs)
    if tables_text:
        full_text += "\n\nTables:\n" + "\n".join(tables_text)
    
    return full_text


def extract_from_google_docs_url(url: str) -> Optional[str]:
    """
    Extract text from Google Docs URL.
    
    Note: This requires the document to be publicly accessible or requires
    Google API authentication. For private docs, export as .docx first.
    
    Args:
        url: Google Docs URL
    
    Returns:
        Extracted text or None if extraction fails
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("requests and beautifulsoup4 are required for Google Docs extraction")
    
    # Convert Google Docs URL to export format
    # Replace /edit with /export?format=html or /export?format=txt
    if '/edit' in url:
        export_url = url.replace('/edit', '/export?format=txt')
    elif '/view' in url:
        export_url = url.replace('/view', '/export?format=txt')
    else:
        # Try to construct export URL
        doc_id = extract_google_doc_id(url)
        if doc_id:
            export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        else:
            raise ValueError("Invalid Google Docs URL format")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(export_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # If it's HTML, parse it
        if 'html' in response.headers.get('content-type', '').lower():
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text(separator='\n\n', strip=True)
        else:
            return response.text
        
    except requests.exceptions.RequestException as e:
        raise Exception(
            f"Failed to extract from Google Docs. "
            f"The document may be private. Try exporting it as .docx and uploading instead. "
            f"Error: {str(e)}"
        )


def extract_google_doc_id(url: str) -> Optional[str]:
    """Extract document ID from Google Docs URL"""
    # Pattern: /d/{DOC_ID}/
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None


def is_google_docs_url(url: str) -> bool:
    """Check if URL is a Google Docs URL"""
    return 'docs.google.com/document' in url.lower()


import streamlit as st
import sys
import os
import traceback
from fpdf import FPDF
from io import BytesIO
import unicodedata, re
from fpdf.enums import XPos, YPos
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.extract import extract_article
from scripts.file_extractor import (
    extract_text_from_file, 
    extract_from_google_docs_url, 
    is_google_docs_url
)
from providers.bedrock_editor import refine_with_chat

st.set_page_config(
    page_title="Story Transformer",
    layout="wide"
)

def sanitize_line(text):
    # Replace problematic Unicode characters with ASCII equivalents
    text = text.replace('\u2011', '-')  # Non-breaking hyphen
    text = text.replace('\u2019', "'").replace('\u201C', '"').replace('\u201D', '"')
    text = text.replace('\u2018', "'").replace('\u2013', '-').replace('\u2014', '--')
    text = text.replace('\u2026', '...')  # Ellipsis
    text = text.replace('\u00A0', ' ')  # Non-breaking space
    # Remove control characters but keep printable Unicode
    text = ''.join(c for c in text if unicodedata.category(c)[0] != "C" or c == '\n')
    text = re.sub(r'(\S{25,})', lambda m: ' '.join([m.group(1)[i:i+25] for i in range(0, len(m.group(1)), 25)]), text)
    return text


def create_pdf(text):
    class PDF(FPDF):
        def header(self):
            pass
        def footer(self):
            pass

    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # Sanitize text first to replace problematic Unicode characters
    text = sanitize_line(text)
    
    # Use Helvetica (standard font) - text is already sanitized
    pdf.set_font("Helvetica", size=10)

    paragraphs = text.split('\n')

    for paragraph in paragraphs:
        if not paragraph.strip():
            pdf.ln(5)
            continue
        words = paragraph.split()
        line = ""
        for word in words:
            if len(word) > 30:
                word = word[:30] + "..."
            test_line = line + " " + word if line else word
            if pdf.get_string_width(test_line) > (pdf.w - 2 * pdf.l_margin - 10):
                if line:
                    try:
                        pdf.cell(0, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    except Exception as e:
                        print(f"Error writing line: {e}")
                    line = word
                else:
                    continue
            else:
                line = test_line
        if line:
            try:
                pdf.cell(0, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(3)
            except Exception as e:
                print(f"Error writing final line: {e}")

    pdf_output = BytesIO()
    try:
        pdf.output(pdf_output)
        pdf_output.seek(0)
        return pdf_output
    except Exception as e:
        print(f"PDF generation failed: {e}")
        fallback = FPDF()
        fallback.add_page()
        fallback.set_font("Helvetica", size=12)
        fallback.cell(0, 10, "PDF generation failed.")
        fallback_output = BytesIO()
        fallback.output(fallback_output)
        fallback_output.seek(0)
        return fallback_output


# Logo
logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "logo.png"))
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.image(logo)

st.title("Story Transformer")

# Check AWS credentials status
st.sidebar.subheader("☁️ AWS Bedrock Configuration")
aws_configured = False
try:
    import boto3
    session = boto3.Session()
    credentials = session.get_credentials()
    if credentials:
        st.sidebar.success("✅ AWS credentials configured")
        region = session.region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        st.sidebar.info(f"Region: {region}")
        aws_configured = True
    else:
        st.sidebar.warning("⚠️ AWS credentials not found")
        st.sidebar.info("Configure using: `aws configure`")
except Exception as e:
    st.sidebar.error("❌ AWS configuration error")
    st.sidebar.info(f"Error: {str(e)}")

if not aws_configured:
    st.warning("⚠️ **AWS credentials not configured.** Please configure AWS credentials using `aws configure` before using this app.")

# Show available models info
with st.sidebar.expander("ℹ️ About Models"):
    st.write("""
    This app uses AWS Bedrock models for:
    - **Translation**: Automatically selects best model for target language
    - **Summarization**: Uses optimized summarization models
    - **Editing**: Refines text based on your requests
    
    Models are automatically selected based on your account access.
    """)

# Initialize session state
if "original_text" not in st.session_state:
    st.session_state.original_text = ""
if "current_text" not in st.session_state:
    st.session_state.current_text = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Main interface
if not st.session_state.original_text:
    # Initial input page
    st.header("📝 Enter Your Content")
    st.info("""
    You can input content in any of these ways:
    - **Paste a Google Docs link** (public docs only)
    - **Paste an article URL** (web article)
    - **Upload a .docx file** (Word document)
    - **Type or paste plain text** directly
    """)
    
    # Input method selector
    input_method = st.radio(
        "Choose input method:",
        ["Plain Text", "Google Docs Link", "Article URL", "Upload .docx File"],
        horizontal=True
    )
    
    article_text = ""
    
    if input_method == "Plain Text":
        article_text = st.text_area(
            "Enter or paste your text:",
            height=300,
            placeholder="Type or paste your text here..."
        )
    
    elif input_method == "Google Docs Link":
        docs_url = st.text_input(
            "Paste Google Docs link:",
            placeholder="https://docs.google.com/document/d/..."
        )
        if docs_url:
            try:
                article_text = extract_from_google_docs_url(docs_url)
                st.success("✅ Successfully extracted from Google Docs!")
            except Exception as e:
                st.error(f"Failed to extract from Google Docs: {str(e)}")
                st.info("💡 **Tip**: Make sure the Google Doc is set to 'Anyone with the link can view'")
    
    elif input_method == "Article URL":
        article_url = st.text_input(
            "Paste article URL:",
            placeholder="https://example.com/article"
        )
        if article_url:
            try:
                article_text = extract_article(article_url)
                st.success("✅ Successfully extracted from URL!")
            except Exception as e:
                st.error(f"Failed to extract from URL: {str(e)}")
    
    elif input_method == "Upload .docx File":
        uploaded_file = st.file_uploader(
            "Upload .docx file:",
            type=["docx"],
            help="Upload a Word document (.docx)"
        )
        if uploaded_file is not None:
            try:
                article_text = extract_text_from_file(uploaded_file)
                st.success("✅ Successfully extracted from file!")
            except Exception as e:
                st.error(f"Failed to extract from file: {str(e)}")
    
    # Process button
    if article_text and st.button("🚀 Start Editing", type="primary", use_container_width=True):
        st.session_state.original_text = article_text
        st.session_state.current_text = article_text
        st.session_state.chat_history = []
        st.rerun()

else:
    # Split-screen editing interface
    left_col, right_col = st.columns([1, 1], gap="large")
    
    # LEFT PANE: Chat interface
    with left_col:
        st.header("Chat with Editor")
        st.caption("Ask me to translate, summarize, or edit your text")
        
        # Display chat history
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg["content"])
        
        # Chat input
        user_input = st.chat_input(
            "Type your request (e.g., 'translate to Spanish', 'summarize in 150 words', 'make it more formal')"
        )
        
        if user_input:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Process request
            with st.spinner("Processing your request..."):
                try:
                    refined = refine_with_chat(
                        original_text=st.session_state.original_text,
                        current_text=st.session_state.current_text,
                        user_request=user_input
                    )
                    
                    # Update current text
                    st.session_state.current_text = refined
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": refined
                    })
                    
                    st.rerun()
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"Error: {error_msg}")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"❌ Error: {error_msg}"
                    })
                    
                    # Provide helpful error messages
                    if "credentials" in error_msg.lower() or "not found" in error_msg.lower():
                        st.info("💡 **Tip**: Make sure AWS credentials are configured. Run `aws configure` in your terminal.")
                    elif "model" in error_msg.lower() and "not available" in error_msg.lower():
                        st.info("💡 **Tip**: Run `python scripts/check_bedrock_models.py` to see available models in your account.")
                    elif "AccessDenied" in error_msg or "access" in error_msg.lower():
                        st.info("💡 **Tip**: Request model access in AWS Bedrock Console: https://console.aws.amazon.com/bedrock/")
        
        # Action buttons
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.original_text = ""
                st.session_state.current_text = ""
                st.session_state.chat_history = []
                st.rerun()
        with col2:
            if st.button("📥 Download PDF", use_container_width=True):
                summary_pdf = create_pdf(st.session_state.current_text)
                st.download_button(
                    "Download",
                    summary_pdf,
                    file_name="edited_text.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    # RIGHT PANE: Display current text
    with right_col:
        st.header("Current Text")
        st.caption("This is your current text (updated after each edit)")
        
        # Display current text
        current_display = st.text_area(
            "Current Version",
            st.session_state.current_text,
            height=600,
            key="current_text_display",
            label_visibility="collapsed"
        )
        
        # Show original text in expander
        with st.expander("📝 View Original Text"):
            st.text_area(
                "Original",
                st.session_state.original_text,
                height=200,
                key="original_text_display",
                label_visibility="collapsed"
            )

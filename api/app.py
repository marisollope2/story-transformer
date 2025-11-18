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

from scripts.summarization_pipeline import summarize_and_translate
from scripts.translation_pipeline import translate_structured_text
from scripts.extract import extract_article
from scripts.file_extractor import (
    extract_text_from_file, 
    extract_from_google_docs_url, 
    is_google_docs_url
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
    # Try to get credentials
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

# Optional: Show available models info
with st.sidebar.expander("ℹ️ About Models"):
    st.write("""
    This app uses AWS Bedrock models:
    - **Translation**: Automatically selects best model for target language
    - **Summarization**: Uses optimized summarization models
    
    Models are automatically selected based on your account access.
    """)

mode = st.radio("Choose what you'd like to do:", ["Summarize", "Translate"])
tab1, tab2 = st.tabs(["Upload File", "Enter URL"])


def language_selector(key_suffix):
    return st.selectbox(
        "Language of output",
        options=[
            "English", "Spanish", "French", "German", "Italian", "Portuguese",
            "Swahili", "Hindi", "Bengali", "Urdu", "Tamil", "Telugu",
            "Indonesian", "Malay", "Thai", "Vietnamese", "Tagalog",
            "Arabic", "Turkish", "Russian", "Chinese", "Japanese", "Korean",
            "Hausa", "Yoruba", "Amharic", "Afrikaans", "Zulu"
        ],
        key=f"language_{key_suffix}"
    )


def summary_controls(key_suffix):
    word_limit = st.number_input(
        "Desired word count for summary",
        min_value=50, max_value=1000, value=150, step=10,
        key=f"word_limit_{key_suffix}"
    )
    lang = language_selector(key_suffix)
    return word_limit, lang


with tab1:
    uploaded_file = st.file_uploader(
        "Upload an article", 
        type=["txt", "docx"],
        help="Supported formats: .txt, .docx (Word documents)"
    )
    if uploaded_file is not None:
        try:
            article_text = extract_text_from_file(uploaded_file)
        except Exception as e:
            st.error(f"Failed to extract text from file: {str(e)}")
            st.stop()

        if mode == "Summarize":
            word_limit, language = summary_controls("file")
        else:
            language = language_selector("file_only")

        st.subheader("Extracted Text")
        st.text_area("Contents", article_text, height=400)

        if st.button(f"{mode} from File"):
            with st.spinner(f"{mode}ing..."):
                try:
                    if mode == "Summarize":
                        # Use Bedrock (no API key needed - uses AWS credentials)
                        output = summarize_and_translate(article_text, word_limit, language, use_bedrock=True)
                    else:
                        # Use Bedrock (no API key needed - uses AWS credentials)
                        output = translate_structured_text(article_text, language, use_bedrock=True)

                    st.subheader("Output")
                    st.write(output)

                    summary_pdf = create_pdf(output)
                    filename = os.path.splitext(uploaded_file.name)[0]
                    st.download_button(
                        "Download Result (.pdf)",
                        summary_pdf,
                        file_name=f"{mode.lower()}_{filename}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"Failed to process: {error_msg}")
                    
                    # Provide helpful error messages
                    if "credentials" in error_msg.lower() or "not found" in error_msg.lower():
                        st.info("💡 **Tip**: Make sure AWS credentials are configured. Run `aws configure` in your terminal.")
                    elif "model" in error_msg.lower() and "not available" in error_msg.lower():
                        st.info("💡 **Tip**: Run `python scripts/check_bedrock_models.py` to see available models in your account.")
                    elif "AccessDenied" in error_msg or "access" in error_msg.lower():
                        st.info("💡 **Tip**: Request model access in AWS Bedrock Console: https://console.aws.amazon.com/bedrock/")
                    
                    with st.expander("Show full error details"):
                        st.code(traceback.format_exc())


with tab2:
    st.info("💡 **Tip**: You can paste a regular article URL or a Google Docs URL")
    with st.expander("ℹ️ About Google Docs"):
        st.write("""
        **For Google Docs:**
        - **Public docs**: Paste the URL directly
        - **Private docs**: Export as .docx (File → Download → Microsoft Word) and upload in the "Upload File" tab
        
        To make a Google Doc public:
        1. Click "Share" button
        2. Change access to "Anyone with the link"
        3. Copy the link and paste it here
        """)
    article_url = st.text_input("Paste the article URL or Google Docs link:")

    if mode == "Summarize":
        word_limit, language = summary_controls("url")
    else:
        language = language_selector("url_only")

    if st.button(f"{mode} from URL") and article_url:
        with st.spinner("Extracting article..."):
            try:
                # Check if it's a Google Docs URL
                if is_google_docs_url(article_url):
                    article_text = extract_from_google_docs_url(article_url)
                else:
                    # Regular article URL
                    article_text = extract_article(article_url)
                st.subheader("Extracted Text")
                st.text_area("Extracted Text", article_text, height=400)

                if mode == "Summarize":
                    # Use Bedrock (no API key needed - uses AWS credentials)
                    output = summarize_and_translate(article_text, word_limit, language, use_bedrock=True)
                else:
                    # Use Bedrock (no API key needed - uses AWS credentials)
                    output = translate_structured_text(article_text, language, use_bedrock=True)

                st.subheader("Output")
                st.write(output)

                summary_pdf = create_pdf(output)
                st.download_button(
                    "Download Result (.pdf)",
                    summary_pdf,
                    file_name=f"{mode.lower()}_from_url.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                error_msg = str(e)
                st.error(f"Failed to extract or process: {error_msg}")
                
                # Provide helpful error messages
                if "private" in error_msg.lower() or "google docs" in error_msg.lower():
                    st.info("""
                    💡 **For private Google Docs:**
                    1. Open your Google Doc
                    2. Go to File → Download → Microsoft Word (.docx)
                    3. Upload the downloaded .docx file in the "Upload .txt" tab
                    """)
                elif "credentials" in error_msg.lower() or "not found" in error_msg.lower():
                    st.info("💡 **Tip**: Make sure AWS credentials are configured. Run `aws configure` in your terminal.")
                elif "model" in error_msg.lower() and "not available" in error_msg.lower():
                    st.info("💡 **Tip**: Run `python scripts/check_bedrock_models.py` to see available models in your account.")
                elif "AccessDenied" in error_msg or "access" in error_msg.lower():
                    st.info("💡 **Tip**: Request model access in AWS Bedrock Console: https://console.aws.amazon.com/bedrock/")
                elif "unsupported file" in error_msg.lower():
                    st.info("💡 **Tip**: Supported file types: .txt, .docx. For Google Docs, use the URL or export as .docx first.")
                
                with st.expander("Show full error details"):
                    st.code(traceback.format_exc())
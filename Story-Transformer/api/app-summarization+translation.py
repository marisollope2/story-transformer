import streamlit as st
import sys
import os
import traceback
from pypdf import PdfReader
from fpdf import FPDF
from io import BytesIO
import unicodedata, re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.summarization_pipeline import summarize_and_translate
from scripts.translation_pipeline import translate_structured_text
from scripts.extract import extract_article


def sanitize_line(text):
    text = text.replace('\u2019', "'")
    text = text.replace('\u201C', '"')
    text = text.replace('\u201D', '"')
    text = text.replace('\u2018', "'")
    text = text.replace('\u2013', '-')
    text = text.replace('\u2014', '--')
    
    text = ''.join(c for c in text if unicodedata.category(c)[0] != "C")
    text = text.replace('\u00A0', ' ')
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
    
    pdf.set_font("Helvetica", size=10)
    
    text = text.replace('\u2019', "'").replace('\u201C', '"').replace('\u201D', '"')
    text = text.replace('\u2018', "'").replace('\u2013', '-').replace('\u2014', '--')
    text = ''.join(c for c in text if ord(c) < 256)
    
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
            
            if pdf.get_string_width(test_line) > (pdf.w - 2*pdf.l_margin - 10):
                if line:
                    try:
                        pdf.cell(0, 5, line, ln=1)
                    except Exception as e:
                        print(f"Error writing line: {str(e)}")
                    line = word
                else:
                    print(f"Skipping too long word: {word}")
                    continue
            else:
                line = test_line
                
        if line:
            try:
                pdf.cell(0, 5, line, ln=1)
                pdf.ln(3)
            except Exception as e:
                print(f"Error writing final line: {str(e)}")

    pdf_output = BytesIO()
    try:
        pdf.output(pdf_output)
        pdf_output.seek(0)
        return pdf_output
    except Exception as e:
        print(f"PDF generation failed: {str(e)}")
        simple_pdf = FPDF()
        simple_pdf.add_page()
        simple_pdf.set_font("Helvetica", size=12)
        simple_pdf.cell(0, 10, "PDF generation failed due to text encoding issues.")
        simple_pdf.ln()
        simple_pdf.cell(0, 10, "Please try again with different text content.")
        fallback_output = BytesIO()
        simple_pdf.output(fallback_output)
        fallback_output.seek(0)
        return fallback_output


st.title("Story Transformer")

mode = st.radio("Choose what you'd like to do:", ["Summarize", "Translate"])

tab1, tab2 = st.tabs(["Upload .txt", "Enter Article URL"])


def language_selector(key_suffix):
    return st.selectbox(
        "Language of output",
        options=["English", "Spanish", "Indonesian", "French", "German"],
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
    uploaded_file = st.file_uploader("Upload an article", type=["txt"])

    if uploaded_file is not None:
        article_text = uploaded_file.read().decode("utf-8")

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
                        output = summarize_and_translate(article_text, word_limit, language)
                    else:
                        output = translate_structured_text(article_text, language)

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
                    st.error(f"Failed to process: {e}")
                    st.code(traceback.format_exc())


with tab2:
    article_url = st.text_input("Paste the article URL:")

    if mode == "Summarize":
        word_limit, language = summary_controls("url")
    else:
        language = language_selector("url_only")

    if st.button(f"{mode} from URL") and article_url:
        with st.spinner("Extracting article..."):
            try:
                article_text = extract_article(article_url)
                st.subheader("Extracted Text")
                st.text_area("Extracted Text", article_text, height=400)

                if mode == "Summarize":
                    output = summarize_and_translate(article_text, word_limit, language)
                else:
                    output = translate_structured_text(article_text, language)

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
                st.error(f"Failed to extract or process: {e}")
                st.code(traceback.format_exc())
import streamlit as st
from pypdf import PdfReader
from fpdf import FPDF
from io import BytesIO
import re
from scripts.claude import translate_text_with_claude, summarize_text_with_claude

st.set_page_config(page_title="Story Transformer", layout="wide")
st.title("Story Transformer")

uploaded_file = st.file_uploader("Upload an article (.pdf)", type=["pdf"])

language = st.selectbox(
    "Choose target translation language:",
    ["Spanish", "French", "Indonesian"]
)

word_limit = st.number_input("Desired word count for summary", min_value=50, max_value=1000, value=150, step=10)

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    raw_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
    full_text = "\n".join(raw_pages)
    full_text = re.sub(r'[ \t]+', ' ', full_text)
    full_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', full_text)
    full_text = re.sub(r'\n{2,}', '\n\n', full_text)
    full_text = re.sub(r' {2,}', ' ', full_text)

    return full_text.strip()

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

if uploaded_file is not None:
    article_text = extract_text_from_pdf(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:
        st.header("Original Text")
        st.text_area("Original", article_text, height=400)

    with col2:
        st.header(f"Translation ({language})")

        if st.button("Translate Now"):
            with st.spinner(f"Translating to {language}..."):
                translated_text = translate_text_with_claude(article_text, language)

            st.success("Translation complete!")

            st.text_area("Translated", translated_text, height=400)

            translated_pdf = create_pdf(translated_text)

            st.download_button(
                label="Download Translation (.pdf)",
                data=translated_pdf,
                file_name=f"translated_{language.lower()}.pdf",
                mime="application/pdf"
            )

    st.header("Summary")

    if st.button("Summarize Now"):
        with st.spinner(f"Summarizing to ~{word_limit} words..."):
            summary_text = summarize_text_with_claude(article_text, word_limit)

        st.success("Summarization complete!")
        st.text_area("Summary", summary_text, height=300)

        summary_pdf = create_pdf(summary_text)

        st.download_button(
            label="Download Summary (.pdf)",
            data=summary_pdf,
            file_name="summary.pdf",
            mime="application/pdf"
        )
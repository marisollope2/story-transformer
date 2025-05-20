import streamlit as st
import sys
import os
from pypdf import PdfReader
from fpdf import FPDF
from io import BytesIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.summarization_pipeline import summarize_and_translate


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


st.title("Story Transformer")

uploaded_file = st.file_uploader("Upload an article", type=["txt"])

word_limit = st.number_input("Desired word count for summary", min_value=50, max_value=1000, value=150, step=10)
language = st.selectbox("Language of output summary", options=["English", "Spanish", "Indonesian", "French", "German"])

if uploaded_file is not None:
    article_text = uploaded_file.read().decode("utf-8")

    st.write("Article preview:")
    st.text_area("Contents", article_text, height=200)

    if st.button("Summarize"):
        with st.spinner("Summarizing..."):
            summary = summarize_and_translate(article_text, word_limit, language)
        st.subheader("Summary")
        st.write(summary)

        summary_pdf = create_pdf(summary)
        filename = os.path.splitext(uploaded_file.name)[0]

        st.download_button(
                label="Download Summary (.pdf)",
                data=summary_pdf,
                file_name=f"summary_{filename}.pdf",
                mime="application/pdf"
            )


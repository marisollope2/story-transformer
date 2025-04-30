import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.summarization_pipeline import summarize_and_translate

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


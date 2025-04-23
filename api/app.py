# scratch code
import streamlit as st
st.title("Story Transformer")

uploaded_file = st.file_uploader("Upload an article", type=["txt"]) # can be changed to pdf, etc.

# specifies word count for summarization func
word_limit = st.number_input("Desired word count for summary", min_value=50, max_value=1000, value=150, step=10) #arbitrary values

# shows article input
if uploaded_file is not None:
    article_text = uploaded_file.read().decode("utf-8")
    # add function/script to read txt files here
    st.write("Article preview:")
    st.text_area("Contents", article_text, height=200)

    if st.button("Summarize"):
        # Summarization script/func should be added here
        summary = f"(Summary of {word_limit} words would go here)"
        st.subheader("Summary")
        st.write(summary)

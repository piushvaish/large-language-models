import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import streamlit as st
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback

def load_openai_api_key():
    dotenv_path = "openai.env"
    load_dotenv(dotenv_path)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError(f"Unable to retrieve OPENAI_API_KEY from {dotenv_path}")
    return openai_api_key

def process_text(text):
    # Split the text into chunks using Langchain's CharacterTextSplitter
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)

    # Convert the chunks of text into embeddings to form a knowledge base
    embeddings = OpenAIEmbeddings()
    knowledgeBase = FAISS.from_texts(chunks, embeddings)

    return knowledgeBase

def main():
    st.title("📄PDF Summarizer")
    st.write("Created by Daniel")
    st.divider()

    try:
        os.environ["OPENAI_API_KEY"] = load_openai_api_key()
    except ValueError as e:
        st.error(str(e))
        return

    pdf = st.file_uploader('Upload your PDF Document', type='pdf')

    if pdf is not None:
        pdf_reader = PdfReader(pdf)
        # Text variable will store the pdf text
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # Create the knowledge base object
        knowledgeBase = process_text(text)

        query = """
        Analyze the attached tender document and generate an ADHD-friendly summary that is clear, concise, and actionable. The summary should be structured as follows:

Quick Opportunity Snapshot:

Provide the project name, location, contracting authority, deadline, award date, and evaluation weighting.
Format as short, bold key details (e.g., 'Project: Roof Upgrade Works at Bray Institute of Further Education').
Main Sections (use clear, labeled headings):

Opportunity Overview:
Provide a one-liner summary of the project.
List key details such as contract type, authority name, and award timeline.
What’s Needed?:
Provide a one-liner summary of submission requirements.
Use bullet points to list technical, financial, health & safety, and supporting document requirements.
How You’ll Be Scored:
Provide a one-liner summary of the evaluation criteria.
Break down the weighting (e.g., '70% Price, 30% Technical') and subcategories (e.g., Risk Plan 15%, Traffic Plan 7.5%).
Next Steps:
Provide a one-liner summary of action items.
Format as a simple checklist (e.g., '[ ] Register on eTenders').
Visual Enhancements:

Suggest visual elements such as icons, color-coded tags, and bar charts for evaluation weightings to improve engagement.
Sidebar Suggestions:

List useful quick links such as downloadable templates, FAQs, and contact details.
Keep the language simple and user-friendly, with a focus on making the tender accessible to someone who may find traditional formats overwhelming.
        """

        if query:
            docs = knowledgeBase.similarity_search(query)
            OpenAIModel = "gpt-4o-2024-11-20"
            llm = ChatOpenAI(model=OpenAIModel, temperature=0.4)
            chain = load_qa_chain(llm, chain_type='stuff')

            with get_openai_callback() as cost:
                response = chain.run(input_documents=docs, question=query)
                print(cost)

            st.subheader('Summary Results:')
            st.write(response)

if __name__ == '__main__':
    main()
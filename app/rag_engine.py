import os
import requests
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.schema import HumanMessage
from langchain_community.chat_models import ChatOpenAI  # Only used if fallback needed

# Load env variables
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
A4F_API_KEY = os.getenv("A4F_API_KEY")
A4F_BASE_URL = os.getenv("A4F_BASE_URL")
A4F_MODEL = os.getenv("A4F_MODEL")


def extract_text_from_pdf_url(pdf_url):
    """Downloads and extracts raw text from the PDF file via URL."""
    response = requests.get(pdf_url)
    response.raise_for_status()

    with open("temp.pdf", "wb") as f:
        f.write(response.content)

    text = ""
    with fitz.open("temp.pdf") as doc:
        for page in doc:
            text += page.get_text()
    os.remove("temp.pdf")
    return text


def create_vector_store(text):
    """Splits text and creates a FAISS vector store."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = [Document(page_content=chunk) for chunk in splitter.split_text(text)]

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    return vectorstore


def retrieve_relevant_chunks(vectorstore, query, k=5):
    """Returns top-k relevant chunks using semantic similarity."""
    docs = vectorstore.similarity_search(query, k=k)
    return [doc.page_content for doc in docs]


def call_a4f_llm(context, question, retries=3):
    """Calls A4F LLM endpoint with retries."""
    url = f"{A4F_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {A4F_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": A4F_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful insurance assistant."},
            {"role": "user", "content": f"Policy Content:\n{context}\n\nQuestion: {question}"}
        ]
    }

    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                continue
            raise Exception(f"A4F API failed after {retries} attempts: {str(e)}")


def answer_questions_from_pdf(pdf_url, questions):
    """Pipeline entry: extracts text, builds vectorstore, answers questions."""
    text = extract_text_from_pdf_url(pdf_url)
    vectorstore = create_vector_store(text)

    answers = []
    for question in questions:
        context_chunks = retrieve_relevant_chunks(vectorstore, question)
        context = "\n\n".join(context_chunks)
        answer = call_a4f_llm(context, question)
        answers.append(answer)

    return answers

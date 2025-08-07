import fitz  # PyMuPDF
import requests
from tempfile import NamedTemporaryFile


def download_pdf_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to download PDF.")
    temp_file = NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.write(response.content)
    temp_file.close()
    return temp_file.name


def extract_text_chunks_from_pdf(pdf_path, chunk_size=500, overlap=50):
    doc = fitz.open(pdf_path)
    full_text = "\n".join(page.get_text() for page in doc)

    chunks = []
    for i in range(0, len(full_text), chunk_size - overlap):
        chunk = full_text[i:i + chunk_size]
        chunks.append(chunk)
    return chunks

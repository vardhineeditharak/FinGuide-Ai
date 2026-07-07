"""
ingest.py
Reads all documents in /data, splits them into chunks, embeds them with a
local sentence-transformer model, and stores them in a persistent Chroma
vector database (/vectorstore).

Run this once (and again whenever you add/update files in /data):
    python ingest.py
"""

import os
import glob
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RESOURCES_DIR = os.path.join(DATA_DIR, "raw_resources")
DB_DIR = os.path.join(os.path.dirname(__file__), "vectorstore")
COLLECTION_NAME = "fin_literacy_kb"

CHUNK_SIZE = 700       # characters per chunk
CHUNK_OVERLAP = 100    # overlap between chunks to preserve context


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Simple sliding-window chunker."""
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def load_documents():
    docs = []
    # Load Markdown and Text documents from data/
    for path in glob.glob(os.path.join(DATA_DIR, "*.md")) + glob.glob(os.path.join(DATA_DIR, "*.txt")):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        source_name = os.path.basename(path)
        # Use the first markdown header as a rough topic label
        topic = source_name.replace(".md", "").replace(".txt", "").replace("_", " ")
        for i, chunk in enumerate(chunk_text(content)):
            docs.append({
                "id": f"{source_name}-{i}",
                "text": chunk,
                "source": source_name,
                "topic": topic,
            })
            
    # Load PDF documents from resources/
    for path in glob.glob(os.path.join(RESOURCES_DIR, "*.pdf")):
        try:
            reader = PdfReader(path)
            content = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
            
            source_name = os.path.basename(path)
            topic = source_name.replace(".pdf", "").replace("_", " ")
            for i, chunk in enumerate(chunk_text(content)):
                docs.append({
                    "id": f"{source_name}-{i}",
                    "text": chunk,
                    "source": source_name,
                    "topic": topic,
                })
            print(f"Loaded and chunked PDF: {source_name}")
        except Exception as e:
            print(f"Error loading PDF {path}: {e}")
            
    return docs



def build_index():
    print("Loading documents from:", DATA_DIR)
    docs = load_documents()
    print(f"Loaded {len(docs)} chunks from {len(glob.glob(os.path.join(DATA_DIR, '*'))) } files")

    # Local embedding model — free, no API key needed, runs on CPU
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2",
        device="cpu"
    )

    client = chromadb.PersistentClient(path=DB_DIR)

    # Reset collection each run so re-ingesting doesn't duplicate chunks
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )

    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[{"source": d["source"], "topic": d["topic"]} for d in docs],
    )

    print(f"Indexed {collection.count()} chunks into Chroma at {DB_DIR}")


if __name__ == "__main__":
    build_index()

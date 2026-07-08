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
    """Paragraph-aware chunker that groups paragraphs to preserve structure."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_len = len(para)
        # If a single paragraph is larger than chunk_size, split it
        if para_len > chunk_size:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            
            start = 0
            while start < para_len:
                end = min(start + chunk_size, para_len)
                chunks.append(para[start:end].strip())
                start += chunk_size - overlap
            continue
        
        if current_len + para_len + (2 if current_chunk else 0) > chunk_size:
            chunks.append("\n\n".join(current_chunk))
            if overlap > 0 and len(current_chunk) > 1 and len(current_chunk[-1]) < overlap:
                current_chunk = [current_chunk[-1], para]
                current_len = len(current_chunk[0]) + 2 + para_len
            else:
                current_chunk = [para]
                current_len = para_len
        else:
            current_chunk.append(para)
            current_len += para_len + (2 if len(current_chunk) > 1 else 0)
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
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

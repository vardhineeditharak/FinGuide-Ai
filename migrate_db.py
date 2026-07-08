import os
import sqlite3
import struct
import chromadb
from chromadb.utils import embedding_functions

DB_DIR = os.path.join(os.path.dirname(__file__), "vectorstore")
COLLECTION_NAME = "fin_literacy_kb"
SQLITE_DB_PATH = os.path.join(DB_DIR, "embeddings.db")

def migrate():
    print("Initializing Chroma client...")
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2",
        device="cpu"
    )
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=embed_fn)

    count = collection.count()
    print(f"Total count in Chroma collection: {count}")

    if count == 0:
        print("No items found in Chroma to migrate.")
        return

    print("Fetching all records from Chroma (this may take a moment)...")
    data = collection.get(include=['embeddings', 'documents', 'metadatas'])
    
    ids = data['ids']
    embeddings = data['embeddings']
    documents = data['documents']
    metadatas = data['metadatas']

    print(f"Retrieved {len(ids)} items. Connecting to target SQLite database: {SQLITE_DB_PATH}...")
    
    # Connect to SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    # Drop existing table if exists
    cursor.execute("DROP TABLE IF EXISTS document_embeddings;")
    
    # Create optimized table
    cursor.execute("""
        CREATE TABLE document_embeddings (
            id TEXT PRIMARY KEY,
            document TEXT,
            source TEXT,
            topic TEXT,
            embedding BLOB
        );
    """)

    # Prepare data for insertion
    insert_data = []
    for i in range(len(ids)):
        doc_id = ids[i]
        doc_text = documents[i]
        meta = metadatas[i] or {}
        source = meta.get("source", "")
        topic = meta.get("topic", "")
        emb = embeddings[i]

        # Convert float list to binary blob (384 floats)
        emb_blob = struct.pack(f'{len(emb)}f', *emb)

        insert_data.append((doc_id, doc_text, source, topic, emb_blob))

    # Bulk insert
    print("Writing records to SQLite...")
    cursor.executemany(
        "INSERT INTO document_embeddings (id, document, source, topic, embedding) VALUES (?, ?, ?, ?, ?);",
        insert_data
    )
    
    conn.commit()
    
    # Verify count
    cursor.execute("SELECT count(*) FROM document_embeddings;")
    new_count = cursor.fetchone()[0]
    print(f"Successfully migrated {new_count} records to SQLite!")

    conn.close()

if __name__ == "__main__":
    migrate()

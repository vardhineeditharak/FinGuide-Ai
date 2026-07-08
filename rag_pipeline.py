"""
rag_pipeline.py
Core RAG logic optimized for serverless deployment:
 1. Embed the user query using the Watsonx.ai cloud embedding API (all-minilm-l6-v2).
 2. Retrieve top-k relevant chunks from our lightweight SQLite vector store using pure Python cosine similarity.
 3. Build a grounded prompt with those chunks + safety instructions.
 4. Call IBM watsonx.ai Granite model to generate the final answer.
"""

import os
import sqlite3
import struct
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models.embeddings import Embeddings

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "vectorstore", "embeddings.db")
TOP_K = 4

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_MODEL_ID = os.getenv("GRANITE_MODEL_ID", "ibm/granite-4-h-small")

SYSTEM_PROMPT = """You are "Saarthi", a friendly digital financial literacy assistant for users in India.

Rules you MUST follow:
- Answer ONLY using the information given in the CONTEXT below. If the context does not contain the answer, say clearly: "I don't have enough verified information on that yet" and suggest the user check the relevant official source (RBI, NPCI, or their bank).
- Never give specific investment advice, guaranteed returns, or personal legal advice. Keep answers educational and general.
- If the question relates to OTP, UPI PIN, scams, or fraud, always include a short safety reminder (e.g., never share OTP/PIN, call 1930 for cyber fraud).
- Keep the tone simple, warm, and non-technical — assume the user may be a first-time digital finance user.
- Keep answers concise: 3-6 sentences, using short paragraphs or bullet points where helpful.
- If relevant, mention which source/topic the info is based on (e.g., "Based on NPCI/RBI guidance...").
"""

_cached_records = None
_embeddings_client = None


def _get_embeddings_client():
    global _embeddings_client
    if _embeddings_client is None:
        credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
        _embeddings_client = Embeddings(
            model_id="sentence-transformers/all-minilm-l6-v2",
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID
        )
    return _embeddings_client


def _get_records():
    global _cached_records
    if _cached_records is None:
        if not os.path.exists(DB_PATH):
            return []
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, document, source, topic, embedding FROM document_embeddings;")
        rows = cursor.fetchall()
        conn.close()

        records = []
        for r_id, doc, src, topic, emb_blob in rows:
            # Unpack the binary blob into a float list
            dim = len(emb_blob) // 4
            emb = list(struct.unpack(f'{dim}f', emb_blob))
            
            # Calculate magnitude for cosine similarity
            mag = sum(x*x for x in emb) ** 0.5
            records.append({
                "id": r_id,
                "text": doc,
                "source": src,
                "topic": topic,
                "embedding": emb,
                "magnitude": mag
            })
        _cached_records = records
    return _cached_records


def retrieve(query, top_k=TOP_K):
    records = _get_records()
    if not records:
        return []

    # Get query embedding using Watsonx cloud API
    emb_client = _get_embeddings_client()
    query_vector = emb_client.embed_query(query)
    
    q_mag = sum(x*x for x in query_vector) ** 0.5
    if q_mag == 0:
        return []

    # Compute cosine similarity
    scores = []
    for r in records:
        dot_product = sum(x * y for x, y in zip(query_vector, r["embedding"]))
        denom = q_mag * r["magnitude"]
        score = dot_product / denom if denom > 0 else 0.0
        scores.append((score, r))

    # Sort by score descending and return top_k
    scores.sort(key=lambda val: val[0], reverse=True)
    
    chunks = []
    for score, r in scores[:top_k]:
        chunks.append({
            "text": r["text"],
            "source": r["source"]
        })
    return chunks


def build_prompt(query, chunks):
    context_str = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )
    prompt = f"""{SYSTEM_PROMPT}

CONTEXT:
{context_str}

USER QUESTION: {query}

ANSWER:"""
    return prompt


def call_granite(prompt):
    """Calls IBM watsonx.ai Granite model. Returns generated text or None on failure."""
    if not (WATSONX_API_KEY and WATSONX_PROJECT_ID):
        return None

    try:
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)

        model = ModelInference(
            model_id=GRANITE_MODEL_ID,
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID,
            params={
                "decoding_method": "greedy",
                "max_new_tokens": 350,
                "min_new_tokens": 20,
                "repetition_penalty": 1.1,
            },
        )

        response = model.generate_text(prompt=prompt)
        return response.strip()
    except Exception as e:
        print(f"[watsonx error] {type(e).__name__}: {e}")
        return None


def fallback_answer(chunks):
    """Used only when watsonx credentials are not configured yet."""
    if not chunks:
        return ("I don't have enough verified information on that yet. "
                "Please check rbi.org.in or npci.org.in for official guidance.")
    bullet_points = "\n".join(f"- {c['text'][:220]}..." for c in chunks[:2])
    return (
        "⚠️ Demo mode (watsonx.ai Granite not connected yet). "
        "Showing raw retrieved context instead of a generated answer:\n\n"
        f"{bullet_points}\n\n"
        "Add your WATSONX_API_KEY and WATSONX_PROJECT_ID in .env to get full AI-generated answers."
    )


def answer_query(query):
    chunks = retrieve(query)
    prompt = build_prompt(query, chunks)
    generated = call_granite(prompt)
    if generated is None:
        answer = fallback_answer(chunks)
        used_fallback = True
    else:
        answer = generated
        used_fallback = False

    sources = sorted(set(c["source"] for c in chunks))
    return {
        "answer": answer,
        "sources": sources,
        "used_fallback": used_fallback,
    }


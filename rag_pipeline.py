"""
rag_pipeline.py
Core RAG logic:
 1. Embed the user query and retrieve top-k relevant chunks from Chroma.
 2. Build a grounded prompt with those chunks + safety instructions.
 3. Call IBM watsonx.ai Granite model to generate the final answer.

If watsonx credentials are missing or invalid, falls back to a clearly-labeled
"context-only" response so the app still runs end-to-end for demo purposes.
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

DB_DIR = os.path.join(os.path.dirname(__file__), "vectorstore")
COLLECTION_NAME = "fin_literacy_kb"
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


_embed_fn = None
_collection = None


def _get_collection():
    global _embed_fn, _collection
    if _collection is None:
        _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device="cpu"
        )
        client = chromadb.PersistentClient(path=DB_DIR)
        _collection = client.get_collection(name=COLLECTION_NAME, embedding_function=_embed_fn)
    return _collection


def retrieve(query, top_k=TOP_K):
    collection = _get_collection()
    results = collection.query(query_texts=[query], n_results=top_k)
    chunks = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for text, meta in zip(docs, metas):
        chunks.append({"text": text, "source": meta.get("source", "unknown")})
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

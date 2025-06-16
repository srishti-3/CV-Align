from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

load_dotenv()
pine = os.getenv("LLM")

# Initialize Pinecone client
pc = Pinecone(api_key=pine)

# Create index if not exists
index_name = "cv-index"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,  # all-MiniLM-L6-v2
        metric="cosine",
        spec=ServerlessSpec(
            cloud="gcp",           # or "aws"
            region="us-central1"   # match Pinecone dashboard region
        )
    )

# Connect to the index
index = pc.Index(index_name)

import uuid
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_resume(parsed_resume):
    chunks = []

    for key, value in parsed_resume.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    text = " ".join(str(v) for v in item.values())
                elif isinstance(item, str):
                    text = item
                else:
                    continue
                if text.strip():
                    chunks.append(text.strip())

        elif isinstance(value, dict):
            text = " ".join(str(v) for v in value.values())
            if text.strip():
                chunks.append(text.strip())

        elif isinstance(value, str):
            if value.strip():
                chunks.append(value.strip())

    return chunks


def embed_and_upsert_chunks(resume_id: str, chunks: list):
    # First delete all old vectors for this resume_id
    index.delete(filter={"resume_id": resume_id})

    # Then upsert fresh ones
    vectors = embedder.encode(chunks).tolist()
    ids = [f"{resume_id}-{i}" for i in range(len(chunks))]
    pinecone_vectors = list(zip(ids, vectors, [{"text": c, "resume_id": resume_id} for c in chunks]))
    index.upsert(pinecone_vectors)

def query_pinecone(jd_text: str, top_k: int = 5):
    jd_embedding = embedder.encode([jd_text])[0].tolist()
    result = index.query(vector=jd_embedding, top_k=top_k, include_metadata=True)
    return [match["metadata"]["text"] for match in result["matches"]]


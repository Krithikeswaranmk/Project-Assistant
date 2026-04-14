import asyncio
import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase: Client | None = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_KEY else None

model = SentenceTransformer("all-MiniLM-L6-v2")


async def embed_and_store(chunks: list[dict], user_id: str, repo_name: str) -> None:
    if not supabase or not chunks:
        return

    rows = []
    for chunk in chunks:
        text_to_embed = f"{chunk.get('file', '')} | {chunk.get('name', '')} | {chunk.get('code', '')[:500]}"
        embedding = await asyncio.to_thread(model.encode, text_to_embed, convert_to_numpy=True)
        embedding = embedding.tolist()
        rows.append(
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "repo_name": repo_name,
                "file_path": chunk.get("file"),
                "chunk_type": chunk.get("type"),
                "chunk_name": chunk.get("name"),
                "code_text": chunk.get("code", ""),
                "language": chunk.get("language", "unknown"),
                "embedding": embedding,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    for i in range(0, len(rows), 50):
        batch = rows[i : i + 50]
        await asyncio.to_thread(lambda: supabase.table("code_chunks").insert(batch).execute())

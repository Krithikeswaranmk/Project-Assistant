import asyncio
import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase: Client | None = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_KEY else None

model = SentenceTransformer("all-MiniLM-L6-v2")


async def search(query: str, user_id: str, repo_name: str, top_k: int = 5) -> list[dict]:
    if not supabase:
        return []

    query_embedding = await asyncio.to_thread(model.encode, query, convert_to_numpy=True)
    query_embedding = query_embedding.tolist()
    result = await asyncio.to_thread(
        lambda: supabase.rpc(
            "match_code_chunks",
            {
                "query_embedding": query_embedding,
                "filter_user_id": user_id,
                "filter_repo_name": repo_name,
                "match_count": top_k,
            },
        ).execute()
    )
    return result.data or []

import asyncio
import os
import shutil
import tempfile
from datetime import datetime

from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException
from git import Repo
from pydantic import BaseModel, Field
from supabase import Client, create_client

from rag.chunker import chunk_repository
from rag.embedder import embed_and_store
from services.github_service import get_file_tree, get_user_repos
from services.scoring_service import score_repo

load_dotenv()

router = APIRouter(prefix="/onboard", tags=["onboard"])

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase: Client | None = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_KEY else None

indexing_status: dict = {}


class OnboardRequest(BaseModel):
    user_id: str
    name: str
    github_username: str
    github_token: str
    target_role: str
    experience_level: str
    focus_areas: list[str] = Field(default_factory=list)


@router.post("")
async def onboard_user(payload: OnboardRequest, background_tasks: BackgroundTasks) -> dict:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")

    indexing_status[payload.user_id] = {
        "status": "indexing",
        "repos_done": 0,
        "repos_total": 0,
        "error_message": None,
    }
    background_tasks.add_task(run_indexing_pipeline, payload)
    return {"status": "started", "user_id": payload.user_id}


async def run_indexing_pipeline(payload: OnboardRequest) -> None:
    if not supabase:
        indexing_status[payload.user_id] = {
            "status": "error",
            "repos_done": 0,
            "repos_total": 0,
            "error_message": "Supabase is not configured",
        }
        return

    try:
        stored_token = payload.github_token
        if not stored_token:
            existing = await asyncio.to_thread(
                lambda: (
                    supabase.table("profiles")
                    .select("github_token")
                    .eq("user_id", payload.user_id)
                    .limit(1)
                    .execute()
                )
            )
            if existing.data:
                stored_token = existing.data[0].get("github_token", "")

        if not stored_token:
            raise ValueError("GitHub token is required")

        await asyncio.to_thread(
            lambda: supabase.table("profiles")
            .upsert(
                {
                    "user_id": payload.user_id,
                    "name": payload.name,
                    "github_username": payload.github_username,
                    "github_token": stored_token,
                    "target_role": payload.target_role,
                    "experience_level": payload.experience_level,
                    "focus_areas": payload.focus_areas,
                    "onboarding_complete": False,
                    "updated_at": datetime.utcnow().isoformat(),
                },
                on_conflict="user_id",
            )
            .execute()
        )

        repos = await asyncio.to_thread(get_user_repos, stored_token, payload.github_username)
        indexing_status[payload.user_id]["repos_total"] = len(repos)
        done = 0

        for repo in repos:
            tmp_path = tempfile.mkdtemp(prefix="project_pilot_")
            try:
                await asyncio.to_thread(Repo.clone_from, repo["clone_url"], tmp_path, depth=1)
                chunks = await asyncio.to_thread(chunk_repository, tmp_path)
                await embed_and_store(chunks, payload.user_id, repo["name"])
                file_tree = await asyncio.to_thread(get_file_tree, tmp_path)
                scores = await asyncio.to_thread(
                    score_repo,
                    repo_name=repo["name"],
                    readme=repo.get("readme_content", ""),
                    file_tree=file_tree,
                    target_role=payload.target_role,
                )
                await asyncio.to_thread(
                    lambda: supabase.table("repositories")
                    .insert(
                        {
                            "user_id": payload.user_id,
                            "name": repo["name"],
                            "description": repo.get("description"),
                            "language": repo.get("language"),
                            "stars": repo.get("stargazers_count", 0),
                            "last_updated": repo.get("updated_at"),
                            "relevance_score": scores.get("relevance_score", 50),
                            "market_demand_score": scores.get("market_demand_score", 50),
                            "key_skills": scores.get("key_skills", []),
                            "missing_skills": scores.get("missing_skills", []),
                            "one_line_summary": scores.get("one_line_summary", ""),
                            "score_reasoning": scores.get("score_reasoning", ""),
                        }
                    )
                    .execute()
                )
            finally:
                if os.path.exists(tmp_path):
                    shutil.rmtree(tmp_path, ignore_errors=True)

            done += 1
            indexing_status[payload.user_id].update(
                {
                    "status": "indexing",
                    "repos_done": done,
                    "error_message": None,
                }
            )

        await asyncio.to_thread(
            lambda: supabase.table("profiles")
            .update({"onboarding_complete": True, "updated_at": datetime.utcnow().isoformat()})
            .eq("user_id", payload.user_id)
            .execute()
        )

        indexing_status[payload.user_id].update(
            {
                "status": "complete",
                "repos_done": done,
                "repos_total": len(repos),
                "error_message": None,
            }
        )
    except Exception as exc:
        indexing_status[payload.user_id].update(
            {
                "status": "error",
                "error_message": str(exc),
            }
        )


@router.get("/status/{user_id}")
async def get_onboard_status(user_id: str) -> dict:
    if user_id not in indexing_status:
        return {"status": "complete", "repos_done": 0, "repos_total": 0, "error_message": None}
    entry = indexing_status[user_id]
    return {
        "status": entry.get("status", "indexing"),
        "repos_done": entry.get("repos_done", 0),
        "repos_total": entry.get("repos_total", 0),
        "error_message": entry.get("error_message"),
    }

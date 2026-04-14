import os
import shutil
import tempfile
from datetime import datetime

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from git import Repo
from pydantic import BaseModel, Field
from supabase import create_client

from rag.chunker import chunk_repository
from rag.embedder import embed_and_store
from services.github_service import get_file_tree, get_user_repos
from services.scoring_service import score_repo

load_dotenv()

router = APIRouter(prefix="/onboard", tags=["onboard"])

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_KEY else None

indexing_status: dict[str, dict] = {}


class OnboardRequest(BaseModel):
    user_id: str
    name: str
    github_username: str
    github_token: str
    target_role: str
    experience_level: str
    focus_areas: list[str] = Field(default_factory=list)


@router.post("")
async def onboard_user(payload: OnboardRequest) -> dict:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")

    indexing_status[payload.user_id] = {
        "status": "indexing",
        "repos_done": 0,
        "repos_total": 0,
        "updated_at": datetime.utcnow().isoformat(),
    }

    try:
        stored_token = payload.github_token
        if not stored_token:
            existing = (
                supabase.table("profiles")
                .select("github_token")
                .eq("user_id", payload.user_id)
                .limit(1)
                .execute()
            )
            if existing.data:
                stored_token = existing.data[0].get("github_token", "")

        if not stored_token:
            raise HTTPException(status_code=400, detail="GitHub token is required")

        supabase.table("profiles").upsert(
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
        ).execute()

        repos = get_user_repos(stored_token, payload.github_username)
        indexing_status[payload.user_id]["repos_total"] = len(repos)
        done = 0

        for repo in repos:
            tmp_path = tempfile.mkdtemp(prefix="repo_", dir=None)
            try:
                Repo.clone_from(repo["clone_url"], tmp_path, depth=1)
                chunks = chunk_repository(tmp_path)
                embed_and_store(chunks, payload.user_id, repo["name"])
                file_tree = get_file_tree(tmp_path)
                scores = score_repo(
                    repo_name=repo["name"],
                    readme=repo.get("readme_content", ""),
                    file_tree=file_tree,
                    target_role=payload.target_role,
                )
                supabase.table("repositories").insert(
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
                ).execute()
            finally:
                shutil.rmtree(tmp_path, ignore_errors=True)

            done += 1
            indexing_status[payload.user_id].update(
                {
                    "status": "indexing",
                    "repos_done": done,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )

        supabase.table("profiles").update(
            {"onboarding_complete": True, "updated_at": datetime.utcnow().isoformat()}
        ).eq("user_id", payload.user_id).execute()

        indexing_status[payload.user_id].update(
            {
                "status": "complete",
                "repos_done": done,
                "repos_total": len(repos),
                "updated_at": datetime.utcnow().isoformat(),
            }
        )
        return {"status": "success", "repos_indexed": done, "profile_id": payload.user_id}
    except HTTPException:
        indexing_status[payload.user_id]["status"] = "error"
        raise
    except Exception as exc:
        indexing_status[payload.user_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {exc}") from exc


@router.get("/status/{user_id}")
async def get_onboard_status(user_id: str) -> dict:
    if user_id not in indexing_status:
        return {"status": "complete", "repos_done": 0, "repos_total": 0}
    entry = indexing_status[user_id]
    return {
        "status": entry.get("status", "indexing"),
        "repos_done": entry.get("repos_done", 0),
        "repos_total": entry.get("repos_total", 0),
    }

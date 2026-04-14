import os
from collections import Counter

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import Client, create_client

load_dotenv()

router = APIRouter(prefix="/profile", tags=["profile"])

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase: Client | None = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_KEY else None


class ScoreFeedbackRequest(BaseModel):
    repo_name: str
    score_type: str
    helpful: bool


@router.get("/{user_id}")
async def get_profile(user_id: str) -> dict:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")

    profile_resp = (
        supabase.table("profiles")
        .select("name,target_role,experience_level,github_username,avatar_url")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    repo_resp = (
        supabase.table("repositories")
        .select("*")
        .eq("user_id", user_id)
        .order("last_updated", desc=True)
        .execute()
    )

    profile = profile_resp.data[0] if profile_resp.data else {
        "name": "",
        "target_role": "",
        "experience_level": "",
        "github_username": "",
        "avatar_url": "",
    }
    repos = repo_resp.data or []

    relevance_scores = [int(repo.get("relevance_score", 0) or 0) for repo in repos]
    overall_relevance = int(sum(relevance_scores) / len(relevance_scores)) if relevance_scores else 0

    top_project = {"name": "", "reason": ""}
    if repos:
        best = max(repos, key=lambda r: int(r.get("relevance_score", 0) or 0))
        top_project = {
            "name": best.get("name", ""),
            "reason": best.get("score_reasoning", "Strong alignment with your target role."),
        }

    skill_counter: Counter[str] = Counter()
    for repo in repos:
        for skill in repo.get("key_skills", []) or []:
            skill_counter[skill] += 1
    repo_count = max(1, len(repos))
    skill_coverage = {skill: int((count / repo_count) * 100) for skill, count in skill_counter.items()}

    return {
        "profile": {
            "name": profile.get("name", ""),
            "target_role": profile.get("target_role", ""),
            "experience_level": profile.get("experience_level", ""),
            "github_username": profile.get("github_username", ""),
            "avatar_url": profile.get("avatar_url", ""),
        },
        "repos": repos,
        "overall_relevance_percent": overall_relevance,
        "top_project": top_project,
        "skill_coverage": skill_coverage,
    }


@router.put("/{user_id}/score-feedback")
async def score_feedback(user_id: str, payload: ScoreFeedbackRequest) -> dict:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")
    supabase.table("score_feedback").insert(
        {
            "user_id": user_id,
            "repo_name": payload.repo_name,
            "score_type": payload.score_type,
            "helpful": payload.helpful,
        }
    ).execute()
    return {"message": "feedback saved"}

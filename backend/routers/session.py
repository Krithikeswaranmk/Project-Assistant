import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client

from agents.planner_agent import generate_session_plan
from rag.retriever import search

load_dotenv()

router = APIRouter(prefix="/session", tags=["session"])

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL and SUPABASE_SERVICE_KEY else None


class SessionPlanRequest(BaseModel):
    user_id: str
    project_name: str
    repo_name: str
    goal: str
    deadline: str
    focus_minutes: int = Field(ge=1, le=240)
    complexity: str


class TaskUpdateRequest(BaseModel):
    completed: bool


@router.post("/plan")
async def plan_session(payload: SessionPlanRequest) -> dict[str, Any]:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")

    context_chunks = search(
        query=payload.goal,
        user_id=payload.user_id,
        repo_name=payload.repo_name,
        top_k=5,
    )
    plan = generate_session_plan(payload, context_chunks)

    tasks = plan.get("tasks", []) if isinstance(plan, dict) else plan
    strategy = plan.get("session_strategy", "") if isinstance(plan, dict) else ""
    deadline_status = plan.get("deadline_status", "on_track") if isinstance(plan, dict) else "on_track"
    estimated_total = sum(int(task.get("estimated_minutes", 0)) for task in tasks)

    insert_payload = {
        "user_id": payload.user_id,
        "project_name": payload.project_name,
        "repo_name": payload.repo_name,
        "goal": payload.goal,
        "deadline": payload.deadline,
        "focus_minutes": payload.focus_minutes,
        "tasks": tasks,
        "session_strategy": strategy,
        "deadline_status": deadline_status,
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
    }
    inserted = supabase.table("sessions").insert(insert_payload).execute()
    if not inserted.data:
        raise HTTPException(status_code=500, detail="Failed to save session")

    return {
        "session_id": inserted.data[0]["id"],
        "tasks": tasks,
        "estimated_total_minutes": estimated_total,
        "session_strategy": strategy,
        "deadline_status": deadline_status,
        "goal": payload.goal,
        "focus_minutes": payload.focus_minutes,
    }


@router.patch("/{session_id}/task/{task_index}")
async def update_task(session_id: str, task_index: int, payload: TaskUpdateRequest) -> dict:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")

    existing = supabase.table("sessions").select("id,tasks").eq("id", session_id).limit(1).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Session not found")

    tasks = existing.data[0].get("tasks") or []
    if task_index < 0 or task_index >= len(tasks):
        raise HTTPException(status_code=400, detail="Invalid task index")

    tasks[task_index]["completed"] = payload.completed
    updated = supabase.table("sessions").update({"tasks": tasks}).eq("id", session_id).execute()
    return {"session": updated.data[0] if updated.data else {"id": session_id, "tasks": tasks}}


@router.get("/history/{user_id}")
async def get_session_history(user_id: str) -> dict:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")

    history = (
        supabase.table("sessions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    return {"sessions": history.data or []}


@router.patch("/{session_id}/complete")
async def complete_session(session_id: str) -> dict:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase is not configured")
    updated = (
        supabase.table("sessions")
        .update({"status": "completed", "completed_at": datetime.utcnow().isoformat()})
        .eq("id", session_id)
        .execute()
    )
    return {"session": updated.data[0] if updated.data else {"id": session_id, "status": "completed"}}

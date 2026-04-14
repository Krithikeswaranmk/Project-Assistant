import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None


def format_chunks(chunks: list[dict]) -> str:
    preview_parts = []
    for chunk in chunks[:3]:
        file_path = chunk.get("file_path") or chunk.get("file") or "unknown"
        name = chunk.get("chunk_name") or chunk.get("name") or "snippet"
        code = (chunk.get("code_text") or chunk.get("code") or "")[:200]
        preview_parts.append(f"File: {file_path} | Function: {name}\n{code}\n---")
    return "\n".join(preview_parts) if preview_parts else "No repository context available."


def _fallback_tasks(focus_minutes: int) -> dict[str, Any]:
    base = max(10, focus_minutes // 3)
    tasks = [
        {
            "id": 1,
            "title": "Review current implementation",
            "description": "Scan the relevant files and identify the key gap blocking progress.",
            "estimated_minutes": base,
            "type": "review",
            "relevant_file": None,
            "completed": False,
        },
        {
            "id": 2,
            "title": "Implement prioritized change",
            "description": "Make the smallest focused code change that satisfies the main goal.",
            "estimated_minutes": base,
            "type": "code",
            "relevant_file": None,
            "completed": False,
        },
        {
            "id": 3,
            "title": "Validate and summarize",
            "description": "Run quick checks/tests and write a short summary of what was completed.",
            "estimated_minutes": focus_minutes - (base * 2),
            "type": "test",
            "relevant_file": None,
            "completed": False,
        },
    ]
    return {
        "tasks": tasks,
        "session_strategy": "Start with understanding, execute one high-impact change, then validate immediately.",
        "deadline_status": "on_track",
    }


def generate_session_plan(request, context_chunks: list[dict]) -> dict[str, Any]:
    if not client:
        return _fallback_tasks(request.focus_minutes)

    prompt = f"""
A developer wants to work on: {request.project_name}
Their goal for this session: {request.goal}
Project deadline: {request.deadline}
Available focus time: {request.focus_minutes} minutes
Project complexity: {request.complexity}

Relevant code context from their repository:
{format_chunks(context_chunks)}

Generate a focused task list for this session. Each task must be completable within the session.

Return JSON:
{{
  "tasks": [
    {{
      "id": <integer starting at 1>,
      "title": <string, short task name>,
      "description": <string, 1-2 sentences of what to do>,
      "estimated_minutes": <integer>,
      "type": "code" | "research" | "test" | "review" | "design",
      "relevant_file": <string, file path from context or null>
    }}
  ],
  "session_strategy": <string, 2 sentences on how to approach this session>,
  "deadline_status": "on_track" | "at_risk" | "behind"
}}

Rules:
- Total estimated_minutes must not exceed {request.focus_minutes}
- Generate 3-6 tasks depending on complexity
- Tasks should be specific and actionable, not vague
- Prioritize based on deadline proximity
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior software engineer helping a developer plan a focused work session. Respond ONLY with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or "{}"
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(content)

        tasks = parsed.get("tasks", [])
        total = 0
        for idx, task in enumerate(tasks, start=1):
            task["id"] = idx
            task["completed"] = bool(task.get("completed", False))
            task["estimated_minutes"] = int(task.get("estimated_minutes", 0) or 0)
            total += task["estimated_minutes"]
        if total > request.focus_minutes:
            scale = request.focus_minutes / max(1, total)
            for task in tasks:
                task["estimated_minutes"] = max(5, int(task["estimated_minutes"] * scale))

        return {
            "tasks": tasks,
            "session_strategy": parsed.get("session_strategy", "Work from highest-impact task to lowest-risk cleanup."),
            "deadline_status": parsed.get("deadline_status", "on_track"),
        }
    except Exception:
        return _fallback_tasks(request.focus_minutes)

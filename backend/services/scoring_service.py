import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY", "")) if os.getenv("GROQ_API_KEY") else None


def _default_scores(target_role: str) -> dict:
    return {
        "relevance_score": 50,
        "market_demand_score": 50,
        "key_skills": ["problem solving", "software development", "version control"],
        "missing_skills": [f"advanced {target_role}", "testing"],
        "one_line_summary": "Repository analyzed with fallback scoring.",
        "score_reasoning": "Scoring service was unavailable, so neutral defaults were used.",
    }


def score_repo(repo_name: str, readme: str, file_tree: list[str], target_role: str) -> dict:
    if not client:
        return _default_scores(target_role)

    prompt = f"""
Analyze this GitHub repository for a person targeting the role: {target_role}

Repository: {repo_name}
README (first 1000 chars): {readme[:1000]}
File tree: {json.dumps(file_tree[:50])}

Return a JSON object with exactly these fields:
{{
  "relevance_score": <integer 0-100, how relevant is this project to {target_role}>,
  "market_demand_score": <integer 0-100, how in-demand are these skills in 2024 job market>,
  "key_skills": [<list of 3-5 skill strings demonstrated in this project>],
  "missing_skills": [<list of 2-3 skills that would make this stronger for {target_role}>],
  "one_line_summary": <string, one sentence about what this project does>,
  "score_reasoning": <string, 2 sentences explaining the relevance score>
}}
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical recruiter and engineer. Respond ONLY with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or "{}"
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(content)
        parsed["relevance_score"] = int(parsed.get("relevance_score", 50))
        parsed["market_demand_score"] = int(parsed.get("market_demand_score", 50))
        return parsed
    except Exception:
        return _default_scores(target_role)

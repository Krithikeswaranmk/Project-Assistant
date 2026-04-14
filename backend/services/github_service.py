import os
from datetime import datetime

from github import Github

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".env", "venv", ".venv", "dist", "build"}


def get_user_repos(github_token: str, github_username: str) -> list[dict]:
    client = Github(github_token)
    user = client.get_user(github_username)
    repos = user.get_repos(sort="updated", direction="desc")

    result = []
    for repo in repos[:10]:
        readme_content = ""
        try:
            readme_content = repo.get_readme().decoded_content.decode("utf-8", errors="ignore")
        except Exception:
            readme_content = ""

        updated_at = repo.updated_at.isoformat() if isinstance(repo.updated_at, datetime) else None
        result.append(
            {
                "name": repo.name,
                "clone_url": repo.clone_url,
                "description": repo.description,
                "language": repo.language,
                "stargazers_count": repo.stargazers_count,
                "updated_at": updated_at,
                "readme_content": readme_content,
            }
        )
    return result


def get_file_tree(repo_path: str) -> list[str]:
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
            if any(part in SKIP_DIRS for part in rel_path.split(os.sep)):
                continue
            files.append(rel_path)
            if len(files) >= 100:
                return files
    return files

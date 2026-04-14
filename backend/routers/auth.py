import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from supabase import Client, create_client

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


class LogoutResponse(BaseModel):
    message: str


@router.get("/github")
async def github_login() -> RedirectResponse:
    if not GITHUB_CLIENT_ID or not GITHUB_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="GitHub OAuth is not configured")

    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        "&scope=repo,read:user,user:email"
    )
    return RedirectResponse(url=url)


@router.get("/github/callback")
async def github_callback(code: str = Query(...)) -> RedirectResponse:
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth credentials missing")

    async with httpx.AsyncClient(timeout=30.0) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to obtain access token")

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        user_resp.raise_for_status()
        gh_user = user_resp.json()

        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        email_resp.raise_for_status()
        email_data = email_resp.json()
        primary_verified_email = None
        for email in email_data:
            if email.get("primary") and email.get("verified"):
                primary_verified_email = email.get("email")
                break

    if supabase:
        github_username = gh_user.get("login", "")
        user_id = str(gh_user.get("id", github_username))
        payload = {
            "user_id": user_id,
            "github_username": github_username,
            "github_token": access_token,
            "avatar_url": gh_user.get("avatar_url"),
            "name": gh_user.get("name") or github_username,
        }
        supabase.table("profiles").upsert(payload, on_conflict="user_id").execute()

    return RedirectResponse(url="http://localhost:5173/dashboard?github_connected=true")


@router.post("/logout", response_model=LogoutResponse)
async def logout() -> LogoutResponse:
    return LogoutResponse(message="logged out")

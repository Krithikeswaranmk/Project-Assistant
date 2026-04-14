import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.auth import router as auth_router
from routers.onboard import router as onboard_router
from routers.profile import router as profile_router
from routers.session import router as session_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("project-pilot")

app = FastAPI(title="Project-Pilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(onboard_router, prefix="/api")
app.include_router(session_router, prefix="/api")
app.include_router(profile_router, prefix="/api")


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Project-Pilot backend started")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

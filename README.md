# Project-Pilot

Project-Pilot is an AI-first project assistant for students and professionals who want to level up their portfolios. It combines repository ingestion, code intelligence, and role-aware scoring to help users understand how their projects map to market expectations. It also provides focused, AI-generated work sessions to turn goals into actionable tasks.

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, Vite, TailwindCSS, Supabase JS, React Router, Axios |
| Backend | FastAPI, Groq API, PyGithub, GitPython, SentenceTransformers |
| Database | Supabase Postgres + pgvector |
| AI/RAG | AST chunking, embedding retrieval, context-grounded planning |

## Setup

1. Clone repository.
2. Configure environment variables.
   - Copy `backend/.env.example` to `backend/.env` and fill values.
   - Copy `frontend/.env.example` to `frontend/.env` and fill values.
3. Run the Supabase schema.
   - Open Supabase SQL Editor.
   - Run `backend/supabase_schema.sql`.
4. Start backend.

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

5. Start frontend.

```bash
cd frontend
npm install
npm run dev
```

## GitHub OAuth App Setup

1. Go to GitHub -> Settings -> Developer settings -> OAuth Apps -> New OAuth App.
2. Set Homepage URL: `http://localhost:5173`.
3. Set Callback URL: `http://localhost:8000/api/auth/github/callback`.
4. Copy Client ID and Client Secret into both backend and frontend `.env` files.

## Phase Roadmap

| Phase | Status | Scope |
|---|---|---|
| Phase 1 | ✅ | Onboarding, OAuth, dashboard, RAG ingest, focus sessions |
| Phase 2 | 🔜 | Deeper orchestration, advanced planning graphs, richer repo reasoning |
| Phase 3 | 🔜 | Voice features, commit-history intelligence, advanced safety and scaling |

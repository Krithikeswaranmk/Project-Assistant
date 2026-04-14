-- Enable pgvector extension
create extension if not exists vector;

-- Profiles table
create table if not exists profiles (
  id uuid primary key default gen_random_uuid(),
  user_id text unique not null,
  name text,
  github_username text,
  github_token text,
  avatar_url text,
  target_role text,
  experience_level text,
  focus_areas text[],
  onboarding_complete boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Repositories table
create table if not exists repositories (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references profiles(user_id),
  name text not null,
  description text,
  language text,
  stars integer default 0,
  last_updated timestamptz,
  relevance_score integer,
  market_demand_score integer,
  key_skills text[],
  missing_skills text[],
  one_line_summary text,
  score_reasoning text,
  indexed_at timestamptz default now()
);

-- Code chunks with embeddings
create table if not exists code_chunks (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  repo_name text not null,
  file_path text,
  chunk_type text,
  chunk_name text,
  code_text text,
  language text,
  embedding vector(384),
  created_at timestamptz default now()
);

-- Sessions table
create table if not exists sessions (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  project_name text,
  repo_name text,
  goal text,
  deadline date,
  focus_minutes integer,
  tasks jsonb,
  session_strategy text,
  deadline_status text,
  status text default 'active',
  created_at timestamptz default now(),
  completed_at timestamptz
);

-- Score feedback table
create table if not exists score_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  repo_name text not null,
  score_type text not null,
  helpful boolean not null,
  created_at timestamptz default now()
);

-- Vector similarity search function
create or replace function match_code_chunks(
  query_embedding vector(384),
  filter_user_id text,
  filter_repo_name text,
  match_count int default 5
)
returns table (
  id uuid,
  repo_name text,
  file_path text,
  chunk_type text,
  chunk_name text,
  code_text text,
  language text,
  similarity float
)
language sql stable
as $$
  select
    id,
    repo_name,
    file_path,
    chunk_type,
    chunk_name,
    code_text,
    language,
    1 - (embedding <=> query_embedding) as similarity
  from code_chunks
  where user_id = filter_user_id
    and repo_name = filter_repo_name
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- Indexes
create index if not exists idx_code_chunks_user_repo on code_chunks(user_id, repo_name);
create index if not exists idx_repositories_user on repositories(user_id);
create index if not exists idx_sessions_user on sessions(user_id);

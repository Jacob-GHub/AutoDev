-- AutoDev schema: one source of truth for repos, code index, call graph, and chat history.
-- Loaded automatically by docker-compose on first start (empty volume only).

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()

-- One row per GitHub repo. repo_id keeps the existing "owner_repo_hash" format.
CREATE TABLE repos (
    id              TEXT PRIMARY KEY,
    url             TEXT NOT NULL UNIQUE,
    indexed_commit  TEXT,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'indexing', 'ready', 'failed')),
    indexed_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- content_hash lets the indexer skip files that haven't changed since the last run.
CREATE TABLE files (
    id            BIGSERIAL PRIMARY KEY,
    repo_id       TEXT NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    path          TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    UNIQUE (repo_id, path)
);

-- code_hash lets the indexer reuse an embedding when a function's code is unchanged,
-- even if other parts of its file changed. text-embedding-3-small = 1536 dims.
CREATE TABLE functions (
    id              BIGSERIAL PRIMARY KEY,
    repo_id         TEXT NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    file_id         BIGINT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    qualified_name  TEXT NOT NULL,          -- e.g. "backend/graph.py:build_graph"
    start_line      INT NOT NULL,
    end_line        INT NOT NULL,
    code            TEXT NOT NULL,
    code_hash       TEXT NOT NULL,
    call_names      TEXT[] NOT NULL DEFAULT '{}',  -- raw names this function calls; resolved into `calls`
    embedding       vector(1536),
    UNIQUE (file_id, name, start_line)      -- same-named functions in one file stay distinct
);

CREATE INDEX functions_repo_name_idx ON functions (repo_id, name);
CREATE INDEX functions_repo_hash_idx ON functions (repo_id, code_hash);
CREATE INDEX functions_embedding_idx ON functions USING hnsw (embedding vector_cosine_ops);

-- Call graph edges. Rebuilt per repo on each index (AST-only, no API cost).
CREATE TABLE calls (
    caller_id  BIGINT NOT NULL REFERENCES functions(id) ON DELETE CASCADE,
    callee_id  BIGINT NOT NULL REFERENCES functions(id) ON DELETE CASCADE,
    PRIMARY KEY (caller_id, callee_id)
);

CREATE INDEX calls_callee_idx ON calls (callee_id);

-- Chat history, persisted per repo so it survives a page reload.
CREATE TABLE conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id     TEXT NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE messages (
    id               BIGSERIAL PRIMARY KEY,
    conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content          TEXT NOT NULL,
    tool_calls       JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX messages_conversation_idx ON messages (conversation_id, created_at);
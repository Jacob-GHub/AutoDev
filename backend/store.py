"""
Read-side queries over the index, plus conversation persistence.
Everything the agent's tools need, answered from Postgres instead of graph.json + Chroma.
"""

import uuid

import numpy as np
from psycopg.types.json import Jsonb

from db import get_conn
from utils.utils import get_embedding

EMBED_MODEL = "text-embedding-3-small"
MAX_MATCHES = 10
MAX_CODE_CHARS = (
    4_000  # per function in a tool result, to keep the agent's context small
)

_FUNC_COLS = "f.id, f.name, f.qualified_name, fi.path, f.start_line, f.end_line"
_FUNC_FROM = "FROM functions f JOIN files fi ON fi.id = f.file_id"


def _func(row, code=None, **extra):
    fid, name, qualified_name, path, start, end = row[:6]
    out = {
        "id": fid,
        "name": name,
        "qualified_name": qualified_name,
        "file": path,
        "start_line": start,
        "end_line": end,
    }
    if code is not None:
        out["code"] = code[:MAX_CODE_CHARS]
    out.update(extra)
    return out


# ---------------------------------------------------------------- functions & call graph


def find_functions(repo_id: str, name: str, with_code: bool = False) -> list:
    """
    Accepts a bare name ("build_graph"), a dotted name ("Foo.bar"), or a fully qualified
    name ("backend/graph.py:Foo.bar"). Returns every match, so same-named functions in
    different files are all visible instead of one silently shadowing the others.
    """
    name = name.strip()
    suffix = ":" + name
    cols = _FUNC_COLS + (", f.code" if with_code else "")
    with get_conn() as conn:
        rows = conn.execute(
            f"""SELECT {cols} {_FUNC_FROM}
                WHERE f.repo_id = %s
                  AND (f.name = %s OR f.qualified_name = %s
                       OR right(f.qualified_name, %s) = %s)
                ORDER BY fi.path, f.start_line
                LIMIT %s""",
            (repo_id, name, name, len(suffix), suffix, MAX_MATCHES),
        ).fetchall()
    return [_func(r, code=r[6] if with_code else None) for r in rows]


def _neighbors(repo_id: str, name: str, direction: str):
    """direction='callers' -> who calls it; direction='callees' -> what it calls."""
    targets = find_functions(repo_id, name)
    if not targets:
        return None

    # callers: edge.callee_id = target, report edge.caller_id (and vice versa)
    match_col, report_col = (
        ("callee_id", "caller_id")
        if direction == "callers"
        else ("caller_id", "callee_id")
    )
    ids = [t["id"] for t in targets]
    with get_conn() as conn:
        rows = conn.execute(
            f"""SELECT c.{match_col}, {_FUNC_COLS}
                FROM calls c
                JOIN functions f ON f.id = c.{report_col}
                JOIN files fi ON fi.id = f.file_id
                WHERE c.{match_col} = ANY(%s)
                ORDER BY fi.path, f.start_line""",
            (ids,),
        ).fetchall()

    grouped = {t["id"]: [] for t in targets}
    for target_id, *func_row in rows:
        f = _func(func_row)
        f.pop("id")
        grouped[target_id].append(f)

    return [
        {"function": t["qualified_name"], direction: grouped[t["id"]]} for t in targets
    ]


def get_callers(repo_id: str, name: str):
    return _neighbors(repo_id, name, "callers")


def get_callees(repo_id: str, name: str):
    return _neighbors(repo_id, name, "callees")


def semantic_search(repo_id: str, query: str, n: int = 5) -> list:
    embedding = np.asarray(get_embedding(query, model=EMBED_MODEL), dtype=np.float32)
    with get_conn() as conn:
        # The HNSW index covers every repo. Without iterative scan, the repo_id filter is
        # applied after the index returns its top candidates, which can leave fewer than
        # n results once several repos are indexed. strict_order keeps results sorted.
        # (Setting exists in pgvector >= 0.8; skipped on older versions.)
        if (
            conn.execute(
                "SELECT current_setting('hnsw.iterative_scan', true)"
            ).fetchone()[0]
            is not None
        ):
            conn.execute("SET LOCAL hnsw.iterative_scan = strict_order")
        rows = conn.execute(
            f"""SELECT {_FUNC_COLS}, f.code, 1 - (f.embedding <=> %s) AS score
                {_FUNC_FROM}
                WHERE f.repo_id = %s AND f.embedding IS NOT NULL
                ORDER BY f.embedding <=> %s
                LIMIT %s""",
            (embedding, repo_id, embedding, n),
        ).fetchall()
    return [_func(r, code=r[6], score=round(float(r[7]), 4)) for r in rows]


# ---------------------------------------------------------------- conversations


def get_or_create_conversation(repo_id: str, conversation_id=None) -> str:
    """Reuses the conversation if it exists for this repo, otherwise starts a new one."""
    with get_conn() as conn:
        if conversation_id:
            try:
                cid = uuid.UUID(str(conversation_id))
            except ValueError:
                cid = None
            if cid:
                row = conn.execute(
                    "SELECT id FROM conversations WHERE id = %s AND repo_id = %s",
                    (cid, repo_id),
                ).fetchone()
                if row:
                    return str(row[0])
        row = conn.execute(
            "INSERT INTO conversations (repo_id) VALUES (%s) RETURNING id", (repo_id,)
        ).fetchone()
        return str(row[0])


def load_history(conversation_id: str, limit: int = 20) -> list:
    """Last `limit` messages, oldest first, in the shape the OpenAI API expects."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT role, content FROM (
                   SELECT role, content, created_at, id FROM messages
                   WHERE conversation_id = %s
                   ORDER BY created_at DESC, id DESC
                   LIMIT %s
               ) recent ORDER BY created_at, id""",
            (conversation_id, limit),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def save_exchange(conversation_id: str, question: str, answer: str, tool_calls: list):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (%s, 'user', %s)",
            (conversation_id, question),
        )
        conn.execute(
            """INSERT INTO messages (conversation_id, role, content, tool_calls)
               VALUES (%s, 'assistant', %s, %s)""",
            (conversation_id, answer or "", Jsonb(tool_calls or [])),
        )

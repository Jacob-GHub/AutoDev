"""
Postgres connection pool for the AutoDev backend.

    pip install "psycopg[binary]" psycopg-pool pgvector

Usage:
    from db import get_conn
    with get_conn() as conn:
        conn.execute("SELECT ...")
"""

import os
from contextlib import contextmanager

import psycopg
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://autodev:autodev@localhost:5433/autodev"
)

REQUIRED_TABLES = {"repos", "files", "functions", "calls", "conversations", "messages"}

_pool = None


def _check_database():
    """Fail fast with a readable message instead of letting the pool retry for 30s."""
    try:
        conn = psycopg.connect(DATABASE_URL, connect_timeout=5)
    except psycopg.OperationalError as e:
        raise RuntimeError(
            f"Can't reach Postgres at {DATABASE_URL}. Is `docker compose up -d` running?\n{e}"
        ) from None

    with conn:
        has_vector = conn.execute(
            "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ).fetchall()
        }

    missing = REQUIRED_TABLES - tables
    if not has_vector or missing:
        raise RuntimeError(
            "Connected, but the schema isn't loaded "
            f"(pgvector: {'yes' if has_vector else 'no'}, missing tables: {sorted(missing) or 'none'}).\n"
            "Make sure db/schema.sql exists next to docker-compose.yml, then run:\n"
            "  docker compose down -v && docker compose up -d"
        )


def _configure(conn):
    # Lets psycopg send/receive Python lists and numpy arrays as pgvector values.
    register_vector(conn)


def _get_pool():
    global _pool
    if _pool is None:
        _check_database()
        _pool = ConnectionPool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            configure=_configure,
            open=True,
        )
    return _pool


@contextmanager
def get_conn():
    """Commits on success, rolls back on exception, returns the connection to the pool."""
    with _get_pool().connection() as conn:
        yield conn


def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


if __name__ == "__main__":
    # Smoke test: python db.py
    try:
        with get_conn() as conn:
            version = conn.execute("SELECT version()").fetchone()[0]
            ext = conn.execute(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            ).fetchone()[0]
            tables = conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1"
            ).fetchall()
        print(version)
        print("pgvector:", ext)
        print("tables:", ", ".join(t[0] for t in tables))
    except RuntimeError as e:
        print(e)
    finally:
        close_pool()

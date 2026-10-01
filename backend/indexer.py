"""
Incremental indexer: repo on disk -> Postgres (files, functions + embeddings, call graph).

Only files whose content changed get re-parsed, and the embedding API is only called for
functions whose exact code hasn't been embedded before in this repo. The call graph is
rebuilt from stored call names each run (pure AST data, no API cost).

    python indexer.py https://github.com/owner/repo            # index / update
    python indexer.py https://github.com/owner/repo --rebuild  # wipe and index from scratch
"""

import ast
import hashlib
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from urllib.parse import urlparse

import numpy as np

from db import close_pool, get_conn
from utils.utils import get_embeddings

REPOS_DIR = Path("repos")
SKIP_DIRS = {
    ".git",
    "venv",
    ".venv",
    "env",
    "node_modules",
    "__pycache__",
    "site-packages",
    "build",
    "dist",
    ".tox",
    ".mypy_cache",
}
EMBED_MODEL = "text-embedding-3-small"
MAX_EMBED_CHARS = (
    16_000  # keeps one function well under the model's 8k-token input limit
)
BATCH_MAX_ITEMS = 128
BATCH_MAX_CHARS = 400_000  # keeps one request well under the per-request token limit


# ---------------------------------------------------------------- data types


@dataclass
class ParsedFunction:
    name: str
    qualified_name: str  # "path/to/file.py:Class.method"
    start_line: int
    end_line: int
    code: str
    code_hash: str
    call_names: list


@dataclass
class IndexStats:
    repo_id: str
    commit: str
    cached: bool = False
    files_total: int = 0
    files_changed: int = 0
    files_deleted: int = 0
    functions_total: int = 0
    embedded: int = 0  # functions sent to the embedding API
    reused: int = 0  # functions whose embedding was reused by code hash
    embed_seconds: float = 0.0
    total_seconds: float = 0.0

    def __str__(self):
        if self.cached:
            return (
                f"{self.repo_id} @ {self.commit[:7]}: already indexed, "
                f"{self.functions_total} functions ({self.total_seconds:.2f}s)"
            )
        return (
            f"{self.repo_id} @ {self.commit[:7]}\n"
            f"  files:     {self.files_total} total, {self.files_changed} changed, {self.files_deleted} deleted\n"
            f"  functions: {self.functions_total} total, {self.embedded} embedded, {self.reused} reused\n"
            f"  time:      {self.total_seconds:.2f}s total, {self.embed_seconds:.2f}s in embedding API"
        )


# ---------------------------------------------------------------- git


def _git(args, cwd=None):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def normalize_url(github_url: str) -> str:
    """
    One canonical URL per repo, so ".../AutoDev", ".../AutoDev.git" and ".../autodev/"
    all map to the same repo_id instead of three separate copies in the database.
    """
    parts = urlparse(github_url.strip()).path.strip("/").split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid GitHub URL: {github_url}")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    return f"https://github.com/{owner}/{repo}".lower()


def get_repo_id(github_url: str) -> str:
    url = normalize_url(github_url)
    owner, repo = urlparse(url).path.strip("/").split("/")
    return f"{owner}_{repo}_{sha1(url.encode()).hexdigest()[:7]}"


def repo_path_for(repo_id: str) -> Path:
    return REPOS_DIR / repo_id / "raw"


def clone_or_update(github_url: str):
    """Shallow-clones the repo, or fast-forwards an existing clone to the remote's latest commit."""
    github_url = normalize_url(github_url)
    repo_id = get_repo_id(github_url)
    path = repo_path_for(repo_id)

    if (path / ".git").exists():
        _git(["fetch", "--depth", "1", "origin"], cwd=path)
        _git(["reset", "--hard", "FETCH_HEAD"], cwd=path)
    else:
        if path.exists():
            shutil.rmtree(path)  # leftover from a failed clone
        path.parent.mkdir(parents=True, exist_ok=True)
        _git(["clone", "--depth", "1", github_url, str(path)])

    return path, repo_id


# ---------------------------------------------------------------- parsing


def _sha256(data) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def _call_names(func_node) -> set:
    """Names called directly in this function's body (not inside nested defs/classes)."""
    names = set()
    stack = list(ast.iter_child_nodes(func_node))
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue  # nested scopes get their own entries
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
        stack.extend(ast.iter_child_nodes(node))
    return names


class _FunctionCollector(ast.NodeVisitor):
    """Collects every function, method, and nested function with its class/function scope."""

    def __init__(self, rel_path, lines):
        self.rel_path = rel_path
        self.lines = lines
        self.scope = []
        self.functions = []

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _visit_function(self, node):
        start = min([d.lineno for d in node.decorator_list] + [node.lineno])
        end = node.end_lineno or node.lineno
        code = "\n".join(self.lines[start - 1 : end])
        dotted = ".".join(self.scope + [node.name])
        self.functions.append(
            ParsedFunction(
                name=node.name,
                qualified_name=f"{self.rel_path}:{dotted}",
                start_line=start,
                end_line=end,
                code=code,
                code_hash=_sha256(code),
                call_names=sorted(_call_names(node)),
            )
        )
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function


def parse_file(source: str, rel_path: str) -> list:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []  # still recorded as a file, so it isn't re-parsed until it changes
    collector = _FunctionCollector(rel_path, source.splitlines())
    collector.visit(tree)
    return collector.functions


def scan_repo(root: Path) -> dict:
    """{relative_path: (source, content_hash)} for every .py file outside SKIP_DIRS."""
    files = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        raw = path.read_bytes()
        files[rel.as_posix()] = (raw.decode("utf-8", errors="replace"), _sha256(raw))
    return files


# ---------------------------------------------------------------- embeddings


def embed_texts(texts_by_hash: dict) -> dict:
    """Batch-embeds {code_hash: code} -> {code_hash: vector}."""
    items = [(h, code[:MAX_EMBED_CHARS]) for h, code in texts_by_hash.items()]
    out = {}
    batch, batch_chars = [], 0

    def flush():
        if batch:
            vectors = get_embeddings([text for _, text in batch], model=EMBED_MODEL)
            for (h, _), vec in zip(batch, vectors):
                out[h] = np.asarray(vec, dtype=np.float32)
            batch.clear()

    for h, text in items:
        if batch and (
            len(batch) >= BATCH_MAX_ITEMS or batch_chars + len(text) > BATCH_MAX_CHARS
        ):
            flush()
            batch_chars = 0
        batch.append((h, text))
        batch_chars += len(text)
    flush()
    return out


# ---------------------------------------------------------------- call graph


def resolve_calls(functions) -> list:
    """
    functions: rows of (id, name, file_id, call_names).
    A call to `name` resolves to a same-file function with that name if one exists,
    otherwise to the only function in the repo with that name. Ambiguous or external
    names (library calls, builtins) are dropped rather than guessed.
    """
    by_file_name, by_name = {}, {}
    for fid, name, file_id, _ in functions:
        by_file_name.setdefault((file_id, name), []).append(fid)
        by_name.setdefault(name, []).append(fid)

    edges = set()
    for fid, _, file_id, call_names in functions:
        for call in call_names or []:
            targets = by_file_name.get((file_id, call))
            if not targets and len(by_name.get(call, [])) == 1:
                targets = by_name[call]
            for target in targets or []:
                if target != fid:
                    edges.add((fid, target))
    return sorted(edges)


# ---------------------------------------------------------------- indexing


def index_repo(github_url: str, rebuild: bool = False) -> IndexStats:
    t0 = time.perf_counter()
    github_url = normalize_url(github_url)
    repo_path, repo_id = clone_or_update(github_url)
    commit = _git(["rev-parse", "HEAD"], cwd=repo_path)

    with get_conn() as conn:
        if rebuild:
            conn.execute("DELETE FROM repos WHERE id = %s", (repo_id,))
        indexed_commit, status = conn.execute(
            """INSERT INTO repos (id, url) VALUES (%s, %s)
               ON CONFLICT (id) DO UPDATE SET url = EXCLUDED.url
               RETURNING indexed_commit, status""",
            (repo_id, github_url),
        ).fetchone()

        # Fast path: nothing new upstream since the last successful index.
        if status == "ready" and indexed_commit == commit:
            count = conn.execute(
                "SELECT count(*) FROM functions WHERE repo_id = %s", (repo_id,)
            ).fetchone()[0]
            return IndexStats(
                repo_id,
                commit,
                cached=True,
                functions_total=count,
                total_seconds=time.perf_counter() - t0,
            )

        conn.execute("UPDATE repos SET status = 'indexing' WHERE id = %s", (repo_id,))

    try:
        stats = _index(repo_id, repo_path, commit)
    except Exception:
        with get_conn() as conn:
            conn.execute("UPDATE repos SET status = 'failed' WHERE id = %s", (repo_id,))
        raise

    stats.total_seconds = time.perf_counter() - t0
    return stats


def _index(repo_id: str, repo_path: Path, commit: str) -> IndexStats:
    stats = IndexStats(repo_id, commit)

    # 1. Diff what's on disk against what's stored.
    disk = scan_repo(repo_path)
    with get_conn() as conn:
        stored = {
            path: (fid, content_hash)
            for fid, path, content_hash in conn.execute(
                "SELECT id, path, content_hash FROM files WHERE repo_id = %s",
                (repo_id,),
            ).fetchall()
        }

    changed = [p for p, (_, h) in disk.items() if p not in stored or stored[p][1] != h]
    deleted = [p for p in stored if p not in disk]
    stats.files_total, stats.files_changed, stats.files_deleted = (
        len(disk),
        len(changed),
        len(deleted),
    )

    # 2. Parse only the changed files.
    parsed = {p: parse_file(disk[p][0], p) for p in changed}
    needed = {f.code_hash: f.code for funcs in parsed.values() for f in funcs}

    # 3. Reuse any embedding whose exact code is already stored (e.g. untouched functions
    #    in a file where something else changed), and embed only what's genuinely new.
    reused = {}
    if needed:
        with get_conn() as conn:
            reused = dict(
                conn.execute(
                    """SELECT DISTINCT ON (code_hash) code_hash, embedding FROM functions
                   WHERE repo_id = %s AND code_hash = ANY(%s) AND embedding IS NOT NULL""",
                    (repo_id, list(needed)),
                ).fetchall()
            )

    to_embed = {h: code for h, code in needed.items() if h not in reused}
    t_embed = time.perf_counter()
    fresh = embed_texts(to_embed) if to_embed else {}
    stats.embed_seconds = time.perf_counter() - t_embed
    embeddings = {**reused, **fresh}

    total_new_funcs = sum(len(fs) for fs in parsed.values())
    stats.embedded = sum(
        1 for fs in parsed.values() for f in fs if f.code_hash in fresh
    )
    stats.reused = total_new_funcs - stats.embedded

    # 4. Write everything in one transaction, so a failure never leaves a half-updated index.
    with get_conn() as conn, conn.transaction(), conn.cursor() as cur:
        stale_ids = [stored[p][0] for p in changed + deleted if p in stored]
        if stale_ids:
            # Cascades to those files' functions and call edges.
            cur.execute("DELETE FROM files WHERE id = ANY(%s)", (stale_ids,))

        for path in changed:
            file_id = cur.execute(
                "INSERT INTO files (repo_id, path, content_hash) VALUES (%s, %s, %s) RETURNING id",
                (repo_id, path, disk[path][1]),
            ).fetchone()[0]
            for f in parsed[path]:
                cur.execute(
                    """INSERT INTO functions
                       (repo_id, file_id, name, qualified_name, start_line, end_line,
                        code, code_hash, call_names, embedding)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        repo_id,
                        file_id,
                        f.name,
                        f.qualified_name,
                        f.start_line,
                        f.end_line,
                        f.code,
                        f.code_hash,
                        f.call_names,
                        embeddings[f.code_hash],
                    ),
                )

        # 5. Rebuild the call graph for the whole repo: a changed file can change what
        #    unchanged files' calls resolve to.
        cur.execute(
            "DELETE FROM calls USING functions f WHERE calls.caller_id = f.id AND f.repo_id = %s",
            (repo_id,),
        )
        functions = cur.execute(
            "SELECT id, name, file_id, call_names FROM functions WHERE repo_id = %s",
            (repo_id,),
        ).fetchall()
        edges = resolve_calls(functions)
        if edges:
            cur.executemany(
                "INSERT INTO calls (caller_id, callee_id) VALUES (%s, %s)", edges
            )
        stats.functions_total = len(functions)

        cur.execute(
            "UPDATE repos SET indexed_commit = %s, status = 'ready', indexed_at = now() WHERE id = %s",
            (commit, repo_id),
        )

    return stats


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("usage: python indexer.py <github_url> [--rebuild]")
        sys.exit(1)
    try:
        print(index_repo(args[0], rebuild="--rebuild" in sys.argv))
    finally:
        close_pool()

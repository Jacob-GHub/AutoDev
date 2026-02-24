import ast
import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict
from graphqe import GraphQueryEngine
from typing import List
import subprocess


@dataclass
class FunctionNode:
    calls: list
    id: str
    name: str
    location: str
    startLine: int
    endLine: int


@dataclass
class FileNode:
    id: str
    name: str
    filePath: str
    functions: List[FunctionNode]


@dataclass
class FolderNode:
    id: str
    name: str
    path: str
    files: List[FileNode]
    folders: List["FolderNode"]


def find_functions(file_path: Path, rel_path: str, tree) -> List[Dict]:
    functions = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_id = f"function:{rel_path}:{node.name}"
            functions[func_id] = FunctionNode(
                calls=[],
                id=func_id,
                name=node.name,
                location=rel_path,
                startLine=node.lineno,
                endLine=node.end_lineno if hasattr(node, "end_lineno") else node.lineno,
            )
    return functions


def initialize_functions(file_path, rel_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    user_funcs = find_functions(file_path, rel_path, tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_id = f"function:{rel_path}:{node.name}"
            if func_id not in user_funcs:
                continue
            for func_node in ast.walk(node):
                if isinstance(func_node, ast.Call):
                    if isinstance(func_node.func, ast.Name):
                        call_name = func_node.func.id
                        # Store all calls, not just same-file ones
                        user_funcs[func_id].calls.append((call_name, None))
                    elif isinstance(func_node.func, ast.Attribute):
                        call_name = func_node.func.attr
                        user_funcs[func_id].calls.append((call_name, None))

    return user_funcs


def build_graph(repo_root: Path) -> Dict:
    fileNodes = []
    all_funcs = {}  # global map of function name -> function_id across all files

    # Pass 1: collect all functions across all files
    for file_path in repo_root.rglob("*.py"):
        rel_path = str(file_path.relative_to(repo_root))
        file_node = FileNode(
            id=f"file:{rel_path}",
            name=file_path.name,
            filePath=rel_path,
            functions=[],
        )
        fileNodes.append(file_node)

        function_nodes = initialize_functions(file_path, rel_path)
        if not function_nodes:
            continue
        for func_id, func_node in function_nodes.items():
            file_node.functions.append(func_node)
            # Register by name globally — last definition wins if there are duplicates
            all_funcs[func_node.name] = func_id
            all_funcs[func_id] = func_id  # also register by full id

    # Pass 2: resolve calls using global function map
    for file_node in fileNodes:
        for func in file_node.functions:
            resolved_calls = []
            for call_name, _ in func.calls:
                if call_name in all_funcs:
                    resolved_calls.append((call_name, all_funcs[call_name]))
                # drop external library calls
            func.calls = resolved_calls

        return {"filenodes": [asdict(n) for n in fileNodes]}


def get_current_commit(repo_path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True
    )
    return result.stdout.strip()


def get_or_build_graph(repo_path: Path, repo_id: str) -> dict:
    graph_path = Path("repos") / repo_id / "graph.json"
    commit_path = Path("repos") / repo_id / "commit.txt"

    current_commit = get_current_commit(repo_path)

    if graph_path.exists() and commit_path.exists():
        cached_commit = commit_path.read_text().strip()
        if cached_commit == current_commit:
            with open(graph_path) as f:
                return json.load(f)

    raw_graph = build_graph(repo_path)
    save_graph(Path("repos") / repo_id, raw_graph)
    commit_path.write_text(current_commit)
    return raw_graph


def save_graph(repo_root: Path, graph: Dict):
    graph_path = repo_root / "graph.json"
    with open(graph_path, "w") as f:
        json.dump(graph, f, indent=2)
    print(f"Saved graph to {graph_path}")


# Example usage:
# if __name__ == "__main__":
# repo_id = "Jacob-GHub_AutoDev_9dd2f6d"
# repo_path = Path("repos") / repo_id / "raw"
# graph = build_graph(repo_path)
# save_graph(Path("repos") / repo_id, graph)
# engine = GraphQueryEngine(graph)
# print(engine.get_called_functions("function:backend/query.py:query"))
# print(engine.get_calling_functions("function:backend/query.py:query"))

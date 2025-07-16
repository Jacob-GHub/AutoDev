import ast
import os
import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict
from uuid import uuid4

from dataclasses import dataclass, field
from typing import List

@dataclass
class FunctionNode:
    calls: list
    id: str
    name: str
    location: str  
    startLine : int
    endLine: int

@dataclass
class FileNode:
    id: str
    name: str
    filePath: str
    functions: List[FunctionNode] = field(default_factory=list)

@dataclass
class FolderNode:
    id: str
    name: str
    path: str
    files: List[FileNode] = field(default_factory=list)
    folders: List["FolderNode"] = field(default_factory=list)

def extract_functions(file_path: Path, rel_path: str) -> List[Dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_id = f"function:{rel_path}:{node.name}"
            calls = []
            for func_node in ast.walk(node):
                if isinstance(func_node,ast.Call):
                    if isinstance(func_node.func,ast.Name):
                        calls.append(func_node.func.id)
                    # elif isinstance(func_node.func,ast.Attribute):
                    #     calls.append(func_node.func.attr)
            functions.append(FunctionNode(
                calls,
                id=func_id,
                name=node.name,
                location=rel_path,
                startLine=node.lineno,
                endLine=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
            ))
    return functions

def build_graph(repo_root: Path) -> Dict:
    fileNodes: List[FileNode] = []

    for file_path in repo_root.rglob("*.py"):
        rel_path = str(file_path.relative_to(repo_root))

        # File node
        file_node = FileNode (
            id=f"file:{rel_path}",
            name=file_path.name,
            filePath=rel_path,
            functions=[],
        )

        fileNodes.append(file_node)

        # Function nodes
        function_nodes = extract_functions(file_path, rel_path)
        file_node.functions.extend(function_nodes)

        # Edges: function -> file

    return {
        "filenodes": [asdict(n) for n in fileNodes],
    }

def save_graph(repo_root: Path, graph: Dict):
    graph_path = repo_root / "graph.json"
    with open(graph_path, "w") as f:
        json.dump(graph, f, indent=2)
    print(f"Saved graph to {graph_path}")

# Example usage:
# if __name__ == "__main__":
repo_id = "Jacob-GHub_AutoDev_9dd2f6d"
repo_path = Path("repos") / repo_id / "raw"
graph = build_graph(repo_path)
# print(graph)
save_graph(Path("repos") / repo_id, graph)


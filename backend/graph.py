import ast
import os
import json
from utils.code_parser import extract_functions
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict
from uuid import uuid4

@dataclass
class CodeNode:
    id: str
    type: str 
    name: str
    filePath: str
    startLine: int = None
    endLine: int = None
    edges: list

@dataclass
class FileNode:
    parent: str
    id: str
    functions: list
    edges: list

@dataclass
class CodeEdge:
    from_id: str
    to_id: str
    type: str  

def build_graph(repo_root: Path) -> Dict:
    nodes: List[CodeNode] = []
    edges: List[CodeEdge] = []

    for file_path in repo_root.rglob("*.py"):
        rel_path = str(file_path.relative_to(repo_root))

        # File node
        file_node = CodeNode(
            id=f"file:{rel_path}",
            type="file",
            name=file_path.name,
            filePath=rel_path
        )
        nodes.append(file_node)

        # Function nodes
        function_nodes = extract_functions(file_path, rel_path)
        nodes.extend(function_nodes)

        # Edges: function -> file
        for fn in function_nodes:
            edges.append(CodeEdge(
                from_id=fn.id,
                to_id=file_node.id,
                type="defined_in"
            ))

    return {
        "nodes": [asdict(n) for n in nodes],
        "edges": [asdict(e) for e in edges]
    }

def save_graph(repo_root: Path, graph: Dict):
    graph_path = repo_root / "graph.json"
    with open(graph_path, "w") as f:
        json.dump(graph, f, indent=2)
    print(f"Saved graph to {graph_path}")

# Example usage:
if __name__ == "__main__":
    repo_id = "your_repo_id_here"
    repo_path = Path("repos") / repo_id / "raw"
    graph = build_graph(repo_path)
    save_graph(Path("repos") / repo_id, graph)

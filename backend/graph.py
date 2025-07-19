import ast
import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict
from graphqe import GraphQueryEngine
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
    functions: List[FunctionNode]

@dataclass
class FolderNode:
    id: str
    name: str
    path: str
    files: List[FileNode]
    folders: List["FolderNode"]

def find_functions(file_path: Path, rel_path: str,tree) -> List[Dict]:
    functions = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_id = f"function:{rel_path}:{node.name}"
            functions[func_id] = FunctionNode(
                calls = [],
                id=func_id,
                name=node.name,
                location=rel_path,
                startLine=node.lineno,
                endLine=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
            )
    return functions

def initialize_functions(file_path,rel_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    
    user_funcs = find_functions(file_path,rel_path,tree)
    # for func in user_funcs.keys():
    #     print(func)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_id = f"function:{rel_path}:{node.name}"
            for func_node in ast.walk(node):
                if isinstance(func_node,ast.Call):
                    if isinstance(func_node.func,ast.Name):
                        call_id = f"function:{rel_path}:{func_node.func.id}"
                        if call_id in user_funcs:
                            # print("function: ",node.name, "calls: ", func_node.func.id)
                            user_funcs[func_id].calls.append((func_node.func.id,call_id))
                    elif isinstance(func_node.func,ast.Attribute):
                        call_id = f"function:{rel_path}:{func_node.func.attr}"
                        if call_id in user_funcs:
                            # print("function: ",node.name, "calls: ", func_node.func.attr)
                            user_funcs[func_id].calls.append((func_node.func.attr,call_id))
    # print(user_funcs)
    return user_funcs


def build_graph(repo_root: Path) -> Dict:
    fileNodes= []

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
        function_nodes = initialize_functions(file_path, rel_path)
        for func_node in function_nodes.values():
            file_node.functions.append(func_node)
        # Edges: function -> file

    return {
        "filenodes": [asdict(n) for n in fileNodes]
    }

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



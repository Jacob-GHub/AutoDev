from graph import get_or_build_graph
from graphqe import GraphQueryEngine
from openai import OpenAI
from agent import run_agent
import json

client = OpenAI()

def handleQuestion(collection, query_msg, repo_path, repo_id, history=[]):
    return run_agent(query_msg, repo_path, repo_id, collection, history)


def call_graph(query_msg, func_name, repo_path, repo_id):
    if not func_name:
        return {
            "type": "call_graph",
            "question": query_msg,
            "results": [{"target": "unknown", "callers": []}]
        }
    
    raw_graph = get_or_build_graph(repo_path, repo_id)
    graph_engine = GraphQueryEngine(raw_graph)
    func = graph_engine.get_function_by_name(func_name)
    
    if not func:
        return {
            "type": "call_graph",
            "question": query_msg,
            "results": [{"target": func_name, "callers": []}]
        }
    
    callers = graph_engine.get_calling_functions(func["id"])

    return {
        "type": "call_graph",
        "question": query_msg,
        "results": [{"target": func_name, "callers": callers}],
    }

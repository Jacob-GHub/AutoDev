from collections import defaultdict
from typing import List, Optional

class GraphQueryEngine:
    def __init__(self, graph_json: dict):
        self.function_map = {}  # Maps function_id to function object
        self.calls_from = defaultdict(list)  # Maps function_id -> list of called function_ids
        self.calls_to = defaultdict(list)  # Reverse: who calls this?
        self.file_map = {}  # Maps file_id to file object

        # Build maps from the input graph
        for file in graph_json['filenodes']:
            self.file_map[file['id']] = file
            for func in file['functions']:
                self.function_map[func['id']] = func
                for call in func.get('calls', []):
                    if len(call) == 2:
                        self.calls_from[func['id']].append(call[1])
                        self.calls_to[call[1]].append(func['id'])
        print(self.calls_from,self.calls_to)

    def get_called_functions(self, function_id: str) -> List[str]:
        #input a given function id and returns a list of functions that it calls
        return self.calls_from.get(function_id, [])

    def get_calling_functions(self, function_id: str) -> List[str]:
        #input a given function id and returns a list of functions that call it
        return self.calls_to.get(function_id, [])

    def get_function_by_name(self, name: str) -> Optional[dict]:
        return next((f for f in self.function_map.values() if f['name'] == name), None)

    def get_file_of_function(self, function_id: str) -> Optional[dict]:
        for file in self.file_map.values():
            if any(func['id'] == function_id for func in file['functions']):
                return file
        print("no files found corresponding to function id: ",function_id, "returning None")
        return None

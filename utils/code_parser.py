import ast

def parse(file):
    with open(file, "r") as f:
        source_file = f.read()
    tree = ast.parse(source_file)
    lines = source_file.splitlines()
    # print(lines)
    # print(ast.dump(tree,indent=4))
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start_line = node.lineno
            end_line = node.end_lineno
            # print(lines[start_line-1:end_line+1])
            code = ("\n".join(lines[start_line - 1:end_line]))
            functions.append({
                "name":node.name,
                "start_line":node.lineno-1,
                "end_line":node.end_lineno,
                "code":code,
                "file":file
            })
    return functions


print(parse("testing.py") )
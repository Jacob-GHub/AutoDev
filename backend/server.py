# from fastapi import FastAPI, UploadFile, Form
# from pathlib import Path
# import shutil
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS  
import json
import sys
from chroma import create_collection,clone_repo
from query import handleQuestion

app = Flask(__name__)
CORS(app)

@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    question = data.get("question")
    repo_url = data.get("repoUrl")
    history = data.get("history", [])[-20:]

    if not question or not repo_url:
        return jsonify({"error": "Missing question or repoUrl"}), 400

    def generate():
        try:
            # Step 1: Cloning
            yield f"data: {json.dumps({'status': 'cloning', 'message': 'Cloning repository...'})}\n\n"
            repo_path, repo_id = clone_repo(repo_url)

            if not repo_path:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to clone repository'})}\n\n"
                return

            # Step 2: Indexing
            yield f"data: {json.dumps({'status': 'indexing', 'message': 'Indexing codebase...'})}\n\n"
            collection = create_collection(repo_path, repo_id)

            if collection is None:
                yield f"data: {json.dumps({'status': 'error', 'message': 'No Python files found in this repository'})}\n\n"
                return

            # Step 3: Thinking
            yield f"data: {json.dumps({'status': 'thinking', 'message': 'Agent is reasoning...'})}\n\n"
            result = handleQuestion(collection, question, repo_path, repo_id, history)

            # Step 4: Done
            yield f"data: {json.dumps({'status': 'done', 'answer': result})}\n\n"

        except Exception as e:
            print("Server error:", str(e))
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(port=3000)

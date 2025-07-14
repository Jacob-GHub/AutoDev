# from fastapi import FastAPI, UploadFile, Form
# from pathlib import Path
# import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS  

from chroma import create_collection,clone_repo
from query import query

app = Flask(__name__)
CORS(app)

@app.route("/api/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        question = data.get("question")
        repo_url = data.get("repoUrl")

        if not question or not repo_url:
            return jsonify({"error": "Missing question or repoUrl"}), 400

        print(question,repo_url)
        
        repo_path,repo_id = clone_repo(repo_url)
        print(repo_path)
        if repo_path:
            collection = create_collection(repo_path,repo_id)
        result = query(collection, question)
        print(jsonify({"answer": result}))
        return jsonify({"answer": result})

    except Exception as e:
        print("Server error:", str(e)) 
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=3000)

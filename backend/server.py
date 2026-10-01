import json
import threading
from collections import defaultdict

from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS

import store
from agent import run_agent
from indexer import get_repo_id, index_repo, repo_path_for

app = Flask(__name__)
CORS(app)

# Two questions about the same repo at once would otherwise run git fetch and the
# index write concurrently on the same rows. One lock per repo serializes that.
_repo_locks = defaultdict(threading.Lock)
_repo_locks_guard = threading.Lock()


def _lock_for(repo_id):
    with _repo_locks_guard:
        return _repo_locks[repo_id]


def _event(**payload):
    return f"data: {json.dumps(payload, default=str)}\n\n"


@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    question = (data.get("question") or "").strip()
    repo_url = data.get("repoUrl")
    conversation_id = data.get("conversationId")

    if not question or not repo_url:
        return jsonify({"error": "Missing question or repoUrl"}), 400

    try:
        repo_id = get_repo_id(repo_url)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    def generate():
        try:
            # Step 1: Clone or fetch, then index only what changed.
            yield _event(
                status="indexing", message="Syncing and indexing repository..."
            )
            with _lock_for(repo_id):
                stats = index_repo(repo_url)

            if stats.functions_total == 0:
                yield _event(
                    status="error",
                    message="No Python functions found in this repository",
                )
                return

            if not stats.cached:
                yield _event(
                    status="indexing",
                    message=f"Indexed {stats.functions_total} functions "
                    f"({stats.files_changed} files changed, {stats.embedded} newly embedded)",
                )

            # Step 2: Load the conversation from the database, not from the client.
            conv_id = store.get_or_create_conversation(repo_id, conversation_id)
            history = store.load_history(conv_id)

            # Step 3: Run the agent.
            yield _event(status="thinking", message="Agent is reasoning...")
            result = run_agent(question, repo_id, repo_path_for(repo_id), history)

            # Step 4: Persist and return.
            store.save_exchange(
                conv_id, question, result["answer"], result["tool_calls"]
            )
            yield _event(status="done", answer=result, conversationId=conv_id)

        except Exception as e:
            app.logger.exception("ask failed")
            yield _event(status="error", message=str(e))

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/api/conversations/<conversation_id>/messages", methods=["GET"])
def conversation_messages(conversation_id):
    """Lets the extension restore a conversation after a page reload."""
    try:
        return jsonify({"messages": store.load_history(conversation_id, limit=100)})
    except Exception:
        return jsonify({"messages": []})


if __name__ == "__main__":
    app.run(port=3000, threaded=True)

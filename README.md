# AutoDev

Ask questions about any Python repository on GitHub, right on its page.

AutoDev is a Chrome extension with a small mascot named Gloop. Open a repository,
click Gloop, and ask something like "How does indexing work?" or "What calls this
function?". An AI agent reads the code, follows how functions call each other, and
answers with the steps it took.
<img width="1261" height="720" alt="chrome-capture-2026-10-07-ezgif com-optimize" src="https://github.com/user-attachments/assets/a6ac9f1e-2426-4cd3-94e2-d4d84a7f82e8" />

## How it works

1. **Index.** The backend clones the repo and parses every Python function. Each
   function is stored in PostgreSQL with an embedding (pgvector) and its call graph.
2. **Stay fresh.** Files and functions are hashed, so after a new commit only the
   code that changed is re-parsed and re-embedded.
3. **Answer.** An agent uses tools (semantic search, read a function, find callers,
   find callees) to trace the code before it answers.
4. **Show.** The extension streams progress to the page, and Gloop's mood follows it:
   reading, thinking, done.

## Tech stack

- **Extension:** React, TypeScript, CSS, Webpack
- **Backend:** Python, Flask, OpenAI API
- **Database:** PostgreSQL with pgvector, run with Docker Compose

## Setup

You need Docker, Python 3.10+, Node.js, Chrome, and an OpenAI API key.

### 1. Backend

```bash
cd backend
echo "OPENAI_API_KEY=your-key-here" > .env
docker compose up -d
pip install -r requirements.txt
python server.py
```

The server runs at `http://127.0.0.1:3000`.

### 2. Extension

```bash
cd frontend
npm install
npm run build
```

Then load it into Chrome:

1. Go to `chrome://extensions`
2. Turn on **Developer mode**
3. Click **Load unpacked** and select the `frontend/dist` folder

### 3. Try it

Open any Python repository on GitHub, click Gloop in the bottom-right corner, and
ask a question. The first question on a repo takes longer because it has to be indexed.

# AutoDev — AI Agent for GitHub Repositories

AutoDev is a Chrome extension that deploys a multi-hop reasoning agent over any public GitHub repository. Ask complex questions about a codebase and get back accurate, sourced answers, without cloning the repo or leaving your browser.

> "How does authentication work in this repo?"  
> "Trace the flow from the API endpoint to the database."  
> "What calls `handleQuestion` and where is it defined?"

---

![chrome-capture-2026-02-26](https://github.com/user-attachments/assets/9966fc1b-813d-4b42-b22b-301a1680e993)


## How It Works

AutoDev uses an agent loop powered by OpenAI's function calling API. Rather than doing a single search and returning results, the agent autonomously chains multiple tool calls to build a complete picture before answering.

For a question like "how does authentication work?", the agent might:
1. Search for authentication-related code semantically
2. Find the `auth_middleware` function and read its source
3. Trace what `auth_middleware` calls using the call graph
4. Read the `verify_token` implementation
5. Synthesize a full explanation with file references

Every step is visible to the user in a collapsible reasoning trace.

---

## Architecture

**Chrome Extension (Frontend)**
- React/TypeScript sidebar injected into GitHub pages
- Streams progress updates in real time via Server-Sent Events
- Displays agent reasoning chain alongside the final answer

**Flask Backend**
- Clones and indexes repositories on first request
- Builds a cross-file AST call graph using two-pass Python parsing
- Stores function embeddings in ChromaDB for semantic search
- Runs the agent loop using OpenAI function calling

**Agent Tools**
- `find_function_location` — exact AST lookup for function definitions
- `get_callers` — find all functions that call a given function
- `get_called_functions` — find all functions a given function calls
- `get_function_code` — read actual source code of a function
- `semantic_search` — vector search over function embeddings
- `get_repo_structure` — read README and top-level file structure

**Caching**
- Repositories are cloned once and reused across sessions
- Call graphs and embeddings are invalidated automatically when the repo's git commit changes
- Repeated queries on the same repo respond in under 5 seconds

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/Jacob-GHub/AutoDev
cd AutoDev
```

### 2. Install backend dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Set your OpenAI API key
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### 4. Start the backend
```bash
python server.py
```

### 5. Load the extension
- Open `chrome://extensions`
- Enable Developer Mode
- Click "Load unpacked" and select the `frontend/dist` folder
- Navigate to any public Python GitHub repository and click "Ask Repo Question"

---

## Limitations

- Currently supports Python repositories only
- Requires a local backend server running on port 3000
- Cross-file call resolution is limited to same-language calls

---

## Roadmap

- JavaScript/TypeScript support
- Local repository support via companion CLI
- Change impact analysis ("if I modify this function, what breaks?")
- Conversational follow-up with full session memory

---

## License

MIT

# 🔍 CodeQuery — Natural Language Search for Your Codebase

CodeQuery is a tool that lets you **ask natural language questions about your codebase**, and get back the **most relevant functions or code chunks**, using machine learning and semantic search.

> 💬 Ask things like:  
> "Where do we add a new user?" → returns `def create_user(...)`

---

## 🧠 How It Works

1. **Parses your codebase** using Python's `ast` module to extract functions.
2. **Generates vector embeddings** for each code chunk using a transformer model (e.g., CodeBERT).
3. **Stores the embeddings** in a Chroma vector database.
4. **Embeds user questions** and performs a similarity search.
5. **Returns the most relevant code snippets**.

---

## 🚀 Example

```bash
$ python query.py "How do we connect to the database?"
```

✅ Result:
```python
def connect_to_db():
    engine = create_engine(DB_URI)
    return engine.connect()
```

---

## 🔧 Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/codequery
cd codequery
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Main libraries used:
- `sentence-transformers`
- `chromadb`
- `tqdm`
- `ast`
- `python-dotenv` (optional for config)

### 3. Run the Indexer

This will:
- Walk through the repo
- Extract functions
- Embed them
- Store them in Chroma

```bash
python index_codebase.py --path ./your_project/
```

### 4. Ask Questions About Your Code

```bash
python query.py "Where is the login handled?"
```

---

## ⚙️ Configuration

You can change the embedding model in `config.py`:

```python
EMBEDDING_MODEL = "microsoft/codebert-base"  # or "sentence-transformers/code-search-net"
```

You can also change:
- Chroma collection name
- Code chunk size limits
- File types to scan (`.py`, `.js`, etc.)

---

## 📁 Project Structure

```
codequery/
├── index_codebase.py       # Parses code and populates Chroma
├── query.py                # Search interface
├── utils/
│   ├── ast_utils.py        # Function parsing
│   └── embedding.py        # Model loading and embedding
├── config.py
└── README.md
```

---

## 📌 Goals

- [x] Extract functions using AST
- [] Embed code using CodeBERT
- [] Store embeddings in Chroma
- [] Natural language query → nearest code match
- [ ] Add web UI (Flask or Streamlit)
- [ ] Support multiple languages (JavaScript, Go, etc.)
- [ ] Ranking results based on usage frequency

---

## 🙌 Contributing

Pull requests welcome! If you have ideas for:
- More intelligent chunking
- Better ranking/scoring
- UI/UX for code search

feel free to open an issue or PR.

---

## 🧠 Inspiration

Inspired by the idea of making codebases **as searchable as Stack Overflow**, but *custom to your own project.*

---

## 📜 License

MIT License.

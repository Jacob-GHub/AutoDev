# 🔍 AutoDev — Natural Language Search for Your Codebase

AutoDev is a tool that lets you **ask natural language questions about your codebase**, and get back the **most relevant functions or code chunks**, using machine learning and semantic search.

> 💬 Ask things like:  
> "Where do we add a new user?" → returns `def create_user(...)`

---

## 🧠 How It Works

1. **Parses your codebase** and extracts each function
2. **Generates vector embeddings** for each code chunk using openAI's embedding model.
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
git clone https://github.com/yourusername/autodev
cd autodev
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

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

---

## 📁 Project Structure

```
autodev/
├── index_codebase.py       # Parses code and populates Chroma
├── query.py                # Search interface
├── utils/
│   ├── ast_utils.py        # Function parsing
│   └── embedding.py        # Model loading and embedding
├── config.py
└── README.md
```

---


## 🧠 Inspiration

Inspired by the idea of making codebases **as searchable as Stack Overflow**, but *custom to your own project.*

---

## 📜 License

MIT License.

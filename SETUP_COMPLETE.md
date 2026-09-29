# ✅ Setup Complete - Ready to Run!

## 📦 Installation

```bash
# 1. Install Python dependencies
uv sync

# If that fails, use pip directly:
uv pip install -r starter_code/requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY=your_key_here

# 3. Install frontend
cd frontend && npm install && cd ..
```

## 🚀 Running the Application

### ⭐ Recommended: Run from starter_code directory

**Terminal 1 - Backend:**
```bash
cd starter_code
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Alternative: Run from project root

**Terminal 1 - Backend:**
```bash
# From project root (where pyproject.toml is)
uvicorn starter_code.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 🎯 Both Methods Work!

The code now supports **both** running patterns:
- ✅ Run `uvicorn main:app` from inside `starter_code/`
- ✅ Run `uvicorn starter_code.main:app` from project root

**How it works:**
- `main.py` and `cli.py` use try/except to handle both import paths
- If relative imports fail, they fall back to absolute imports
- `pyproject.toml` is in project root
- `uv sync` creates `.venv` in project root
- Both running methods work seamlessly!

## 🔍 Verify Installation

### Test Backend
```bash
# From starter_code/
cd starter_code
python -c "from agent.graph import build_graph; build_graph(); print('✓ Agent OK')"

# Or from project root
python -c "from starter_code.agent.graph import build_graph; build_graph(); print('✓ Agent OK')"
```

### Test Database
```bash
cd starter_code
python db_duckdb.py
# Should show 4 tables with row counts
```

### Test CLI
```bash
# From starter_code/
cd starter_code
python cli.py

# Or from project root
python -m starter_code.cli
```

## 📁 Project Structure

```
agentic-ai-rca-challenge/          # Project root
├── pyproject.toml                 # Python package config (uv sync uses this)
├── .venv/                         # Virtual environment (created by uv sync)
├── .env                           # Environment variables (API keys)
│
├── starter_code/                  # Backend code
│   ├── __init__.py                # Makes it a package
│   ├── main.py                    # FastAPI app (supports both run methods)
│   ├── cli.py                     # CLI interface (supports both run methods)
│   ├── db_duckdb.py               # Database
│   ├── agent/                     # Multi-agent system
│   │   ├── graph.py
│   │   ├── orchestrator_agent.py
│   │   ├── investigation_agent.py
│   │   ├── data_retrieval_agent.py
│   │   ├── analysis_agent.py
│   │   ├── explanation_agent.py
│   │   └── prompts/               # Skills in markdown
│   └── requirements.txt
│
└── frontend/                      # React frontend
    ├── package.json
    └── src/
```

## 🛠️ Development Workflow

### When Working in starter_code/
```bash
# Terminal 1
cd starter_code
uvicorn main:app --reload

# Terminal 2
cd frontend
npm run dev
```

### When Working from Project Root
```bash
# Terminal 1
uvicorn starter_code.main:app --reload

# Terminal 2
cd frontend
npm run dev
```

## 🐳 Docker Option

```bash
docker compose up --build
```

This runs both backend and frontend with:
- ✅ Backend: uvicorn --reload (auto-reload)
- ✅ Frontend: npm run dev (hot reload)
- ✅ Code mounted as volumes

## 💡 Why This Works

### Flexible Import Strategy

**main.py and cli.py use:**
```python
try:
    from agent.graph import build_graph  # Works from starter_code/
except ImportError:
    from starter_code.agent.graph import build_graph  # Works from root
```

This means:
- ✅ Run from `starter_code/`: Uses relative imports
- ✅ Run from project root: Uses absolute imports
- ✅ No need to modify code based on where you run from!

### Package Structure

- `pyproject.toml` defines the package in project root
- `uv sync` installs dependencies in `.venv` at project root
- `starter_code/` is marked as a package in pyproject.toml
- Both running methods have access to all dependencies

## 🎯 Choose Your Preference

**Most developers prefer:**
```bash
cd starter_code
uvicorn main:app --reload
```

**But you can also use:**
```bash
# From project root
uvicorn starter_code.main:app --reload
```

**Both work perfectly!** 🎉

## 📚 Next Steps

1. Make sure `.env` has your `ANTHROPIC_API_KEY`
2. Choose your preferred running method
3. Start backend and frontend
4. Open http://localhost:3000
5. Start investigating anomalies!

See [RUN_COMMANDS.md](RUN_COMMANDS.md) for detailed command reference.

---

**You're all set!** Both running methods are supported and work seamlessly. 🚀

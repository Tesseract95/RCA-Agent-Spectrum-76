# Run Commands - Network Investigation Agent

Complete guide for running the application locally and with Docker.

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- uv (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker (optional, for containerized deployment)

## 🚀 Local Development (Recommended)

### First Time Setup

```bash
# 1. Clone/Navigate to project
cd agentic-ai-rca-challenge

# 2. Setup Python backend with uv
uv sync

# If uv sync fails, use pip instead:
# uv pip install -r starter_code/requirements.txt

# 3. Setup environment variables
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your_key_here

# 4. Setup frontend
cd frontend
npm install
cd ..
```

### Running Backend (FastAPI with uvicorn)

**Terminal 1 - Start Backend:**

You can run from either location:

**Option A: From starter_code directory (simpler)**
```bash
cd starter_code
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option B: From project root (where pyproject.toml is)**
```bash
# From project root
uvicorn starter_code.main:app --reload --host 0.0.0.0 --port 8000

# Or with uv
uv run uvicorn starter_code.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be available at:**
- API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Running Frontend (React with Vite)

**Terminal 2 - Start Frontend:**

```bash
cd frontend

# Start development server with hot reload
npm run dev

# Or specify host explicitly
npm run dev -- --host 0.0.0.0
```

**Frontend will be available at:**
- http://localhost:3000

### Running CLI (Interactive Terminal)

**Alternative to web interface:**

**Option A: From starter_code directory (simpler)**
```bash
cd starter_code
python cli.py
```

**Option B: From project root**
```bash
python -m starter_code.cli

# Or with uv
uv run python -m starter_code.cli
```

## 🐳 Docker Development

### Using Docker Compose (All Services)

```bash
# 1. Make sure .env is configured
cp .env.example .env
# Edit .env and add your API key

# 2. Build and start all services
docker compose up --build

# Or run in background
docker compose up -d --build

# 3. View logs
docker compose logs -f

# 4. Stop services
docker compose down

# 5. Stop and remove volumes (fresh start)
docker compose down -v
```

**Services will be available at:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

### Docker with Hot Reload

The docker-compose.yml is configured for development with:
- Backend: Code mounted, uvicorn with `--reload`
- Frontend: Code mounted, `npm run dev` with hot reload
- Any code changes will automatically reload!

### Building Individual Services

```bash
# Build backend only
docker compose build backend

# Build frontend only  
docker compose build frontend

# Run specific service
docker compose up backend
docker compose up frontend
```

## 📊 Verify Installation

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {
#   "status": "online",
#   "agent_ready": true,
#   "database_ready": true,
#   "agents": {...}
# }
```

### Test Frontend

Open browser to http://localhost:3000 - should see the chat interface.

### Test Database

```bash
cd starter_code

# Using uv
uv run python db_duckdb.py

# Should show 4 tables with row counts
```

## 🔧 Development Workflow

### Recommended Setup

**Terminal Layout:**
```
┌─────────────────────────┬─────────────────────────┐
│  Terminal 1: Backend    │  Terminal 2: Frontend   │
│  (uvicorn with reload)  │  (npm run dev)          │
│                         │                         │
│  cd starter_code        │  cd frontend            │
│  uv run uvicorn ...     │  npm run dev            │
└─────────────────────────┴─────────────────────────┘
```

### Making Changes

**Backend Changes:**
- Edit files in `starter_code/`
- Uvicorn automatically reloads
- Check terminal for errors

**Frontend Changes:**
- Edit files in `frontend/src/`
- Vite automatically reloads
- Check browser for updates

**Agent Skills Changes:**
- Edit files in `starter_code/agent/prompts/*.md`
- Backend needs manual restart

## 🛠️ Common Commands

### Backend Management

```bash
cd starter_code

# Start with custom port
uv run uvicorn main:app --reload --port 8080

# Start without reload (production-like)
uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Run CLI instead
uv run python cli.py

# Test database
uv run python db_duckdb.py

# Test agent build
uv run python -c "from agent.graph import build_graph; build_graph(); print('✓ OK')"
```

### Frontend Management

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Docker Management

```bash
# Start services
docker compose up

# Start in background
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart specific service
docker compose restart backend
docker compose restart frontend

# Stop services
docker compose down

# Clean everything (including volumes)
docker compose down -v
docker system prune -a

# Rebuild after changes
docker compose up --build
```

## 🐛 Troubleshooting

### Backend Issues

**"No LLM API key found"**
```bash
# Make sure .env exists and has ANTHROPIC_API_KEY
cat .env | grep ANTHROPIC_API_KEY

# Should show: ANTHROPIC_API_KEY=your_key_here
```

**"Module not found"**
```bash
# Reinstall dependencies
uv sync

# Or manually
pip install -e .
```

**"Database not initialized"**
```bash
cd starter_code
uv run python db_duckdb.py
# Should initialize and show 4 tables
```

**Port 8000 already in use**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --port 8080
```

### Frontend Issues

**"Cannot connect to backend"**
- Make sure backend is running on port 8000
- Check VITE_API_URL in frontend/.env
- Check CORS settings in starter_code/main.py

**Port 3000 already in use**
```bash
# Kill process
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- --port 3001
```

**"Module not found" in frontend**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Docker Issues

**"Port already allocated"**
```bash
# Stop all compose services
docker compose down

# Or change ports in docker-compose.yml
```

**"Cannot connect to Docker daemon"**
```bash
# Start Docker Desktop (macOS/Windows)
# Or start docker service (Linux)
sudo systemctl start docker
```

**Changes not reflecting**
```bash
# Rebuild containers
docker compose up --build

# Or remove and rebuild
docker compose down
docker compose up --build
```

## 📝 Quick Reference

### Environment Variables (.env)

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_key_here
```

### Project Structure

```
starter_code/
├── agent/              # All agent files (flat structure)
│   ├── graph.py
│   ├── state.py
│   ├── tools.py
│   ├── orchestrator_agent.py
│   ├── investigation_agent.py
│   ├── data_retrieval_agent.py
│   ├── analysis_agent.py
│   ├── explanation_agent.py
│   └── prompts/       # Agent skills (markdown)
├── db_duckdb.py       # Database adapter
├── main.py            # FastAPI application
└── cli.py             # CLI interface

frontend/
├── src/
│   ├── App.jsx        # Main component
│   ├── services/
│   │   └── api.js     # API client
│   └── ...
└── package.json
```

### Default Ports

- Backend (FastAPI): 8000
- Frontend (Vite): 3000
- API Docs: 8000/docs

## 🎯 Quick Start Commands

### Fastest Way to Run

**Option A: From starter_code (easiest)**
```bash
# Setup (one time)
uv sync  # Or: uv pip install -r starter_code/requirements.txt
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env
cd frontend && npm install && cd ..

# Run (every time)
# Terminal 1:
cd starter_code && uvicorn main:app --reload

# Terminal 2:
cd frontend && npm run dev

# Open: http://localhost:3000
```

**Option B: From project root**
```bash
# Setup (one time)
uv sync
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env
cd frontend && npm install && cd ..

# Run (every time)
# Terminal 1:
uvicorn starter_code.main:app --reload

# Terminal 2:
cd frontend && npm run dev

# Open: http://localhost:3000
```

### Docker Quick Start

```bash
# Setup (one time)
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env

# Run
docker compose up --build

# Open: http://localhost:3000
```

---

**For more details, see:**
- README.md - Complete documentation
- QUICKSTART.md - 5-minute getting started guide
- ARCHITECTURE.md - System architecture

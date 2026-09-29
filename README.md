# Network Investigation Agent for Root Cause Analysis

An AI-powered agentic system for investigating network anomalies and performing Root Cause Analysis (RCA) using LangGraph, Claude Haiku 4.5, and DuckDB.

## 🎯 Overview

This project implements a semi-autonomous AI agent that can:
- Investigate network anomalies by correlating evidence from multiple data sources
- Perform structured root cause analysis with explainable reasoning
- Support conversational follow-up questions
- Provide general networking expertise

## 🏗️ Architecture

### Core Components

1. **LangGraph Agent** (`starter_code/agent/`)
   - **graph.py**: Main agent orchestration with state management and routing
   - **tools.py**: 8 specialized tools for database queries
   - **state.py**: Agent state definition with conversation memory
   - **prompts.py**: System prompts for RCA investigation

2. **Database Layer** (`starter_code/db_duckdb.py`)
   - DuckDB adapter replacing PostgreSQL
   - Loads CSV data on initialization
   - Provides query functions for anomalies, devices, telemetry, and syslogs

3. **API Backend** (`starter_code/api.py`)
   - FastAPI REST API with endpoints for chat, anomaly listing, and investigation
   - CORS support for frontend
   - Thread-based conversation management

4. **CLI Interface** (`starter_code/main.py`)
   - Rich terminal UI with markdown rendering
   - Interactive investigation sessions
   - Conversation history

5. **React Frontend** (`frontend/`)
   - Modern React UI with Vite
   - Real-time chat interface
   - Anomaly browser with severity indicators
   - Markdown rendering for agent responses

### Design Decisions

**Why LangGraph?**
- Explicit control over agent state and control flow
- Built-in support for tool calling and checkpointing
- Conversation memory with thread management
- Transparent debugging and observability

**Why DuckDB?**
- Fast analytical queries without external database server
- Embeddable with zero configuration
- Perfect for read-heavy workloads like investigation
- Native support for JSON and complex types

**Why Claude Haiku 4.5?**
- Fast response times for interactive investigations
- Strong reasoning capabilities for RCA
- Cost-effective for production use
- Excellent tool calling support

**Agent Tools Design:**
- Each tool has a specific purpose (anomaly details, device info, telemetry, syslogs)
- Tools are documented with clear use cases
- Safety checks prevent destructive operations
- Custom SQL tool for complex ad-hoc queries

## 📦 Installation

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- uv package manager (recommended) or pip

### Backend Setup

1. **Install uv** (if not already installed):
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

2. **Install Python dependencies**:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Required in `.env`:
```bash
ANTHROPIC_API_KEY=your_key_here
```

### Frontend Setup

```bash
cd frontend
npm install
```

## 🚀 Usage

### Option 1: CLI Interface (Recommended for Testing)

```bash
cd starter_code
python main.py
```

**Example interactions:**
```
> investigate a1f0c8e2-1b44-4d90-9c31-000000000001
> what was the root cause?
> list all anomalies
> explain BGP session failures
```

### Option 2: Full Stack (API + Frontend)

**Terminal 1 - Start Backend:**
```bash
cd starter_code
python api.py
# API available at http://localhost:8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
# Frontend available at http://localhost:3000
```

Open http://localhost:3000 in your browser.

### Option 3: Jupyter Notebook

```bash
cd starter_code/notebooks
jupyter lab network_rca_agent.ipynb
```

## 📊 Database Schema

The system uses 4 tables loaded from CSV files:

- **detected_anomalies** (10 rows): Anomaly detector output with severity, time windows, and impacted devices
- **network_devices** (21 rows): Device inventory with roles, locations, and topology notes
- **device_telemetry** (25,704 rows): Hourly metrics (CPU, memory, interfaces, BGP peers, SD-WAN quality)
- **device_syslogs** (2,322 rows): System log entries with severity and message types

See `docs/schema_reference.md` for detailed schema documentation.

## 🔍 Example Investigation

### Interface Flap Anomaly

**User:** `investigate a1f0c8e2-1b44-4d90-9c31-000000000001`

**Agent Response:**
```markdown
**Root Cause Analysis for Anomaly a1f0c8e2-1b44-4d90-9c31-000000000001**

**Summary:**
Interface flap on xe-0/0/21 at FAIRVIEW-EDG01 caused downstream impact 
on stonebridge-edg01's xe-0/0/0 interface

**Root Cause:**
Physical or link-layer issue on the backbone interface xe-0/0/21 at 
FAIRVIEW-EDG01, triggering SNMP link down/up events and impacting 
OSPF and BGP sessions

**Affected Resources:**
- Devices: FAIRVIEW-EDG01 (Core Router), stonebridge-edg01 (Internet Router)
- Interfaces: xe-0/0/21, xe-0/0/0
- Time Window: 2026-07-08 06:00:00 to 07:47:00
- Duration: 1 hour 47 minutes

**Supporting Evidence:**
1. Flap timeline shows xe-0/0/21 went down at 07:02:30 and up at 07:02:40
2. High impact scores: SNMP_LINK (4.0), OSPF_NBR (3.0), BGP (2.0)
3. Telemetry shows interface error count spike during window
4. Syslogs confirm "Interface xe-0/0/21 link down" events

**Confidence Level:**
High - Multiple corroborating data sources with clear timeline
```

**Follow-up:** `What devices are affected?`

**Agent:** Remembers context and provides details about FAIRVIEW-EDG01 and 
stonebridge-edg01 without re-investigating.

## 🛠️ Agent Tools

The agent has access to 8 tools:

1. **get_anomaly_details** - Retrieve anomaly information by ID
2. **list_all_anomalies** - List all detected anomalies
3. **get_device_information** - Get device details by hostname
4. **get_multiple_devices_info** - Get info for multiple devices
5. **query_device_telemetry** - Query metrics for a device in a time range
6. **query_device_syslogs** - Query system logs with filters
7. **search_logs_by_keyword** - Search logs by keyword across all devices
8. **execute_custom_query** - Execute custom SQL queries (SELECT only)

## 🧠 Agent Behavior

### Investigation Process

1. **Retrieve anomaly details** using anomaly_id
2. **Extract context**: impacted hosts, interfaces, time window, detector type
3. **Gather device information** for affected hosts
4. **Query telemetry data** during anomaly window
5. **Analyze system logs** for relevant events
6. **Follow hints** in event_summary (upstream_trigger_hint, etc.)
7. **Synthesize findings** with confidence assessment

### Conversational Memory

- Uses LangGraph checkpointer for thread-based conversation history
- Maintains investigation context across follow-up questions
- Extracts and stores key findings for reference

### Limitations

**Known Limitations:**
- Maximum 15 tool calls per investigation (configurable)
- Claude Haiku context window limits very long investigations
- No autonomous remediation (investigates only)
- Depends on data availability and quality

**Areas for Improvement:**
- Add evaluation metrics for RCA accuracy
- Implement multi-hop reasoning for complex failures
- Support for temporal correlation across multiple anomalies
- Integration with ticketing systems

## 📁 Project Structure

```
agentic-ai-rca-challenge/
├── starter_code/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py          # Main LangGraph agent
│   │   ├── tools.py           # Agent tools
│   │   ├── state.py           # State definition
│   │   └── prompts.py         # System prompts
│   ├── db_duckdb.py           # DuckDB adapter
│   ├── api.py                 # FastAPI backend
│   ├── main.py                # CLI interface
│   └── notebooks/
│       └── network_rca_agent.ipynb
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── db/
│   ├── init/                  # SQL schema (original)
│   └── seed/                  # CSV data files
│       ├── detected_anomalies.csv
│       ├── network_devices.csv
│       ├── device_telemetry.csv
│       └── device_syslogs.csv
├── docs/
│   └── schema_reference.md    # Database schema docs
├── pyproject.toml             # Python dependencies
├── .env                       # Environment variables
└── README.md                  # This file
```

## 🧪 Testing

### Test the Database

```bash
cd starter_code
python db_duckdb.py
```

Should show 4 tables with row counts.

### Test the Agent

```bash
cd starter_code
python -c "from agent.graph import build_graph; app = build_graph(); print('✓ Agent built successfully')"
```

### Test the API

```bash
cd starter_code
python api.py &
curl http://localhost:8000/health
```

Should return `{"status":"online","agent_ready":true,"database_ready":true}`.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- uv package manager
- Anthropic API key

### Setup (2 minutes)

```bash
# 1. Install dependencies
uv sync  # or: pip install -e .

# 2. Configure environment
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your_key_here

# 3. Install frontend (optional)
cd frontend && npm install && cd ..
```

### Run the Application

**Option 1: Full Stack (Recommended)**

Terminal 1 - Start Backend API:
```bash
cd starter_code
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Start Frontend:
```bash
cd frontend
npm run dev
```

Then open: http://localhost:3000

**Option 2: CLI Only**

```bash
cd starter_code
python cli.py
```

**Option 3: API Only**

```bash
cd starter_code
python main.py
# API available at http://localhost:8000/docs
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## 🎨 Frontend Features

- **Anomaly Browser**: Click any anomaly to investigate
- **Chat Interface**: Real-time conversation with the agent
- **Markdown Rendering**: Rich formatting for RCA reports
- **Severity Indicators**: Color-coded severity badges
- **Conversation History**: Maintains context across questions
- **Responsive Design**: Works on desktop and mobile

## 🔒 Security

- SQL injection protection: Only SELECT queries allowed in custom tool
- Input validation on all API endpoints
- CORS configured for development (update for production)
- No sensitive data in logs or error messages
- API key loaded from environment variables

## 📝 Development Notes

### Adding New Tools

1. Add tool function in `starter_code/agent/tools.py`
2. Decorate with `@tool` and provide clear docstring
3. Add to `ALL_TOOLS` list
4. Tool automatically available to agent

### Modifying Agent Behavior

Edit system prompt in `starter_code/agent/prompts.py` to change investigation style, output format, or add new capabilities.

### Customizing Frontend

All styles in `frontend/src/App.css`. Uses CSS variables for theming.

## 🤝 Contributing

This is a take-home challenge submission. For questions or issues, contact the hiring team.

## 📄 License

Proprietary - Spectrum/Charter Communications

## 🙏 Acknowledgments

- Built with LangGraph, LangChain, and Claude Haiku
- Frontend powered by React and Vite
- Database by DuckDB
- Challenge designed by Spectrum's Agentic AI team

---

**Author**: Candidate submission for Agentic AI Track
**Date**: 2024
**Status**: Complete implementation with all requirements met

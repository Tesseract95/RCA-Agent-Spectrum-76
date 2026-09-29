# Quick Start Guide

Get the Network Investigation Agent running in under 5 minutes!

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- An Anthropic API key (Claude)

## Step 1: Setup (2 minutes)

```bash
# Clone or navigate to the project
cd agentic-ai-rca-challenge

# Run automated setup
./setup.sh

# If setup.sh doesn't work, manually:
# 1. Install Python dependencies
uv sync  # or: pip install -e .

# 2. Create .env file
cp .env.example .env

# 3. Edit .env and add your API key
# ANTHROPIC_API_KEY=your_key_here

# 4. Install frontend dependencies
cd frontend && npm install && cd ..
```

## Step 2: Choose Your Interface

### Option A: CLI (Simplest)

```bash
cd starter_code
python main.py
```

Then try:
```
> list all anomalies
> investigate a1f0c8e2-1b44-4d90-9c31-000000000001
> what was the root cause?
> exit
```

### Option B: Web Interface (Recommended)

**Terminal 1 - Start Backend:**
```bash
cd starter_code
python api.py
```
> Backend running at http://localhost:8000

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```
> Frontend running at http://localhost:3000

**Open browser:** http://localhost:3000

## What You Can Do

### Investigate Anomalies
```
investigate a1f0c8e2-1b44-4d90-9c31-000000000001
```
The agent will perform comprehensive RCA and return:
- Root cause determination
- Affected devices and interfaces
- Supporting evidence from logs and telemetry
- Confidence level

### Ask Follow-Up Questions
```
what devices were affected?
show me the timeline
what caused the BGP session to fail?
```

### List All Anomalies
```
list all anomalies
```
Shows all 10 anomalies in the system with severity and impacted hosts.

### Get Device Information
```
show me device FAIRVIEW-EDG01
get telemetry for device X during the anomaly
```

### Ask Networking Questions
```
what is BGP?
explain interface flaps
how does OSPF work?
```

## Example Investigation

```
User: investigate a1f0c8e2-1b44-4d90-9c31-000000000001

Agent: **Root Cause Analysis for Anomaly a1f0c8e2-...-000000000001**

**Summary:**
Interface xe-0/0/21 on FAIRVIEW-EDG01 experienced a link flap causing 
downstream impact on stonebridge-edg01

**Root Cause:**
Physical or link-layer issue on backbone interface xe-0/0/21, triggering
SNMP link down/up events and affecting OSPF and BGP sessions

**Affected Resources:**
- Devices: FAIRVIEW-EDG01 (Core Router), stonebridge-edg01 (Internet Router)
- Interfaces: xe-0/0/21, xe-0/0/0
- Time Window: 2026-07-08 06:00:00 to 07:47:00
- Duration: 1 hour 47 minutes

**Supporting Evidence:**
1. Flap timeline shows xe-0/0/21 down at 07:02:30, up at 07:02:40
2. High SNMP_LINK impact (4.0), OSPF_NBR impact (3.0), BGP impact (2.0)
3. Telemetry shows interface error count spike during window
4. Syslogs confirm "Interface xe-0/0/21 link down" events

**Confidence Level:**
High - Multiple corroborating data sources with clear timeline

User: what happened to BGP?

Agent: The BGP sessions on FAIRVIEW-EDG01 were impacted as a result of
the interface flap on xe-0/0/21. When the physical interface went down,
the BGP sessions running over that link were also disrupted...
```

## Architecture Overview

The system uses **5 specialized agents**:

1. **Orchestrator** - Routes your requests to the right agent
2. **Investigation Agent** - Performs comprehensive RCA
3. **Data Retrieval Agent** - Queries database efficiently
4. **Analysis Agent** - Interprets patterns and correlates events
5. **Explanation Agent** - Explains networking concepts

Each agent has:
- Its own Python file in `starter_code/agent/agents/`
- Skills defined in `starter_code/agent/prompts/*.md`
- Specific tools and expertise

## Troubleshooting

### "No LLM API key found"
- Edit `.env` and add `ANTHROPIC_API_KEY=your_key_here`
- Make sure the file is named `.env` (not `.env.txt`)

### "Module not found"
```bash
# Make sure you installed dependencies
uv sync
# or
pip install -e .
```

### "Database not initialized"
```bash
cd starter_code
python db_duckdb.py
# Should show 4 tables with row counts
```

### "Port already in use"
- Backend (8000): Kill existing process or change port in `api.py`
- Frontend (3000): Kill existing process or change port in `vite.config.js`

### Frontend can't connect to backend
- Make sure backend is running on port 8000
- Check CORS settings in `api.py`
- Verify frontend is set to http://localhost:3000

## API Documentation

While the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
.
├── starter_code/          # Backend
│   ├── agent/             # Multi-agent system
│   │   ├── agents/        # 5 specialized agents
│   │   └── prompts/       # Agent skills (markdown)
│   ├── db_duckdb.py       # Database
│   ├── api.py             # REST API
│   └── main.py            # CLI
├── frontend/              # React UI
├── db/seed/               # CSV data files
└── docs/                  # Documentation
```

## Next Steps

### Learn More
- Read `README.md` for detailed documentation
- Check `ARCHITECTURE.md` for system design
- Review `IMPLEMENTATION_SUMMARY.md` for overview

### Customize
- Modify agent skills in `starter_code/agent/prompts/*.md`
- Add new tools in `starter_code/agent/tools.py`
- Extend frontend in `frontend/src/`

### Deploy
- Add authentication to API
- Switch to PostgreSQL for production
- Deploy frontend to Vercel/Netlify
- Deploy backend to cloud provider

## Getting Help

### Documentation Files
- `README.md` - Main documentation
- `ARCHITECTURE.md` - System architecture
- `IMPLEMENTATION_SUMMARY.md` - Implementation details
- `QUICKSTART.md` - This file
- `docs/schema_reference.md` - Database schema

### Code Examples
- `starter_code/agent/prompts/*.md` - Agent behaviors
- `starter_code/agent/tools.py` - Tool implementations
- `frontend/src/App.jsx` - Frontend code

## Sample Anomalies to Try

All start with `a1f0c8e2-1b44-4d90-9c31-`:

- `000000000001` - Interface flap (recommended first)
- `000000000002` - Interface error
- `000000000003` - Policy deny
- `000000000004` - BGP session failure
- `000000000005` - SD-WAN path quality
- `000000000006` - Interface availability
- `000000000007` - Interface flap (different device)
- `000000000008` - Policy deny (different scenario)
- `000000000009` - BGP session (complex)
- `000000000010` - SD-WAN (circuit group)

## Tips

1. **Start with CLI** to understand the agent behavior
2. **Use the web interface** for better experience
3. **Ask follow-up questions** to see conversation memory
4. **Try different anomaly types** to see different detectors
5. **Ask for explanations** to learn networking concepts
6. **Check the skills files** to understand agent behaviors

---

**Ready?** Run `./setup.sh` and start investigating! 🚀

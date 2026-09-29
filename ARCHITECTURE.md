# Network Investigation Agent - Architecture Documentation

## Overview

This is a production-ready Multi-Agent System for network anomaly investigation and root cause analysis, built with LangGraph, Claude Haiku 4.5, DuckDB, and React.

## System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  - Chat Interface  - Anomaly Browser  - Markdown Rendering  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST
┌───────────────────────────▼─────────────────────────────────┐
│                 FastAPI Backend                             │
│  - /chat  - /anomalies  - /investigate  - /health          │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              Multi-Agent System (LangGraph)                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Orchestrator Agent (Supervisor)             │   │
│  │  - Request classification                           │   │
│  │  - Intelligent routing                              │   │
│  │  - Conversation context                             │   │
│  └──────┬───────┬──────────┬─────────┬─────────────────┘   │
│         │       │          │         │                     │
│  ┌──────▼─┐ ┌──▼────┐ ┌───▼───┐ ┌──▼──────┐             │
│  │Investig│ │Data   │ │Analysi│ │Explanati│             │
│  │ation   │ │Retriev│ │s      │ │on       │             │
│  │Agent   │ │al     │ │Agent  │ │Agent    │             │
│  └────┬───┘ │Agent  │ └───┬───┘ └────┬────┘             │
│       │     └───┬───┘     │          │                   │
│       └─────────┼─────────┴──────────┘                   │
│                 │ Tools                                    │
│  ┌──────────────▼───────────────────────────────────┐     │
│  │  8 Specialized Tools for Data Access             │     │
│  │  - get_anomaly_details                           │     │
│  │  - query_device_telemetry                        │     │
│  │  - query_device_syslogs                          │     │
│  │  - search_logs_by_keyword                        │     │
│  │  - get_device_information                        │     │
│  │  - execute_custom_query                          │     │
│  └──────────────┬───────────────────────────────────┘     │
└─────────────────┼───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│         Database Layer (DuckDB)                     │
│  - detected_anomalies     - network_devices         │
│  - device_telemetry       - device_syslogs          │
│  (Loaded from CSV files on initialization)          │
└─────────────────────────────────────────────────────┘
```

## Multi-Agent Architecture

### Design Pattern: Supervisor (Orchestrator)

The system uses a **Supervisor pattern** where an Orchestrator agent routes requests to specialized agents based on intent classification.

#### Why This Pattern?

1. **Separation of Concerns**: Each agent has a specific role and expertise
2. **Scalability**: Easy to add new specialized agents
3. **Maintainability**: Agents are independently testable and modifiable
4. **Performance**: Agents can be optimized for their specific tasks
5. **Modularity**: Clear boundaries between components

### Agent Breakdown

#### 1. Orchestrator Agent
**File**: `starter_code/agent/agents/orchestrator_agent.py`
**Skills**: `starter_code/agent/prompts/orchestrator_skills.md`

**Responsibilities:**
- Parse user intent from messages
- Extract entities (anomaly IDs, device names)
- Classify requests into categories
- Route to appropriate specialized agent
- Maintain conversation context

**Routing Logic:**
- Investigation keywords → Investigation Agent
- Data queries → Data Retrieval Agent
- Analysis requests → Analysis Agent
- Explanation questions → Explanation Agent
- List anomalies → Handle directly

**Key Features:**
- Context-aware routing (considers active investigations)
- Anomaly ID extraction
- Simple query handling

#### 2. Investigation Agent
**File**: `starter_code/agent/agents/investigation_agent.py`
**Skills**: `starter_code/agent/prompts/investigation_skills.md`
**Max Loops**: 15

**Responsibilities:**
- Lead comprehensive RCA investigations
- Follow structured methodology
- Coordinate evidence gathering
- Synthesize findings into clear conclusions
- Assess confidence levels

**Methodology:**
1. Retrieve anomaly details
2. Gather device context
3. Analyze telemetry data
4. Review system logs
5. Follow investigative hints
6. Synthesize and conclude

**Tools Used**: All 8 tools

**Output Format**: Structured RCA report with:
- Summary
- Root Cause
- Affected Resources
- Supporting Evidence
- Confidence Level
- Additional Context

#### 3. Data Retrieval Agent
**File**: `starter_code/agent/agents/data_retrieval_agent.py`
**Skills**: `starter_code/agent/prompts/data_retrieval_skills.md`
**Max Loops**: 10

**Responsibilities:**
- Efficiently query databases
- Correlate data across tables
- Extract relevant JSON fields
- Provide clean, structured data

**Expertise:**
- Time-based queries
- Hostname to device_id resolution
- Multi-device queries
- JSON extraction from model_output

**Tools Used**: All 8 tools

**Focus**: Data accuracy and presentation

#### 4. Analysis Agent
**File**: `starter_code/agent/agents/analysis_agent.py`
**Skills**: `starter_code/agent/prompts/analysis_skills.md`
**Max Loops**: 8

**Responsibilities:**
- Interpret telemetry patterns
- Identify anomalous behavior
- Correlate events temporally
- Recognize failure patterns

**Analysis Techniques:**
- Baseline comparison
- Pattern recognition
- Temporal correlation
- Event sequence reconstruction

**Tools Used**: 
- query_device_telemetry
- query_device_syslogs
- search_logs_by_keyword
- execute_custom_query

**Focus**: Insight extraction, not just data reporting

#### 5. Explanation Agent
**File**: `starter_code/agent/agents/explanation_agent.py`
**Skills**: `starter_code/agent/prompts/explanation_skills.md`
**Max Loops**: 3

**Responsibilities:**
- Explain networking concepts
- Provide educational content
- Answer "what is" / "how does" questions
- Contextualize network operations

**Topics Covered:**
- Network protocols (BGP, OSPF, BFD, LLDP)
- Network devices and roles
- Common failure modes
- Network metrics

**Tools Used**: 
- get_device_information (only for data-specific questions)
- execute_custom_query (only for network inventory)

**Focus**: Education and clarity, not database queries

## Code Organization

### Directory Structure

```
starter_code/
├── agent/
│   ├── __init__.py
│   ├── graph.py                    # Main orchestrator graph
│   ├── state.py                    # Shared state definition
│   ├── tools.py                    # All 8 tools
│   ├── agents/                     # Specialized agents
│   │   ├── __init__.py
│   │   ├── orchestrator_agent.py   # Request routing
│   │   ├── investigation_agent.py  # RCA specialist
│   │   ├── data_retrieval_agent.py # Database expert
│   │   ├── analysis_agent.py       # Pattern recognition
│   │   └── explanation_agent.py    # Networking expert
│   └── prompts/                    # Agent skills (markdown)
│       ├── orchestrator_skills.md
│       ├── investigation_skills.md
│       ├── data_retrieval_skills.md
│       ├── analysis_skills.md
│       └── explanation_skills.md
├── db_duckdb.py                    # Database adapter
├── api.py                          # FastAPI backend
└── main.py                         # CLI interface
```

### Why This Structure?

1. **Modular Agents**: Each agent is self-contained with its own file
2. **Separate Skills**: Prompts in markdown for easy editing without touching code
3. **Clear Separation**: Database, API, agents, and tools are independent modules
4. **Easy Testing**: Each component can be tested in isolation
5. **Maintainability**: Changes to one agent don't affect others

## Data Flow

### Investigation Request Flow

```
1. User → "investigate a1f0c8e2-..."
   ↓
2. Frontend → POST /chat
   ↓
3. FastAPI → build_graph().invoke()
   ↓
4. Orchestrator → Classifies as "investigation"
   ↓
5. Routes to Investigation Agent
   ↓
6. Investigation Agent:
   - Calls get_anomaly_details
   - Calls get_multiple_devices_info
   - Calls query_device_telemetry
   - Calls query_device_syslogs
   - Calls search_logs_by_keyword
   - Synthesizes findings
   ↓
7. Returns structured RCA
   ↓
8. FastAPI → Returns to frontend
   ↓
9. Frontend → Renders markdown RCA
```

### Tool Execution Flow

```
Agent Node → Invokes LLM with tools bound
↓
LLM decides which tools to call
↓
ToolNode executes tools sequentially
↓
Returns results to Agent Node
↓
Agent Node processes results
↓
LLM decides: more tools or final response
```

## Technology Stack

### Backend
- **LangGraph**: Agent orchestration and state management
- **LangChain**: LLM integration and tool calling
- **Claude Haiku 4.5**: Primary LLM (fast, cost-effective, strong reasoning)
- **DuckDB**: Embedded analytical database
- **FastAPI**: REST API framework
- **Pandas**: Data manipulation for CSV loading
- **Rich**: CLI formatting and markdown rendering

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool and dev server
- **Axios**: HTTP client
- **React Markdown**: Markdown rendering in chat

### Development
- **Python 3.11+**: Backend language
- **uv**: Fast Python package manager
- **Node.js 18+**: Frontend tooling

## Performance Characteristics

### Agent Loop Limits
- **Investigation**: 15 loops (comprehensive analysis)
- **Data Retrieval**: 10 loops (efficient queries)
- **Analysis**: 8 loops (focused interpretation)
- **Explanation**: 3 loops (minimal tool use)

### Database Performance
- **DuckDB**: In-memory analytical queries
- **CSV Loading**: One-time on initialization
- **Query Speed**: Sub-second for most queries
- **Dataset Size**: ~28K rows across 4 tables

### LLM Performance
- **Model**: Claude Haiku 4.5
- **Response Time**: 1-3 seconds per call
- **Token Efficiency**: Optimized prompts in skills files
- **Cost**: ~$0.001 per investigation (approximate)

## Security Considerations

### Input Validation
- SQL injection protection: Only SELECT queries allowed
- Parameter sanitization in all database queries
- Anomaly ID format validation
- Time range validation

### API Security
- CORS configured for development (update for production)
- No authentication (add JWT/OAuth for production)
- Rate limiting not implemented (add for production)
- API keys loaded from environment variables

### Data Privacy
- No PII in sample data
- Logs don't contain sensitive information
- Database file should be secured in production
- API keys never logged

## Scalability Path

### Current Scale
- Single-process, single-machine
- Suitable for: 1-10 concurrent users
- Database: Embedded (single file)

### Future Enhancements

#### Short Term
1. Add Redis for conversation state persistence
2. Implement API authentication
3. Add rate limiting
4. Deploy behind reverse proxy

#### Medium Term
1. Switch to PostgreSQL for production
2. Implement agent result caching
3. Add evaluation metrics and monitoring
4. Multi-tenant support

#### Long Term
1. Distributed agent execution
2. Horizontal scaling with load balancing
3. Real-time data ingestion
4. Multi-model support (ensemble decisions)

## Extension Points

### Adding a New Agent

1. Create `agents/new_agent.py`:
```python
def create_new_agent():
    # Agent implementation
    ...

def new_agent_node(state: AgentState) -> AgentState:
    # Node wrapper
    ...
```

2. Create `prompts/new_agent_skills.md`:
```markdown
# New Agent Skills
## Role
...
```

3. Update `orchestrator_agent.py`:
- Add classification logic
- Add routing case

4. Update `graph.py`:
- Import new agent
- Add node to graph
- Add routing edge

### Adding a New Tool

1. Add function to `tools.py`:
```python
@tool
def new_tool(param: str) -> str:
    """Tool description"""
    # Implementation
    ...
```

2. Add to relevant agent's tool list

3. Update skills markdown with usage guidance

## Testing Strategy

### Unit Tests
- Test each tool independently
- Test orchestrator classification logic
- Test database queries

### Integration Tests
- Test full investigation flow
- Test agent routing
- Test API endpoints

### End-to-End Tests
- CLI investigation scenarios
- Frontend interaction flows
- Multi-turn conversations

## Monitoring and Observability

### Current Logging
- Agent routing decisions
- Tool invocations
- Database queries
- API requests

### Future Monitoring
- LangSmith tracing
- Agent performance metrics
- Tool usage statistics
- Investigation success rates
- User satisfaction scores

## Known Limitations

1. **Context Window**: Long investigations may exceed context limits
2. **No Parallel Tools**: Tools execute sequentially
3. **Single Investigation**: Can't handle multiple anomalies simultaneously
4. **No Streaming**: Response only available after completion
5. **Static Data**: No real-time data ingestion

## Design Decisions Rationale

### Why DuckDB over PostgreSQL?
- Zero configuration for evaluation
- Excellent analytical query performance
- Easy to distribute (single file)
- Can migrate to PostgreSQL for production

### Why Multi-Agent over Single Agent?
- **Specialization**: Each agent optimized for its task
- **Maintainability**: Independent agent updates
- **Scalability**: Easier to add new capabilities
- **Performance**: Smaller context per agent
- **Testability**: Isolated unit testing

### Why Claude Haiku 4.5?
- **Speed**: Fast response times for interactive use
- **Cost**: Most cost-effective for production
- **Quality**: Strong reasoning for RCA tasks
- **Tool Calling**: Excellent function calling support

### Why Supervisor Pattern?
- **Simplicity**: Easy to understand and debug
- **Flexibility**: Can route based on complex logic
- **Efficiency**: Agents only invoked when needed
- **Transparency**: Clear audit trail of routing decisions

## Conclusion

This architecture provides a solid foundation for production network investigation with:
- ✅ Clear separation of concerns
- ✅ Modular, maintainable code
- ✅ Scalable design patterns
- ✅ Well-documented components
- ✅ Production-ready features
- ✅ Extension points for growth

The multi-agent design with skills-based prompts creates a flexible, powerful system that can evolve with changing requirements while maintaining code quality and operational reliability.

"""
FastAPI backend for the Network Investigation Agent.

Run from starter_code directory:
    cd starter_code
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Or from project root:
    uvicorn starter_code.main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import sys
import uuid
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

# Handle both running from starter_code/ and from project root
try:
    from agent.graph import build_graph
    from db_duckdb import get_all_anomalies, get_anomaly_by_id, list_tables
except ImportError:
    # Running from project root
    from starter_code.agent.graph import build_graph
    from starter_code.db_duckdb import get_all_anomalies, get_anomaly_by_id, list_tables

# Initialize FastAPI app
app = FastAPI(
    title="Network Investigation Agent API",
    description="Multi-Agent System for network anomaly root cause analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent graph
agent_app = None


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    global agent_app
    try:
        print("🚀 Initializing Network Investigation Agent...")
        agent_app = build_graph()
        print("✓ Multi-Agent System initialized successfully")
        print("  - Orchestrator Agent: Ready")
        print("  - Investigation Agent: Ready")
        print("  - Data Retrieval Agent: Ready")
        print("  - Analysis Agent: Ready")
        print("  - Explanation Agent: Ready")
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        print("Make sure you have set ANTHROPIC_API_KEY in .env file")


# Pydantic models for request/response
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    timestamp: str


class AnomalyListResponse(BaseModel):
    anomalies: list[dict]
    count: int


class AnomalyDetailResponse(BaseModel):
    anomaly: dict


class HealthResponse(BaseModel):
    status: str
    agent_ready: bool
    database_ready: bool
    agents: dict


# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health check"""
    db_ready = False
    try:
        tables = list_tables()
        db_ready = len(tables) > 0
    except:
        pass
    
    return {
        "status": "online",
        "agent_ready": agent_app is not None,
        "database_ready": db_ready,
        "agents": {
            "orchestrator": "active",
            "investigation": "active",
            "data_retrieval": "active",
            "analysis": "active",
            "explanation": "active"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check"""
    db_ready = False
    try:
        tables = list_tables()
        db_ready = len(tables) == 4
    except:
        pass
    
    return {
        "status": "online",
        "agent_ready": agent_app is not None,
        "database_ready": db_ready,
        "agents": {
            "orchestrator": "active" if agent_app else "inactive",
            "investigation": "active" if agent_app else "inactive",
            "data_retrieval": "active" if agent_app else "inactive",
            "analysis": "active" if agent_app else "inactive",
            "explanation": "active" if agent_app else "inactive"
        }
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the agent.
    
    The orchestrator routes requests to specialized agents:
    - Investigation queries → Investigation Agent
    - Data queries → Data Retrieval Agent
    - Analysis requests → Analysis Agent
    - Explanation questions → Explanation Agent
    
    Maintains conversation context using thread_id.
    """
    if agent_app is None:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check ANTHROPIC_API_KEY in .env")
    
    # Generate thread_id if not provided
    thread_id = request.thread_id or str(uuid.uuid4())
    
    try:
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "current_anomaly_id": None,
            "current_investigation": None,
            "loop_count": 0,
            "max_loops": 15,
        }
        
        # Run the agent
        config = {"configurable": {"thread_id": thread_id}}
        result = agent_app.invoke(initial_state, config)
        
        # Extract the response
        messages = result.get("messages", [])
        response_text = "No response generated."
        
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                response_text = message.content
                break
        
        return {
            "response": response_text,
            "thread_id": thread_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/anomalies", response_model=AnomalyListResponse)
async def list_anomalies():
    """
    List all detected anomalies.
    
    Returns a simplified view of all anomalies for display.
    """
    try:
        import json
        anomalies = get_all_anomalies()
        
        # Simplify for display
        simplified = []
        for anomaly in anomalies:
            model_output = anomaly.get('model_output', {})
            
            # Parse JSON if it's a string
            if isinstance(model_output, str):
                model_output = json.loads(model_output)
            
            simplified.append({
                "anomaly_id": anomaly['anomaly_id'],
                "date": str(anomaly['anomaly_date']),
                "severity": anomaly['severity'],
                "detector": model_output.get('detector', 'unknown'),
                "impacted_hosts": model_output.get('impacted_hostnames', []),
                "host_count": model_output.get('host_count', 0),
                "criticality": model_output.get('criticality', 'unknown')
            })
        
        return {
            "anomalies": simplified,
            "count": len(simplified)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/anomalies/{anomaly_id}", response_model=AnomalyDetailResponse)
async def get_anomaly(anomaly_id: str):
    """
    Get detailed information about a specific anomaly.
    """
    try:
        anomaly = get_anomaly_by_id(anomaly_id)
        
        if not anomaly:
            raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")
        
        return {
            "anomaly": anomaly
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/investigate/{anomaly_id}", response_model=ChatResponse)
async def investigate_anomaly(anomaly_id: str, thread_id: Optional[str] = None):
    """
    Start an investigation for a specific anomaly.
    
    This is a convenience endpoint that creates a chat message to investigate
    the given anomaly ID. Routes to Investigation Agent via Orchestrator.
    """
    if agent_app is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    # Verify the anomaly exists
    try:
        anomaly = get_anomaly_by_id(anomaly_id)
        if not anomaly:
            raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Create investigation message
    message = f"Investigate anomaly {anomaly_id}"
    
    # Use the chat endpoint logic
    request = ChatRequest(message=message, thread_id=thread_id)
    return await chat(request)


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", "8000"))
    
    print(f"""

 Network Investigation Agent - Multi-Agent System API            
                                                                 
 Server running at: http://localhost:{port}                        
 API Docs: http://localhost:{port}/docs                            
 Health Check: http://localhost:{port}/health                      
                                                                 
 Agents:                                                         
   • Orchestrator Agent (request routing)                        
    • Investigation Agent (comprehensive RCA)                     
   • Data Retrieval Agent (database queries)                     
    • Analysis Agent (pattern interpretation)                     
   • Explanation Agent (networking expertise)                    

    """)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

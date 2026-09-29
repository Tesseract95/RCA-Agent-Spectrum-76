"""
Orchestrator Agent - Routes requests to specialized agents
"""
from typing import Literal
from pathlib import Path

from langchain_core.messages import HumanMessage
from .tools import list_all_anomalies


def load_skills(agent_name: str) -> str:
    """Load skills from markdown file"""
    skills_path = Path(__file__).parent / "prompts" / f"{agent_name}_skills.md"
    with open(skills_path, 'r') as f:
        return f.read()


def extract_anomaly_id(text: str) -> str | None:
    """Extract anomaly ID from text"""
    import re
    pattern = r'a1f0c8e2-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9]{12}'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else None


def classify_request(message: str, current_anomaly_id: str | None) -> Literal[
    "investigation", "data_retrieval", "analysis", "explanation", "list_anomalies"
]:
    """
    Classify the user's request to route to the appropriate agent.
    """
    message_lower = message.lower()
    
    # Check for investigation keywords
    if any(keyword in message_lower for keyword in ["investigate", "rca", "root cause"]):
        return "investigation"
    
    # Check for list anomalies
    if any(keyword in message_lower for keyword in ["list anomalies", "show anomalies", "all anomalies"]):
        return "list_anomalies"
    
    # Check for explanation keywords
    if any(keyword in message_lower for keyword in ["what is", "explain", "how does", "what does", "define"]):
        # But if it's about current investigation, route to analysis
        if current_anomaly_id and any(word in message_lower for word in ["this", "that", "the issue", "the problem"]):
            return "analysis"
        return "explanation"
    
    # Check for data retrieval keywords
    if any(keyword in message_lower for keyword in ["get", "show", "fetch", "retrieve", "query", "device", "telemetry", "logs"]):
        return "data_retrieval"
    
    # Check for analysis keywords
    if any(keyword in message_lower for keyword in ["analyze", "pattern", "spike", "correlation", "trend", "why", "caused"]):
        return "analysis"
    
    # If we have an active investigation and this is a follow-up, route to analysis
    if current_anomaly_id:
        return "analysis"
    
    # Default to explanation for general questions
    return "explanation"


def orchestrator_node(state: dict) -> dict:
    """
    Orchestrator node that classifies requests and routes to specialized agents.
    """
    messages = state["messages"]
    current_anomaly_id = state.get("current_anomaly_id")
    
    if not messages:
        return state
    
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return state
    
    user_message = last_message.content
    
    # Extract anomaly ID if present
    extracted_id = extract_anomaly_id(user_message)
    if extracted_id:
        current_anomaly_id = extracted_id
    
    # Classify the request
    request_type = classify_request(user_message, current_anomaly_id)
    
    # Store the routing decision
    return {
        "current_anomaly_id": current_anomaly_id,
        "agent_route": request_type,
        "loop_count": 0,
    }


def route_to_agent(state: dict) -> Literal[
    "investigation_agent", "data_retrieval_agent", "analysis_agent", 
    "explanation_agent", "list_anomalies_handler", "end"
]:
    """
    Route to the appropriate specialized agent based on classification.
    """
    route = state.get("agent_route", "explanation")
    
    if route == "investigation":
        return "investigation_agent"
    elif route == "data_retrieval":
        return "data_retrieval_agent"
    elif route == "analysis":
        return "analysis_agent"
    elif route == "explanation":
        return "explanation_agent"
    elif route == "list_anomalies":
        return "list_anomalies_handler"
    else:
        return "end"


def list_anomalies_handler_node(state: dict) -> dict:
    """
    Simple handler for listing anomalies.
    """
    from langchain_core.messages import AIMessage
    
    # Call the tool using invoke method (not deprecated __call__)
    result = list_all_anomalies.invoke({})
    
    # Create a response message
    response = f"Here are all the detected anomalies:\n\n{result}\n\nClick on any anomaly ID to investigate it, or ask me to investigate a specific one."
    
    return {
        "messages": [AIMessage(content=response)]
    }

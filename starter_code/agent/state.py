"""
State management for the Multi-Agent Network Investigation System.
Defines the agent state structure and typing.
"""
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    State for the Multi-Agent Network Investigation System.
    
    The orchestrator maintains conversational history and routes to specialized agents.
    Each specialized agent maintains its own sub-state during execution.
    """
    # Conversational messages with add_messages reducer
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Current investigation context
    current_anomaly_id: str | None
    current_investigation: dict | None
    
    # Routing information
    agent_route: str | None
    
    # Agent metadata
    loop_count: int
    max_loops: int

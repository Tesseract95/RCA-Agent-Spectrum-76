"""
Multi-Agent Network Investigation System with Orchestrator.

This system uses specialized agents coordinated by an orchestrator:
- Orchestrator: Routes requests to appropriate specialized agents
- Investigation Agent: Performs deep RCA on anomalies
- Data Retrieval Agent: Queries and correlates data sources
- Analysis Agent: Interprets telemetry and log patterns
- Explanation Agent: Provides networking expertise

Architecture: Supervisor pattern with specialized sub-agents
Each agent has:
- Dedicated Python module in agents/
- Skills defined in prompts/*.md files
- Specific tool access and expertise
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .orchestrator_agent import orchestrator_node, route_to_agent, list_anomalies_handler_node
from .investigation_agent import investigation_agent_node
from .data_retrieval_agent import data_retrieval_agent_node
from .analysis_agent import analysis_agent_node
from .explanation_agent import explanation_agent_node


def build_graph():
    """
    Build and compile the Multi-Agent Network Investigation System.
    
    Architecture:
    - Orchestrator routes requests to specialized agents
    - Each agent has specific expertise and tools
    - Conversation memory maintained across interactions
    
    Agents:
    - Orchestrator: Request classification and routing
    - Investigation: Comprehensive RCA with structured methodology
    - Data Retrieval: Efficient database queries and correlation
    - Analysis: Pattern recognition and event correlation
    - Explanation: Networking concepts and education
    
    Returns:
        Compiled LangGraph application with checkpointer for conversation memory
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add orchestrator
    workflow.add_node("orchestrator", orchestrator_node)
    
    # Add specialized agents
    workflow.add_node("investigation_agent", investigation_agent_node)
    workflow.add_node("data_retrieval_agent", data_retrieval_agent_node)
    workflow.add_node("analysis_agent", analysis_agent_node)
    workflow.add_node("explanation_agent", explanation_agent_node)
    workflow.add_node("list_anomalies_handler", list_anomalies_handler_node)
    
    # Set entry point
    workflow.set_entry_point("orchestrator")
    
    # Add routing from orchestrator to specialized agents
    workflow.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "investigation_agent": "investigation_agent",
            "data_retrieval_agent": "data_retrieval_agent",
            "analysis_agent": "analysis_agent",
            "explanation_agent": "explanation_agent",
            "list_anomalies_handler": "list_anomalies_handler",
            "end": END,
        }
    )
    
    # All agents end after completion
    workflow.add_edge("investigation_agent", END)
    workflow.add_edge("data_retrieval_agent", END)
    workflow.add_edge("analysis_agent", END)
    workflow.add_edge("explanation_agent", END)
    workflow.add_edge("list_anomalies_handler", END)
    
    # Add memory checkpointer for conversation history
    memory = MemorySaver()
    
    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    
    return app


def run_agent(user_input: str, thread_id: str = "default") -> str:
    """
    Helper function to run the agent with a single input.
    
    Args:
        user_input: The user's question or command
        thread_id: Thread ID for conversation continuity (default: "default")
    
    Returns:
        The agent's response as a string
    """
    app = build_graph()
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "current_anomaly_id": None,
        "current_investigation": None,
        "loop_count": 0,
        "max_loops": 15,
    }
    
    # Run the graph
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(initial_state, config)
    
    # Extract the last AI message
    messages = result.get("messages", [])
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message.content
    
    return "No response generated."


if __name__ == "__main__":
    # Test the agent
    print("Building Network Investigation Agent...")
    app = build_graph()
    print("Agent built successfully!")
    print("\nTesting with sample query...")
    
    response = run_agent("List all anomalies")
    print("\nAgent response:")
    print(response)

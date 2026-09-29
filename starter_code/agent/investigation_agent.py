"""
Investigation Agent - Performs comprehensive RCA on anomalies
"""
import os
from typing import Literal
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .tools import (
    get_anomaly_details,
    get_device_information,
    get_multiple_devices_info,
    query_device_telemetry,
    query_device_syslogs,
    search_logs_by_keyword,
    execute_custom_query,
)

load_dotenv()


def load_skills() -> str:
    """Load investigation agent skills from markdown file"""
    skills_path = Path(__file__).parent / "prompts" / "investigation_skills.md"
    with open(skills_path, 'r') as f:
        return f.read()


def get_llm():
    """Get the configured LLM"""
    if os.getenv("ANTHROPIC_API_KEY"):
        return ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.1)
    elif os.getenv("GOOGLE_API_KEY"):
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)
    elif os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    else:
        raise ValueError("No LLM API key found in .env")


def create_investigation_agent():
    """Create the Investigation Agent graph"""
    tools = [
        get_anomaly_details,
        get_device_information,
        get_multiple_devices_info,
        query_device_telemetry,
        query_device_syslogs,
        search_logs_by_keyword,
        execute_custom_query,
    ]
    
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)
    skills = load_skills()
    
    def agent_node(state: AgentState):
        messages = state["messages"]
        system_msg = SystemMessage(content=skills)
        llm_messages = [system_msg] + list(messages)
        response = llm_with_tools.invoke(llm_messages)
        
        return {
            "messages": [response],
            "loop_count": state.get("loop_count", 0) + 1,
        }
    
    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        messages = state["messages"]
        last_message = messages[-1]
        
        if state.get("loop_count", 0) >= 15:
            return "end"
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        return "end"
    
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


def investigation_agent_node(state: AgentState) -> AgentState:
    """
    Run the Investigation Agent and update investigation context.
    """
    investigation_agent = create_investigation_agent()
    result = investigation_agent.invoke(state)
    
    # Store investigation context
    messages = result.get("messages", [])
    investigation_summary = ""
    
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            if "Root Cause Analysis" in msg.content:
                investigation_summary = msg.content[:200] + "..."
                break
    
    return {
        "messages": result.get("messages", []),
        "current_investigation": {
            "summary": investigation_summary,
            "full_analysis": messages[-1].content if messages else ""
        }
    }

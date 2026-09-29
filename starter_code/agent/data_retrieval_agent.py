"""
Data Retrieval Agent - Efficiently queries database and provides structured data
"""
import os
from typing import Literal
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
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
    """Load data retrieval agent skills from markdown file"""
    skills_path = Path(__file__).parent / "prompts" / "data_retrieval_skills.md"
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


def create_data_retrieval_agent():
    """Create the Data Retrieval Agent graph"""
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
        
        if state.get("loop_count", 0) >= 10:
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


def data_retrieval_agent_node(state: AgentState) -> AgentState:
    """
    Run the Data Retrieval Agent.
    """
    data_agent = create_data_retrieval_agent()
    result = data_agent.invoke(state)
    return {"messages": result.get("messages", [])}

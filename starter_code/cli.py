"""
Interactive CLI for the Network Investigation Agent.

Run from starter_code directory:
    cd starter_code
    python cli.py

Or from project root:
    python -m starter_code.cli
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from langchain_core.messages import HumanMessage

# Handle both running from starter_code/ and from project root
try:
    from agent.graph import build_graph
except ImportError:
    from starter_code.agent.graph import build_graph

console = Console()


def print_welcome():
    """Print welcome message with instructions"""
    welcome_text = """
# Network Investigation Agent - CLI

I'm an AI agent specialized in network root cause analysis using a multi-agent system.

**What I can do:**
- Investigate anomalies by ID (e.g., 'a1f0c8e2-1b44-4d90-9c31-000000000001')
- List all available anomalies
- Answer follow-up questions about investigations
- Provide general networking expertise

**Example queries:**
- "investigate a1f0c8e2-1b44-4d90-9c31-000000000001"
- "list all anomalies"
- "what caused this issue?"
- "explain BGP session failures"

**Active Agents:**
- 🎯 Orchestrator (routes your requests)
- 🔍 Investigation (performs RCA)
- 📊 Data Retrieval (queries database)
- 📈 Analysis (interprets patterns)
- 💡 Explanation (networking knowledge)

Type 'exit' or 'quit' to quit.
    """
    console.print(Markdown(welcome_text))
    console.print()


def main():
    """Main CLI loop"""
    print_welcome()
    
    # Build the agent graph
    try:
        console.print("[yellow]Initializing multi-agent system...[/yellow]")
        app = build_graph()
        console.print("[green]✓ All agents ready![/green]\n")
    except Exception as e:
        console.print(f"[red]Error initializing agents: {e}[/red]")
        console.print("[yellow]Make sure you have set ANTHROPIC_API_KEY in .env file[/yellow]")
        sys.exit(1)
    
    # Use a consistent thread_id for conversation continuity
    thread_id = "cli-session"
    config = {"configurable": {"thread_id": thread_id}}
    
    console.print("[dim]Tip: Conversation history is maintained throughout this session[/dim]\n")
    
    while True:
        try:
            # Get user input
            user_input = console.input("[bold cyan]> [/bold cyan]").strip()
            
            # Check for exit commands
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Show thinking indicator
            console.print()
            with console.status("[bold green]Agents working...", spinner="dots"):
                # Create initial state
                initial_state = {
                    "messages": [HumanMessage(content=user_input)],
                    "current_anomaly_id": None,
                    "current_investigation": None,
                    "agent_route": None,
                    "loop_count": 0,
                    "max_loops": 15,
                }
                
                # Invoke the agent
                result = app.invoke(initial_state, config)
            
            # Extract and display the response
            messages = result.get("messages", [])
            
            # Get the last AI message
            response_text = None
            for message in reversed(messages):
                if hasattr(message, 'content') and message.content:
                    # Skip tool messages
                    if not hasattr(message, 'tool_calls'):
                        response_text = message.content
                        break
            
            if response_text:
                # Show which agent handled the request
                agent_route = result.get("agent_route", "unknown")
                agent_name = {
                    "investigation": "🔍 Investigation Agent",
                    "data_retrieval": "📊 Data Retrieval Agent",
                    "analysis": "📈 Analysis Agent",
                    "explanation": "💡 Explanation Agent",
                    "list_anomalies": "📋 Orchestrator"
                }.get(agent_route, "🤖 Agent")
                
                # Display the response in a nice panel
                console.print(Panel(
                    Markdown(response_text),
                    title=f"[bold blue]{agent_name}[/bold blue]",
                    border_style="blue"
                ))
            else:
                console.print("[yellow]No response generated.[/yellow]")
            
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]\n")
            continue
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]\n")
            continue


if __name__ == "__main__":
    main()

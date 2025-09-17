#!/usr/bin/env python3
"""
CLI Super-Agent Chat with Oracle JDBC (jaydebeapi) Example Tool

Requirements (tested with):
- python 3.10+
- langchain==0.3.27
- langgraph>=0.2.38
- rich>=13.7
- typer>=0.12
- jaydebeapi>=1.2.3

Usage:
  export OPENAI_API_KEY=...
  export ORACLE_JDBC_JAR=/path/to/ojdbc8.jar
  export ORACLE_URL=jdbc:oracle:thin:@//host:1521/service
  export ORACLE_USER=myuser
  export ORACLE_PASSWORD=mypassword
  python cli_super_agent.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.markdown import Markdown

# --- LangChain / LangGraph imports ---
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from secret.secret_util import get_config

# get all secret and config params from config
config = get_config()

# ----------------------- Config -----------------------------------
DEFAULT_MODEL = "gpt-4.1-mini"
REASONING_EFFORT = "medium"

app = typer.Typer(add_completion=False)
console = Console()

# ----------------------- Demo Tools --------------------------------
@tool("math.add")
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b

@tool("string.echo")
def echo(text: str) -> str:
    """Echo the provided text."""
    return text

@tool("data.lookup_user")
def lookup_user(username: str) -> Dict[str, Any]:
    """Fake user directory lookup."""
    users = {
        "wei": {"name": "Wei Zhang", "role": "Product Manager", "city": "New York"},
        "lucas": {"name": "Lucas", "role": "VIP", "city": "New York"},
    }
    return users.get(username.lower(), {"error": "user not found"})

# Oracle JDBC connection tool using jaydebeapi
@tool("oracle.query")
def oracle_query(sql: str) -> List[Dict[str, Any]]:
    """Run a SQL query against Oracle DB via JDBC (jaydebeapi)."""
    import jaydebeapi
    jdbc_jar = config['oracle']["JDBC_JAR"]
    url = config['oracle']["JDBC_URL"]
    user = config['oracle']["USERNAME"]
    password = config['oracle']["PASSWORD"]
    if not all([jdbc_jar, url, user, password]):
        return [{"error": "Set ORACLE_JDBC_JAR, ORACLE_URL, ORACLE_USER, ORACLE_PASSWORD env vars"}]
    try:
        conn = jaydebeapi.connect(
            "oracle.jdbc.OracleDriver",
            url,
            [user, password],
            jdbc_jar,
        )
        curs = conn.cursor()
        curs.execute(sql)
        cols = [d[0] for d in curs.description]
        rows = [dict(zip(cols, r)) for r in curs.fetchall()]
        curs.close()
        conn.close()
        return rows
    except Exception as e:
        return [{"error": str(e)}]

TOOLS = [add, echo, lookup_user, oracle_query]

# ----------------------- State ------------------------------------
@dataclass
class AgentState:
    input: str
    history: List[Dict[str, Any]] = field(default_factory=list)
    route: Optional[str] = None
    result: Optional[str] = None
    interrupt_policy: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# ----------------------- LLM Factory -------------------------------

def make_llm(model: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or DEFAULT_MODEL,
        temperature=0.2,
        reasoning_effort=REASONING_EFFORT,
    )

# ----------------------- Supervisor -------------------------------

def supervisor_router(state: AgentState) -> Literal["policy", "calc", "general", "oracle"]:
    text = state.input.lower()
    if any(k in text for k in ["sum", "add", "+", "calculate", "math"]):
        return "calc"
    if any(k in text for k in ["policy", "access", "entitlement", "ontology", "neo4j", "fibo"]):
        return "policy"
    if "oracle" in text or "sql" in text:
        return "oracle"
    return "general"

INTERRUPT_TABLE = {"policy": "hard", "calc": "soft", "oracle": "hard", "general": None}

# ----------------------- Agents -----------------------------------

def build_policy_agent(model: Optional[str] = None):
    llm = make_llm(model)
    return create_react_agent(llm, tools=[], state_schema=AgentState)


def build_calc_agent(model: Optional[str] = None):
    llm = make_llm(model)
    return create_react_agent(llm, tools=[add], state_schema=AgentState)


def build_general_agent(model: Optional[str] = None):
    llm = make_llm(model)
    return create_react_agent(llm, tools=[echo, lookup_user], state_schema=AgentState)


def build_oracle_agent(model: Optional[str] = None):
    llm = make_llm(model)
    return create_react_agent(llm, tools=[oracle_query], state_schema=AgentState)

# ----------------------- Graph Wiring ------------------------------

def build_graph(model: Optional[str] = None):
    policy_agent = build_policy_agent(model)
    calc_agent = build_calc_agent(model)
    general_agent = build_general_agent(model)
    oracle_agent = build_oracle_agent(model)

    def route_node(state: AgentState) -> str:
        route = supervisor_router(state)
        state.route = route
        state.interrupt_policy = INTERRUPT_TABLE.get(route)
        return route

    graph = StateGraph(AgentState)
    graph.add_node("policy", lambda s: policy_agent.invoke(s))
    graph.add_node("calc", lambda s: calc_agent.invoke(s))
    graph.add_node("general", lambda s: general_agent.invoke(s))
    graph.add_node("oracle", lambda s: oracle_agent.invoke(s))

    graph.add_conditional_edges("policy", lambda s: END)
    graph.add_conditional_edges("calc", lambda s: END)
    graph.add_conditional_edges("general", lambda s: END)
    graph.add_conditional_edges("oracle", lambda s: END)

    graph.set_entry_point(route_node)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)

# ----------------------- Interrupt Handling ------------------------

def maybe_interrupt(state: AgentState, auto: bool) -> bool:
    policy = state.interrupt_policy
    if policy is None:
        return True
    if auto and policy == "soft":
        return True
    title = {"hard": "🚦 Confirmation Required", "soft": "⚠️  Proceed?"}.get(policy, "Proceed?")
    msg = f"Route: {state.route}\nPolicy: {policy}\n\nAbout to execute:\n{state.input}\n"
    console.print(Panel.fit(Markdown(msg), title=title))
    ok = Confirm.ask("Do you want to continue?", default=(policy != "hard"))
    return bool(ok)

# ----------------------- CLI Runner --------------------------------

@app.command()
def chat(
    auto: bool = typer.Option(False, help="Run without human interrupts for soft flows."),
    model: Optional[str] = typer.Option(None, help="LLM model name (override)."),
    transcript: Optional[str] = typer.Option(None, help="Append transcript to file."),
):
    graph = build_graph(model=model)

    console.rule("[bold cyan]Super-Agent CLI Chat")
    console.print("Type 'exit' or 'quit' to leave.\n")

    history: List[Dict[str, Any]] = []

    def log(line: str):
        if transcript:
            with open(transcript, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    while True:
        try:
            user = console.input("[bold green]you › [/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nbye! 👋")
            break
        if user.lower() in {"exit", "quit"}:
            console.print("bye! 👋")
            break

        state = AgentState(input=user, history=history)
        route = supervisor_router(state)
        state.route = route
        state.interrupt_policy = INTERRUPT_TABLE.get(route)

        if not maybe_interrupt(state, auto=auto):
            console.print("[yellow]Aborted.[/yellow]")
            log(f"**You:** {user}\n**Aborted**\n")
            continue

        final = graph.invoke(state)
        console.print(Panel.fit(Markdown(final.result or "(no result)"), title=f"{route} agent"))

        turn = {"user": user, "route": route, "result": final.result}
        history.append(turn)

        if transcript:
            log(f"**You:** {user}")
            log(f"**{route} agent:** {final.result}\n")


if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        console = Console()
        console.print(f"[red]Fatal error:[/red] {e}")
        sys.exit(1)

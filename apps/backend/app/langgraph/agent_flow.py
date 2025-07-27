from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from app.agents.builder import BuilderAgent
from app.agents.strategist import StrategistAgent
from app.agents.scout import ScoutAgent
from app.tools.message import Message
from app.env.grid import Grid
from typing import TypedDict, Annotated

# Define the state schema
class AgentState(TypedDict):
    grid: Grid
    messages: list[Message]

# Define agent steps
def scout_step(state: AgentState) -> AgentState:
    scout = ScoutAgent("scout", state["grid"])
    msg = scout.step(state["messages"])
    new_messages = state["messages"] + [msg] if msg else state["messages"]
    return {"grid": state["grid"], "messages": new_messages}

def strategist_step(state: AgentState) -> AgentState:
    strategist = StrategistAgent("strategist", state["grid"])
    msg = strategist.step(state["messages"])
    new_messages = state["messages"] + [msg] if msg else state["messages"]
    return {"grid": state["grid"], "messages": new_messages}

def builder_step(state: AgentState) -> AgentState:
    builder = BuilderAgent("builder", state["grid"])
    msg = builder.step(state["messages"])
    new_messages = state["messages"] + [msg] if msg else state["messages"]
    return {"grid": state["grid"], "messages": new_messages}

# Build the LangGraph flow
def build_agent_flow():
    graph = StateGraph(AgentState)
    graph.add_node("scout", scout_step)
    graph.add_node("strategist", strategist_step)
    graph.add_node("builder", builder_step)

    # Define execution flow
    graph.set_entry_point("scout")
    graph.add_edge("scout", "strategist")
    graph.add_edge("strategist", "builder")
    graph.add_edge("builder", END)

    # Add optional memory saver (future expansion)
    memory = SqliteSaver("agent_flow.db")
    app = graph.compile()
    return app
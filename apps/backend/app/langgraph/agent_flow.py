from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from app.agents.builder import BuilderAgent
from app.agents.strategist import StrategistAgent
from app.agents.scout import ScoutAgent
from app.tools.message import Message
from app.env.grid import Grid
from typing import TypedDict, Annotated, List

# Define the state schema
class AgentState(TypedDict):
    grid: Grid
    messages: List[Message]
    step_count: int
    objectives: List[str]
    exploration_progress: float
    buildings_built: int

# Create agent instances (will be replaced by actual instances)
scout_agent = None
strategist_agent = None  
builder_agent = None

def initialize_agents(grid: Grid):
    """Initialize agent instances with the grid"""
    global scout_agent, strategist_agent, builder_agent
    scout_agent = ScoutAgent("scout", grid)
    strategist_agent = StrategistAgent("strategist", grid)
    builder_agent = BuilderAgent("builder", grid)

# Define agent steps - each agent acts only once per step
def scout_step(state: AgentState) -> AgentState:
    """Scout explores and reports findings"""
    if scout_agent is None:
        initialize_agents(state["grid"])
    
    # Scout acts based on current messages
    result_message = scout_agent.step(state["messages"])
    
    # Add scout's message to the state
    new_messages = state["messages"].copy()
    if result_message:
        new_messages.append(result_message)
    
    return {
        **state,
        "messages": new_messages
    }

def strategist_step(state: AgentState) -> AgentState:
    """Strategist analyzes and plans"""
    if strategist_agent is None:
        initialize_agents(state["grid"])
    
    # Strategist acts based on current messages (including scout reports)
    result_message = strategist_agent.step(state["messages"])
    
    # Add strategist's message to the state  
    new_messages = state["messages"].copy()
    if result_message:
        new_messages.append(result_message)
    
    return {
        **state,
        "messages": new_messages
    }

def builder_step(state: AgentState) -> AgentState:
    """Builder constructs based on strategist orders"""
    if builder_agent is None:
        initialize_agents(state["grid"])
    
    # Builder acts based on current messages (including strategist orders)
    result_message = builder_agent.step(state["messages"])
    
    # Add builder's message to the state
    new_messages = state["messages"].copy()
    if result_message:
        new_messages.append(result_message)
    
    return {
        **state,
        "messages": new_messages
    }

# Build the LangGraph flow with proper sequencing
def build_agent_flow():
    """Build the agent coordination flow"""
    graph = StateGraph(AgentState)
    
    # Add nodes for each agent
    graph.add_node("scout", scout_step)
    graph.add_node("strategist", strategist_step)
    graph.add_node("builder", builder_step)

    # Define execution flow: Scout -> Strategist -> Builder -> END
    graph.set_entry_point("scout")
    graph.add_edge("scout", "strategist")
    graph.add_edge("strategist", "builder")
    graph.add_edge("builder", END)

    # Compile the graph
    app = graph.compile()
    return app
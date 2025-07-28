from langgraph.graph import StateGraph, END
from app.agents.builder import BuilderAgent
from app.agents.strategist import StrategistAgent
from app.agents.scout import ScoutAgent
from app.tools.message import Message
from app.env.grid import Grid
from typing import TypedDict, List, Literal, Dict
import logging

logger = logging.getLogger(__name__)

# Enhanced state schema with conditional logic
class AgentState(TypedDict):
    grid: Grid
    messages: List[Message]
    step_count: int
    mission_phase: Literal["initialization", "exploration", "analysis", "construction", "optimization", "completion"]
    objectives: List[str]
    exploration_progress: float
    buildings_built: int
    active_threats: int
    resource_constraints: bool
    coordination_needed: bool
    emergency_mode: bool
    last_activity: Dict[str, str]  # agent_id -> last_action_type
    strategic_plan_ready: bool

# Global agent instances
scout_agent = None
strategist_agent = None  
builder_agent = None

def initialize_agents(grid: Grid):
    """Initialize agent instances with the grid"""
    global scout_agent, strategist_agent, builder_agent
    scout_agent = ScoutAgent("scout", grid)
    strategist_agent = StrategistAgent("strategist", grid)
    builder_agent = BuilderAgent("builder", grid)
    logger.info("Agents initialized for simplified conditional flow")

def execute_single_step(state: AgentState) -> AgentState:
    """Execute a single step with conditional agent selection"""
    if scout_agent is None:
        initialize_agents(state["grid"])
    
    logger.info(f"Executing step {state['step_count']} - Phase: {state['mission_phase']}")
    
    new_messages = state["messages"].copy()
    
    # Determine which agent should act based on current phase and conditions
    active_agent = determine_active_agent(state)
    
    if state["emergency_mode"]:
        logger.warning("Emergency mode - all agents coordinate")
        # Emergency: all agents act
        for agent in [scout_agent, strategist_agent, builder_agent]:
            if agent:
                result = agent.step(new_messages)
                if result:
                    new_messages.append(result)
        state["last_activity"]["scout"] = "emergency"
        state["last_activity"]["strategist"] = "emergency"
        state["last_activity"]["builder"] = "emergency"
        state["emergency_mode"] = False  # Reset after handling
        
    elif state["coordination_needed"]:
        logger.info("Coordination mode - agents collaborate")
        # Coordination: agents work together
        scout_result = scout_agent.step(new_messages)
        if scout_result:
            new_messages.append(scout_result)
            
        strategist_result = strategist_agent.step(new_messages)
        if strategist_result:
            new_messages.append(strategist_result)
            
        builder_result = builder_agent.step(new_messages)
        if builder_result:
            new_messages.append(builder_result)
            
        state["last_activity"]["scout"] = "coordination"
        state["last_activity"]["strategist"] = "coordination"
        state["last_activity"]["builder"] = "coordination"
        state["coordination_needed"] = False  # Reset after coordination
        
    else:
        # Normal mode: single agent acts based on phase
        if active_agent == "scout":
            result = scout_agent.step(new_messages)
            if result:
                new_messages.append(result)
            state["last_activity"]["scout"] = "exploration"
            
        elif active_agent == "strategist":
            result = strategist_agent.step(new_messages)
            if result:
                new_messages.append(result)
                # Check if strategic plan is ready
                if "STRATEGIC_BUILD_ORDER" in result.content:
                    state["strategic_plan_ready"] = True
            state["last_activity"]["strategist"] = "analysis"
            
        elif active_agent == "builder":
            result = builder_agent.step(new_messages)
            if result:
                new_messages.append(result)
            state["last_activity"]["builder"] = "construction"
    
    # Update mission phase based on progress
    update_mission_phase(state)
    
    # Update exploration and building metrics
    state["exploration_progress"] = _calculate_exploration_progress(state["grid"])
    state["buildings_built"] = _count_buildings(state["grid"])
    
    # Trigger coordination periodically to prevent agents from working in isolation
    if state["step_count"] % 5 == 0:  # Every 5 steps
        state["coordination_needed"] = True
        logger.info("Triggering coordination due to step count")
    
    return {
        **state,
        "messages": new_messages
    }

def determine_active_agent(state: AgentState) -> str:
    """Determine which agent should be active based on mission phase and conditions"""
    phase = state["mission_phase"]
    exploration = state["exploration_progress"]
    buildings = state["buildings_built"]
    
    logger.info(f"Determining active agent: phase={phase}, exploration={exploration:.1%}, buildings={buildings}")
    
    # Emergency conditions
    if state["emergency_mode"]:
        return "all"  # Will be handled specially
    
    # Coordination conditions
    if state["coordination_needed"]:
        return "all"  # Will be handled specially
    
    # Phase-based agent selection with clear priorities
    if phase in ["initialization", "exploration"] or exploration < 0.6:
        logger.info("Selecting scout for exploration")
        return "scout"
    elif phase == "analysis" or (exploration >= 0.6 and not state["strategic_plan_ready"]):
        logger.info("Selecting strategist for analysis")
        return "strategist"
    elif phase == "construction" or (state["strategic_plan_ready"] and buildings < 5):
        logger.info("Selecting builder for construction")
        return "builder"
    else:
        # Default to scout if uncertain
        logger.info("Defaulting to scout")
        return "scout"

def update_mission_phase(state: AgentState):
    """Update mission phase based on current conditions"""
    current_phase = state["mission_phase"]
    exploration = state["exploration_progress"]
    buildings = state["buildings_built"]
    
    new_phase = current_phase
    
    if current_phase == "initialization" and state["step_count"] >= 2:
        new_phase = "exploration"
    elif current_phase == "exploration" and exploration >= 0.6:
        new_phase = "analysis"
    elif current_phase == "analysis" and state["strategic_plan_ready"]:
        new_phase = "construction"
    elif current_phase == "construction" and buildings >= 5:
        new_phase = "completion"
    
    if new_phase != current_phase:
        logger.info(f"Phase transition: {current_phase} → {new_phase}")
        state["mission_phase"] = new_phase

def build_agent_flow():
    """Build simplified agent coordination flow that avoids recursion"""
    
    graph = StateGraph(AgentState)
    
    # Single node that handles all logic
    graph.add_node("execute_step", execute_single_step)
    
    # Set entry point
    graph.set_entry_point("execute_step")
    
    # Simple routing: always end after one step to avoid recursion
    graph.add_edge("execute_step", END)
    
    # Compile WITHOUT checkpointer and with minimal recursion limit
    return graph.compile()

# Helper functions
def _calculate_exploration_progress(grid: Grid) -> float:
    """Calculate exploration progress from grid state"""
    # This integrates with scout's visited_cells through the simulation
    # For now, return a simple calculation based on agent positions
    total_cells = grid.width * grid.height
    explored_cells = 0
    
    # Get scout agent's visited cells if available
    if scout_agent and hasattr(scout_agent, 'visited_cells'):
        explored_cells = len(scout_agent.visited_cells)
    else:
        # Fallback calculation
        for agent_id in ["scout", "builder", "strategist"]:
            pos = grid.get_agent_position(agent_id)
            if pos:
                explored_cells += 1
    
    progress = min(explored_cells / total_cells, 1.0)
    logger.debug(f"Exploration progress: {explored_cells}/{total_cells} = {progress:.1%}")
    return progress

def _count_buildings(grid: Grid) -> int:
    """Count buildings in the grid"""
    count = 0
    for cell in grid.grid.values():
        if cell.structure and cell.structure == "building":
            count += 1
    logger.debug(f"Buildings count: {count}")
    return count# apps/backend/app/langgraph/agent_flow.py

from langgraph.graph import StateGraph, END
from app.agents.builder import BuilderAgent
from app.agents.strategist import StrategistAgent
from app.agents.scout import ScoutAgent
from app.tools.message import Message
from app.env.grid import Grid
from typing import TypedDict, List, Literal, Dict
import logging

logger = logging.getLogger(__name__)

# Enhanced state schema with conditional logic
class AgentState(TypedDict):
    grid: Grid
    messages: List[Message]
    step_count: int
    mission_phase: Literal["initialization", "exploration", "analysis", "construction", "optimization", "completion"]
    objectives: List[str]
    exploration_progress: float
    buildings_built: int
    active_threats: int
    resource_constraints: bool
    coordination_needed: bool
    emergency_mode: bool
    last_activity: Dict[str, str]  # agent_id -> last_action_type

# Global agent instances (will be replaced by actual instances)
scout_agent = None
strategist_agent = None  
builder_agent = None

def initialize_agents(grid: Grid):
    """Initialize agent instances with the grid"""
    global scout_agent, strategist_agent, builder_agent
    scout_agent = ScoutAgent("scout", grid)
    strategist_agent = StrategistAgent("strategist", grid)
    builder_agent = BuilderAgent("builder", grid)
    logger.info("Agents initialized for conditional flow")

# Conditional routing functions
def should_prioritize_exploration(state: AgentState) -> bool:
    """Determine if exploration should be prioritized"""
    return (state["exploration_progress"] < 0.6 and 
            state["mission_phase"] in ["initialization", "exploration"])

def should_enter_analysis_phase(state: AgentState) -> bool:
    """Determine if we should enter analysis phase"""
    return (state["exploration_progress"] >= 0.6 and 
            state["mission_phase"] in ["exploration"] and
            not state["emergency_mode"])

def should_coordinate_construction(state: AgentState) -> bool:
    """Determine if construction coordination is needed"""
    return (state["mission_phase"] in ["analysis", "construction"] and
            state["buildings_built"] < 5 and
            state.get("strategic_plan_ready", False))

def should_handle_emergency(state: AgentState) -> bool:
    """Determine if emergency handling is needed"""
    return (state["emergency_mode"] or 
            state["active_threats"] > 0 or
            state["resource_constraints"])

# Enhanced agent step functions with conditional logic
def scout_exploration_step(state: AgentState) -> AgentState:
    """Scout step focused on exploration"""
    if scout_agent is None:
        initialize_agents(state["grid"])
    
    logger.info(f"Scout exploration step - Progress: {state['exploration_progress']:.1%}")
    
    # Scout acts with exploration priority
    result_message = scout_agent.step(state["messages"])
    
    new_messages = state["messages"].copy()
    if result_message:
        new_messages.append(result_message)
        state["last_activity"]["scout"] = "exploration"
    
    # Update exploration progress
    state["exploration_progress"] = _calculate_exploration_progress(state["grid"])
    
    return {
        **state,
        "messages": new_messages
    }

def strategist_analysis_step(state: AgentState) -> AgentState:
    """Strategist step focused on analysis and planning"""
    if strategist_agent is None:
        initialize_agents(state["grid"])
    
    logger.info(f"Strategist analysis step - Buildings: {state['buildings_built']}")
    
    # Strategist analyzes scout reports and creates plans
    result_message = strategist_agent.step(state["messages"])
    
    new_messages = state["messages"].copy()
    if result_message:
        new_messages.append(result_message)
        state["last_activity"]["strategist"] = "analysis"
        
        # Check if strategic planning is complete
        if "STRATEGIC_BUILD_ORDER" in result_message.content:
            state["strategic_plan_ready"] = True
    
    return {
        **state,
        "messages": new_messages
    }

def builder_construction_step(state: AgentState) -> AgentState:
    """Builder step focused on construction"""
    if builder_agent is None:
        initialize_agents(state["grid"])
    
    logger.info(f"Builder construction step - Current buildings: {state['buildings_built']}")
    
    # Builder executes construction based on strategic orders
    result_message = builder_agent.step(state["messages"])
    
    new_messages = state["messages"].copy()
    if result_message:
        new_messages.append(result_message)
        state["last_activity"]["builder"] = "construction"
    
    # Update buildings count
    state["buildings_built"] = _count_buildings(state["grid"])
    
    return {
        **state,
        "messages": new_messages
    }

def coordination_step(state: AgentState) -> AgentState:
    """Multi-agent coordination step"""
    if scout_agent is None:
        initialize_agents(state["grid"])
    
    logger.info("Executing coordination step - all agents collaborate")
    
    new_messages = state["messages"].copy()
    
    # All agents act in coordinated manner
    # Scout provides intel
    scout_result = scout_agent.step(new_messages)
    if scout_result:
        new_messages.append(scout_result)
    
    # Strategist coordinates based on latest intel
    strategist_result = strategist_agent.step(new_messages)
    if strategist_result:
        new_messages.append(strategist_result)
    
    # Builder executes coordinated actions
    builder_result = builder_agent.step(new_messages)
    if builder_result:
        new_messages.append(builder_result)
    
    # Update coordination status
    state["coordination_needed"] = False
    state["last_activity"]["scout"] = "coordination"
    state["last_activity"]["strategist"] = "coordination"
    state["last_activity"]["builder"] = "coordination"
    
    # Update metrics
    state["exploration_progress"] = _calculate_exploration_progress(state["grid"])
    state["buildings_built"] = _count_buildings(state["grid"])
    
    return {
        **state,
        "messages": new_messages
    }

def emergency_response_step(state: AgentState) -> AgentState:
    """Emergency response coordination"""
    if scout_agent is None:
        initialize_agents(state["grid"])
    
    logger.warning("Emergency response step activated")
    
    new_messages = state["messages"].copy()
    
    # Emergency prioritization: Scout assesses, Strategist adapts, Builder responds
    emergency_message = Message(
        sender="system",
        content="EMERGENCY_MODE: Prioritize immediate response and coordination"
    )
    new_messages.append(emergency_message)
    
    # All agents respond to emergency
    for agent in [scout_agent, strategist_agent, builder_agent]:
        if agent:
            result = agent.step(new_messages)
            if result:
                new_messages.append(result)
    
    # Reset emergency flags
    state["emergency_mode"] = False
    state["active_threats"] = max(0, state["active_threats"] - 1)
    
    return {
        **state,
        "messages": new_messages
    }

# Conditional routing functions with proper termination
def route_from_exploration(state: AgentState) -> str:
    """Route after exploration phase with termination conditions"""
    logger.info(f"Routing from exploration: progress={state['exploration_progress']:.1%}, phase={state['mission_phase']}")
    
    # Emergency takes priority
    if should_handle_emergency(state):
        return "emergency_response"
    
    # Check for mission completion
    if state["buildings_built"] >= 5:
        state["mission_phase"] = "completion"
        return END
    
    # Transition to analysis if enough exploration is done
    if should_enter_analysis_phase(state):
        state["mission_phase"] = "analysis"
        return "strategist_analysis"
    
    # Force coordination every few steps to prevent infinite loops
    if state["step_count"] % 5 == 0:
        state["coordination_needed"] = True
        return "coordination"
    
    # End after too many steps to prevent infinite loops
    if state["step_count"] > 20:
        return END
    
    # Continue exploration by ending this step
    return END

def route_from_analysis(state: AgentState) -> str:
    """Route after analysis phase with termination conditions"""
    logger.info(f"Routing from analysis: buildings={state['buildings_built']}, strategic_plan={state.get('strategic_plan_ready', False)}")
    
    # Emergency takes priority
    if should_handle_emergency(state):
        return "emergency_response"
    
    # Check for mission completion
    if state["buildings_built"] >= 5:
        state["mission_phase"] = "completion"
        return END
    
    # Move to construction if plan is ready
    if should_coordinate_construction(state):
        state["mission_phase"] = "construction"
        return "builder_construction"
    
    # Force coordination periodically
    if state["step_count"] % 4 == 0:
        state["coordination_needed"] = True
        return "coordination"
    
    # End after too many steps
    if state["step_count"] > 20:
        return END
    
    # End this step
    return END

def route_from_construction(state: AgentState) -> str:
    """Route after construction phase with termination conditions"""
    logger.info(f"Routing from construction: buildings={state['buildings_built']}")
    
    # Emergency takes priority
    if should_handle_emergency(state):
        return "emergency_response"
    
    # Mission completion check
    if state["buildings_built"] >= 5:
        state["mission_phase"] = "completion"
        return END
    
    # If exploration is still needed and buildings are low, go back to scout
    if state["exploration_progress"] < 0.8 and state["buildings_built"] < 2:
        return "scout_exploration"
    
    # Force coordination periodically
    if state["step_count"] % 3 == 0:
        state["coordination_needed"] = True
        return "coordination"
    
    # End after too many steps
    if state["step_count"] > 20:
        return END
    
    # End this step
    return END

def route_from_coordination(state: AgentState) -> str:
    """Route after coordination step with termination conditions"""
    logger.info(f"Routing from coordination: phase={state['mission_phase']}")
    
    # Emergency takes priority
    if should_handle_emergency(state):
        return "emergency_response"
    
    # Mission completion check
    if state["buildings_built"] >= 5:
        state["mission_phase"] = "completion"
        return END
    
    # Route based on mission phase but always end the step
    phase = state["mission_phase"]
    if phase == "exploration" or state["exploration_progress"] < 0.6:
        return "scout_exploration"
    elif phase == "analysis" or not state.get("strategic_plan_ready", False):
        return "strategist_analysis"
    elif phase == "construction":
        return "builder_construction"
    
    # Default: end the step
    return END

def route_from_emergency(state: AgentState) -> str:
    """Route after emergency response with termination conditions"""
    logger.info("Routing from emergency response")
    
    # Always end after emergency to prevent loops
    state["emergency_mode"] = False
    return END

def determine_coordination_need(state: AgentState) -> AgentState:
    """Determine if coordination is needed based on agent activities"""
    # Check if agents haven't communicated recently
    scout_activity = state["last_activity"].get("scout", "none")
    strategist_activity = state["last_activity"].get("strategist", "none")
    builder_activity = state["last_activity"].get("builder", "none")
    
    # Trigger coordination if agents are working in isolation
    if (scout_activity != "coordination" and 
        strategist_activity != "coordination" and 
        builder_activity != "coordination" and
        state["step_count"] % 3 == 0):  # Every 3 steps
        state["coordination_needed"] = True
    
    return state

# Build the enhanced conditional flow
def build_agent_flow():
    """Build enhanced agent coordination flow with conditional routing"""
    
    graph = StateGraph(AgentState)
    
    # Add specialized nodes
    graph.add_node("scout_exploration", scout_exploration_step)
    graph.add_node("strategist_analysis", strategist_analysis_step)
    graph.add_node("builder_construction", builder_construction_step)
    graph.add_node("coordination", coordination_step)
    graph.add_node("emergency_response", emergency_response_step)
    
    # Set entry point
    graph.set_entry_point("scout_exploration")
    
    # Simplified conditional edges to prevent recursion
    graph.add_conditional_edges(
        "scout_exploration",
        route_from_exploration,
        {
            "strategist_analysis": "strategist_analysis", 
            "coordination": "coordination",
            "emergency_response": "emergency_response",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "strategist_analysis",
        route_from_analysis,
        {
            "builder_construction": "builder_construction",
            "coordination": "coordination",
            "emergency_response": "emergency_response",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "builder_construction", 
        route_from_construction,
        {
            "scout_exploration": "scout_exploration",
            "coordination": "coordination",
            "emergency_response": "emergency_response",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "coordination",
        route_from_coordination,
        {
            "scout_exploration": "scout_exploration",
            "strategist_analysis": "strategist_analysis",
            "builder_construction": "builder_construction",
            "emergency_response": "emergency_response",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "emergency_response",
        route_from_emergency,
        {
            "scout_exploration": "scout_exploration",
            "strategist_analysis": "strategist_analysis", 
            "builder_construction": "builder_construction",
            "coordination": "coordination",
            END: END
        }
    )
    
    # Compile with recursion limit
    return graph.compile({"recursion_limit": 10})

def route_based_on_phase(state: AgentState) -> str:
    """Route based on current mission phase"""
    phase = state["mission_phase"]
    
    if phase == "exploration" or state["exploration_progress"] < 0.6:
        return "scout_exploration"
    elif phase == "analysis" or not state.get("strategic_plan_ready", False):
        return "strategist_analysis"
    elif phase == "construction":
        return "builder_construction"
    else:
        return "scout_exploration"

# Helper functions
def _calculate_exploration_progress(grid: Grid) -> float:
    """Calculate exploration progress from grid state"""
    # This would integrate with your existing scout's visited_cells
    # For now, return a placeholder calculation
    total_cells = grid.width * grid.height
    explored_cells = 0
    
    # Count cells that have been visited (you'd need to track this)
    # This is a simplified version
    for agent_id in ["scout", "builder", "strategist"]:
        pos = grid.get_agent_position(agent_id)
        if pos:
            explored_cells += 1
    
    return min(explored_cells / total_cells, 1.0)

def _count_buildings(grid: Grid) -> int:
    """Count buildings in the grid"""
    count = 0
    for cell in grid.grid.values():
        if cell.structure and cell.structure != "scanned":
            count += 1
    return count
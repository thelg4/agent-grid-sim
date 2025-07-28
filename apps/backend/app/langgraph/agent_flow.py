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
    
    # CRITICAL: Compile WITHOUT any parameters to avoid checkpointer requirement
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
    return count
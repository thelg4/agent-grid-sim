from langgraph.graph import StateGraph, END
from app.agents.builder import BuilderAgent
from app.agents.strategist import StrategistAgent
from app.agents.scout import ScoutAgent
from app.tools.message import Message, MessageType, MessagePriority
from app.tools.message_queue import CoordinationManager, SharedState
from app.env.grid import Grid
from typing import TypedDict, List, Literal, Dict, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)

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
    last_activity: Dict[str, str]
    strategic_plan_ready: bool
    shared_state: SharedState
    coordination_manager: CoordinationManager
    agent_states: Dict[str, Dict[str, Any]]
    error_recovery_attempts: int
    performance_metrics: Dict[str, float]
    parallel_execution_enabled: bool

# Global agent instances and coordination
scout_agent = None
strategist_agent = None  
builder_agent = None
coordination_manager = None
shared_state = None

def initialize_agents(grid: Grid):
    """Initialize agent instances with enhanced coordination"""
    global scout_agent, strategist_agent, builder_agent, coordination_manager, shared_state
    
    # Initialize shared systems
    shared_state = SharedState()
    coordination_manager = CoordinationManager(shared_state)
    
    # Initialize agents with coordination capabilities
    scout_agent = ScoutAgent("scout", grid)
    strategist_agent = StrategistAgent("strategist", grid)
    builder_agent = BuilderAgent("builder", grid)
    
    # Set up initial resources
    shared_state.resources.update({
        "materials": 100,
        "energy": 50,
        "tools": 10
    })
    
    # Define agent capabilities
    shared_state.agent_capabilities.update({
        "scout": {"exploration", "reconnaissance", "pathfinding"},
        "builder": {"construction", "resource_management", "engineering"},
        "strategist": {"planning", "coordination", "analysis"}
    })
    
    logger.info("Enhanced agents and coordination system initialized")

def initialization_phase(state: AgentState) -> AgentState:
    """Initialize agents and establish communication protocols"""
    logger.info("Executing initialization phase")
    
    try:
        if scout_agent is None:
            initialize_agents(state["grid"])
        
        # Update state to move to exploration
        state["mission_phase"] = "exploration"
        state["last_activity"].update({"scout": "initialized", "strategist": "initialized", "builder": "initialized"})
        
        logger.info("Initialization complete, transitioning to exploration")
        return state
        
    except Exception as e:
        logger.error(f"Initialization phase error: {e}")
        state["mission_phase"] = "completion"
        return state

def exploration_phase(state: AgentState) -> AgentState:
    """Execute ONE exploration step"""
    logger.info("Executing exploration phase")
    
    try:
        # Execute scout step and capture the message
        if scout_agent and coordination_manager:
            scout_messages = coordination_manager.get_messages_for_agent("scout")
            result_message = scout_agent.step(scout_messages)
            
            if result_message:
                # Add the message to our state messages
                state["messages"].append(result_message)
                coordination_manager.send_message(result_message)
                state["last_activity"]["scout"] = "exploration"
                logger.info(f"Scout generated message: {result_message.content}")
        
        # Update exploration progress
        state["exploration_progress"] = _calculate_exploration_progress(state["grid"])
        
        logger.info(f"Exploration step complete. Progress: {state['exploration_progress']:.1%}")
        
        # Check if we should transition to analysis (30% threshold)
        if state["exploration_progress"] >= 0.3 or state["step_count"] >= 10:
            state["mission_phase"] = "analysis"
            logger.info("Sufficient exploration completed, transitioning to analysis phase")
        
        return state
        
    except Exception as e:
        logger.error(f"Exploration phase error: {e}")
        state["mission_phase"] = "analysis"  # Move forward on error
        return state

def analysis_phase(state: AgentState) -> AgentState:
    """Execute ONE analysis step"""
    logger.info("Executing analysis phase")
    
    try:
        if strategist_agent and coordination_manager:
            strategist_messages = coordination_manager.get_messages_for_agent("strategist")
            result_message = strategist_agent.step(strategist_messages)
            
            if result_message:
                # Add the message to our state messages
                state["messages"].append(result_message)
                coordination_manager.send_message(result_message)
                state["last_activity"]["strategist"] = "analysis"
                logger.info(f"Strategist generated message: {result_message.content}")
                
                # Check if this is a build order
                if "STRATEGIC_BUILD_ORDER" in result_message.content:
                    state["strategic_plan_ready"] = True
                    state["mission_phase"] = "construction"
                    logger.info("Strategic build order issued, transitioning to construction")
                    return state
        
        # If no build order yet, stay in analysis but mark plan as ready for next iteration
        state["strategic_plan_ready"] = True
        state["mission_phase"] = "construction"
        
        logger.info("Analysis step complete, transitioning to construction")
        return state
        
    except Exception as e:
        logger.error(f"Analysis phase error: {e}")
        state["mission_phase"] = "construction"
        state["strategic_plan_ready"] = True
        return state

def construction_phase(state: AgentState) -> AgentState:
    """Execute ONE construction step"""
    logger.info("Executing construction phase")
    
    try:
        if builder_agent and coordination_manager:
            builder_messages = coordination_manager.get_messages_for_agent("builder")
            result_message = builder_agent.step(builder_messages)
            
            if result_message:
                # Add the message to our state messages
                state["messages"].append(result_message)
                coordination_manager.send_message(result_message)
                state["last_activity"]["builder"] = "construction"
                logger.info(f"Builder generated message: {result_message.content}")
        
        # Update buildings count
        state["buildings_built"] = _count_buildings(state["grid"])
        
        logger.info(f"Construction step complete. Buildings: {state['buildings_built']}")
        
        # Check if we should transition to completion
        if state["buildings_built"] >= 5:
            state["mission_phase"] = "completion"
            logger.info("Building target reached, transitioning to completion")
        # Otherwise, cycle back to get more strategic orders
        elif state["step_count"] % 3 == 0:  # Every 3rd step, go back to analysis for new orders
            state["mission_phase"] = "analysis"
            logger.info("Cycling back to analysis for new strategic orders")
        
        return state
        
    except Exception as e:
        logger.error(f"Construction phase error: {e}")
        return state

def completion_phase(state: AgentState) -> AgentState:
    """Final completion phase"""
    logger.info("Mission completed successfully")
    
    state["mission_phase"] = "completion"
    state["last_activity"].update({agent: "completed" for agent in ["scout", "strategist", "builder"]})
    
    # Add completion message
    completion_msg = Message(
        sender="system",
        content="🎉 MISSION ACCOMPLISHED: All objectives completed!",
        message_type=MessageType.REPORT,
        priority=MessagePriority.HIGH
    )
    state["messages"].append(completion_msg)
    
    return state

def route_phase(state: AgentState) -> str:
    """Route to the appropriate phase based on current mission phase"""
    phase = state["mission_phase"]
    
    logger.info(f"Routing to phase: {phase}")
    
    if phase == "initialization":
        return "initialization_phase"
    elif phase == "exploration":
        return "exploration_phase"
    elif phase == "analysis":
        return "analysis_phase"
    elif phase == "construction":
        return "construction_phase"
    elif phase == "completion":
        return "completion_phase"
    else:
        return "completion_phase"  # Default fallback

def build_agent_flow():
    """Build enhanced agent flow with proper phase transitions"""
    
    # Create state graph
    graph = StateGraph(AgentState)
    
    # Add phase nodes
    graph.add_node("initialization_phase", initialization_phase)
    graph.add_node("exploration_phase", exploration_phase)
    graph.add_node("analysis_phase", analysis_phase)
    graph.add_node("construction_phase", construction_phase)
    graph.add_node("completion_phase", completion_phase)
    
    # Set entry point
    graph.set_entry_point("initialization_phase")
    
    # Add conditional routing from each phase
    phase_routes = {
        "initialization_phase": "initialization_phase",
        "exploration_phase": "exploration_phase", 
        "analysis_phase": "analysis_phase",
        "construction_phase": "construction_phase",
        "completion_phase": "completion_phase"
    }
    
    # Route from each phase based on the updated state
    graph.add_conditional_edges("initialization_phase", route_phase, phase_routes)
    graph.add_conditional_edges("exploration_phase", route_phase, phase_routes)
    graph.add_conditional_edges("analysis_phase", route_phase, phase_routes)
    graph.add_conditional_edges("construction_phase", route_phase, phase_routes)
    
    # Completion phase ends the flow
    graph.add_edge("completion_phase", END)
    
    logger.info("Compiling enhanced LangGraph flow with proper phase management")
    return graph.compile()

# Helper functions with enhanced error handling
def _calculate_exploration_progress(grid: Grid) -> float:
    """Calculate exploration progress with error handling"""
    try:
        if scout_agent and hasattr(scout_agent, 'visited_cells'):
            total_cells = grid.width * grid.height
            explored_cells = len(scout_agent.visited_cells)
            progress = min(explored_cells / total_cells, 1.0)
            return progress
        return 0.0
    except Exception as e:
        logger.error(f"Error calculating exploration progress: {e}")
        return 0.0

def _count_buildings(grid: Grid) -> int:
    """Count buildings with error handling"""
    try:
        count = 0
        for cell in grid.grid.values():
            if cell.structure and hasattr(cell.structure, 'built_by'):
                count += 1
        return count
    except Exception as e:
        logger.error(f"Error counting buildings: {e}")
        return 0
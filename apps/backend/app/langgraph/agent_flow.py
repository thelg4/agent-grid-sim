# # Corrected version of apps/backend/app/langgraph/agent_flow.py
# # The key fix is ensuring ALL routing destinations are properly defined

# from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import MemorySaver
# from app.agents.builder import BuilderAgent
# from app.agents.strategist import StrategistAgent
# from app.agents.scout import ScoutAgent
# from app.tools.message import Message, MessageType, MessagePriority
# from app.tools.message_queue import CoordinationManager, SharedState
# from app.env.grid import Grid
# from typing import TypedDict, List, Literal, Dict, Any, Optional
# import logging
# import time
# import asyncio
# from concurrent.futures import ThreadPoolExecutor
# import traceback

# logger = logging.getLogger(__name__)

# class AgentState(TypedDict):
#     grid: Grid
#     messages: List[Message]
#     step_count: int
#     mission_phase: Literal["initialization", "exploration", "analysis", "construction", "optimization", "completion"]
#     objectives: List[str]
#     exploration_progress: float
#     buildings_built: int
#     active_threats: int
#     resource_constraints: bool
#     coordination_needed: bool
#     emergency_mode: bool
#     last_activity: Dict[str, str]
#     strategic_plan_ready: bool
#     shared_state: SharedState
#     coordination_manager: CoordinationManager
#     agent_states: Dict[str, Dict[str, Any]]
#     error_recovery_attempts: int
#     performance_metrics: Dict[str, float]
#     parallel_execution_enabled: bool

# # Global agent instances and coordination
# scout_agent = None
# strategist_agent = None  
# builder_agent = None
# coordination_manager = None
# shared_state = None
# executor = ThreadPoolExecutor(max_workers=3)

# def initialize_agents(grid: Grid):
#     """Initialize agent instances with enhanced coordination"""
#     global scout_agent, strategist_agent, builder_agent, coordination_manager, shared_state
    
#     # Initialize shared systems
#     shared_state = SharedState()
#     coordination_manager = CoordinationManager(shared_state)
    
#     # Initialize agents with coordination capabilities
#     scout_agent = ScoutAgent("scout", grid)
#     strategist_agent = StrategistAgent("strategist", grid)
#     builder_agent = BuilderAgent("builder", grid)
    
#     # Set up initial resources
#     shared_state.resources.update({
#         "materials": 100,
#         "energy": 50,
#         "tools": 10
#     })
    
#     # Define agent capabilities
#     shared_state.agent_capabilities.update({
#         "scout": {"exploration", "reconnaissance", "pathfinding"},
#         "builder": {"construction", "resource_management", "engineering"},
#         "strategist": {"planning", "coordination", "analysis"}
#     })
    
#     logger.info("Enhanced agents and coordination system initialized")

# def should_execute_parallel(state: AgentState) -> bool:
#     """Determine if agents should execute in parallel"""
#     return (
#         state["parallel_execution_enabled"] and 
#         not state["emergency_mode"] and
#         state["step_count"] > 5  # Allow parallel after initial coordination
#     )

# def route_next_action(state: AgentState) -> str:
#     """Enhanced conditional routing based on comprehensive state analysis"""
#     try:
#         phase = state["mission_phase"]
#         exploration = state["exploration_progress"]
#         buildings = state["buildings_built"]
#         emergency = state["emergency_mode"]
#         coordination_needed = state["coordination_needed"]
        
#         logger.info(f"Routing decision: phase={phase}, exploration={exploration:.1%}, "
#                    f"buildings={buildings}, emergency={emergency}, coordination={coordination_needed}")
        
#         # Emergency routing takes highest priority
#         if emergency:
#             return "emergency_response"
        
#         # Coordination routing
#         if coordination_needed:
#             return "coordination_phase"
            
#         # Check for error recovery needs
#         if state["error_recovery_attempts"] > 0:
#             return "error_recovery"
        
#         # Parallel execution routing
#         if should_execute_parallel(state):
#             return "parallel_execution"
        
#         # Phase-based routing with enhanced logic
#         if phase == "initialization":
#             return "exploration_phase"  # Changed from initialization_phase to avoid loops
#         elif phase == "exploration" and exploration < 0.7:
#             return "exploration_phase" 
#         elif phase == "analysis" or (exploration >= 0.7 and not state["strategic_plan_ready"]):
#             return "analysis_phase"
#         elif phase == "construction" and buildings < 5:
#             return "construction_phase"
#         elif phase == "optimization" or buildings >= 5:
#             return "optimization_phase"
#         else:
#             return "completion_phase"
            
#     except Exception as e:
#         logger.error(f"Error in routing decision: {e}")
#         return "error_recovery"

# def initialization_phase(state: AgentState) -> AgentState:
#     """Initialize agents and establish communication protocols"""
#     logger.info("Executing initialization phase")
    
#     try:
#         if scout_agent is None:
#             initialize_agents(state["grid"])
        
#         # Send initialization messages
#         init_messages = [
#             Message("system", "Initialize exploration protocols", 
#                    MessageType.COMMAND, MessagePriority.HIGH, "scout"),
#             Message("system", "Initialize strategic planning systems",
#                    MessageType.COMMAND, MessagePriority.HIGH, "strategist"),
#             Message("system", "Initialize construction capabilities",
#                    MessageType.COMMAND, MessagePriority.HIGH, "builder")
#         ]
        
#         if coordination_manager:
#             for msg in init_messages:
#                 coordination_manager.send_message(msg)
        
#         # Update state
#         state["mission_phase"] = "exploration"
#         state["last_activity"].update({"scout": "initialized", "strategist": "initialized", "builder": "initialized"})
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Initialization phase error: {e}")
#         state["error_recovery_attempts"] += 1
#         return state

# def exploration_phase(state: AgentState) -> AgentState:
#     """Enhanced exploration with resource management"""
#     logger.info("Executing exploration phase")
#     start_time = time.time()
    
#     try:
#         # Execute scout with resource considerations
#         if scout_agent and coordination_manager:
#             scout_messages = coordination_manager.get_messages_for_agent("scout")
#             result = scout_agent.step(scout_messages)
            
#             if result:
#                 coordination_manager.send_message(result)
#                 state["last_activity"]["scout"] = "exploration"
        
#         # Check if we need to transition to analysis
#         if state["exploration_progress"] >= 0.7:
#             state["mission_phase"] = "analysis"
#             state["coordination_needed"] = True
        
#         # Update performance metrics
#         execution_time = time.time() - start_time
#         state["performance_metrics"]["exploration_time"] = execution_time
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Exploration phase error: {e}")
#         state["error_recovery_attempts"] += 1
#         return state

# def analysis_phase(state: AgentState) -> AgentState:
#     """Strategic analysis with enhanced decision making"""
#     logger.info("Executing analysis phase")
#     start_time = time.time()
    
#     try:
#         if strategist_agent and coordination_manager:
#             strategist_messages = coordination_manager.get_messages_for_agent("strategist")
#             result = strategist_agent.step(strategist_messages)
            
#             if result:
#                 coordination_manager.send_message(result)
#                 state["last_activity"]["strategist"] = "analysis"
                
#                 # Check if strategic plan is ready
#                 if "STRATEGIC_BUILD_ORDER" in result.content:
#                     state["strategic_plan_ready"] = True
#                     state["mission_phase"] = "construction"
        
#         execution_time = time.time() - start_time
#         state["performance_metrics"]["analysis_time"] = execution_time
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Analysis phase error: {e}")
#         state["error_recovery_attempts"] += 1
#         return state

# def construction_phase(state: AgentState) -> AgentState:
#     """Construction with resource coordination"""
#     logger.info("Executing construction phase")
#     start_time = time.time()
    
#     try:
#         if builder_agent and coordination_manager:
#             builder_messages = coordination_manager.get_messages_for_agent("builder")
#             result = builder_agent.step(builder_messages)
            
#             if result:
#                 coordination_manager.send_message(result)
#                 state["last_activity"]["builder"] = "construction"
        
#         # Check for completion
#         if state["buildings_built"] >= 5:
#             state["mission_phase"] = "optimization"
        
#         execution_time = time.time() - start_time
#         state["performance_metrics"]["construction_time"] = execution_time
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Construction phase error: {e}")
#         state["error_recovery_attempts"] += 1
#         return state

# async def execute_agent_async(agent, messages):
#     """Execute agent step asynchronously"""
#     loop = asyncio.get_event_loop()
#     return await loop.run_in_executor(executor, agent.step, messages)

# def parallel_execution(state: AgentState) -> AgentState:
#     """Execute multiple agents in parallel where appropriate"""
#     logger.info("Executing parallel agent operations")
#     start_time = time.time()
    
#     try:
#         if not (scout_agent and strategist_agent and builder_agent and coordination_manager):
#             logger.warning("Not all agents initialized for parallel execution")
#             return state
            
#         # Prepare messages for each agent
#         scout_messages = coordination_manager.get_messages_for_agent("scout")
#         strategist_messages = coordination_manager.get_messages_for_agent("strategist") 
#         builder_messages = coordination_manager.get_messages_for_agent("builder")
        
#         # Execute in parallel using thread pool
#         future_scout = executor.submit(scout_agent.step, scout_messages)
#         future_strategist = executor.submit(strategist_agent.step, strategist_messages)
#         future_builder = executor.submit(builder_agent.step, builder_messages)
        
#         # Collect results with timeout
#         results = []
#         for future, agent_name in [(future_scout, "scout"), (future_strategist, "strategist"), (future_builder, "builder")]:
#             try:
#                 result = future.result(timeout=30)  # 30 second timeout
#                 if result:
#                     coordination_manager.send_message(result)
#                     results.append((agent_name, result))
#                     state["last_activity"][agent_name] = "parallel_execution"
#             except Exception as e:
#                 logger.error(f"Parallel execution error for {agent_name}: {e}")
#                 state["last_activity"][agent_name] = "error"
        
#         execution_time = time.time() - start_time
#         state["performance_metrics"]["parallel_execution_time"] = execution_time
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Parallel execution error: {e}")
#         state["error_recovery_attempts"] += 1
#         return state

# def coordination_phase(state: AgentState) -> AgentState:
#     """Handle agent coordination and conflict resolution"""
#     logger.info("Executing coordination phase")
    
#     try:
#         if coordination_manager:
#             # Detect and resolve conflicts
#             conflicts = coordination_manager.detect_conflicts()
            
#             for conflict in conflicts:
#                 conflict_type = conflict["type"]
#                 if conflict_type in coordination_manager.conflict_resolution_strategies:
#                     resolution_messages = coordination_manager.conflict_resolution_strategies[conflict_type](conflict)
#                     for msg in resolution_messages:
#                         coordination_manager.send_message(msg)
        
#         # Update coordination status
#         state["coordination_needed"] = False
#         state["last_activity"].update({agent: "coordination" for agent in ["scout", "strategist", "builder"]})
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Coordination phase error: {e}")
#         state["error_recovery_attempts"] += 1
#         return state

# def emergency_response(state: AgentState) -> AgentState:
#     """Handle emergency situations with all agents"""
#     logger.info("Executing emergency response")
    
#     try:
#         if coordination_manager:
#             # Send emergency messages to all agents
#             emergency_msg = Message(
#                 "system", "Emergency situation detected - coordinate response",
#                 MessageType.COMMAND, MessagePriority.URGENT, requires_ack=True
#             )
#             coordination_manager.send_message(emergency_msg)
        
#         # Execute all agents in emergency mode
#         for agent_name, agent in [("scout", scout_agent), ("strategist", strategist_agent), ("builder", builder_agent)]:
#             if agent and coordination_manager:
#                 messages = coordination_manager.get_messages_for_agent(agent_name)
#                 result = agent.step(messages)
#                 if result:
#                     coordination_manager.send_message(result)
#                 state["last_activity"][agent_name] = "emergency"
        
#         # Reset emergency mode after handling
#         state["emergency_mode"] = False
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Emergency response error: {e}")
#         state["error_recovery_attempts"] += 1
#         return state

# def error_recovery(state: AgentState) -> AgentState:
#     """Handle error recovery and system restoration"""
#     logger.info("Executing error recovery")
    
#     try:
#         # Attempt to reinitialize failed components
#         if scout_agent is None or strategist_agent is None or builder_agent is None:
#             initialize_agents(state["grid"])
        
#         # Reset error counter if recovery successful
#         state["error_recovery_attempts"] = max(0, state["error_recovery_attempts"] - 1)
        
#         # Send recovery messages
#         if coordination_manager:
#             recovery_msg = Message(
#                 "system", "System recovery in progress",
#                 MessageType.REPORT, MessagePriority.HIGH
#             )
#             coordination_manager.send_message(recovery_msg)
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Error recovery failed: {e}")
#         state["error_recovery_attempts"] += 1
#         return state

# def optimization_phase(state: AgentState) -> AgentState:
#     """Optimization phase for mission completion"""
#     logger.info("Executing optimization phase")
    
#     try:
#         # Check if mission should be completed
#         if state["buildings_built"] >= 5:
#             state["mission_phase"] = "completion"
#             return state
        
#         # Execute final coordination between agents
#         for agent_name, agent in [("scout", scout_agent), ("strategist", strategist_agent), ("builder", builder_agent)]:
#             if agent and coordination_manager:
#                 messages = coordination_manager.get_messages_for_agent(agent_name)
#                 result = agent.step(messages)
#                 if result:
#                     coordination_manager.send_message(result)
#                 state["last_activity"][agent_name] = "optimization"
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Optimization phase error: {e}")
#         state["error_recovery_attempts"] += 1
#         return state

# def completion_phase(state: AgentState) -> AgentState:
#     """Final completion phase"""
#     logger.info("Executing completion phase")
    
#     try:
#         state["mission_phase"] = "completion"
#         state["last_activity"].update({agent: "completed" for agent in ["scout", "strategist", "builder"]})
        
#         # Send completion message
#         if coordination_manager:
#             completion_msg = Message(
#                 "system", "Mission completed successfully",
#                 MessageType.REPORT, MessagePriority.HIGH
#             )
#             coordination_manager.send_message(completion_msg)
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Completion phase error: {e}")
#         return state

# def update_state_metrics(state: AgentState) -> AgentState:
#     """Update performance metrics and state information"""
#     try:
#         # Update exploration progress
#         state["exploration_progress"] = _calculate_exploration_progress(state["grid"])
#         state["buildings_built"] = _count_buildings(state["grid"])
        
#         # Update shared state metrics
#         if shared_state:
#             shared_state.update_metric("exploration_progress", state["exploration_progress"])
#             shared_state.update_metric("buildings_built", state["buildings_built"])
#             shared_state.update_metric("step_count", state["step_count"])
        
#         # Check for phase transitions
#         _check_phase_transitions(state)
        
#         return state
        
#     except Exception as e:
#         logger.error(f"Error updating state metrics: {e}")
#         return state

# def _check_phase_transitions(state: AgentState):
#     """Check and handle phase transitions"""
#     current_phase = state["mission_phase"]
    
#     if current_phase == "exploration" and state["exploration_progress"] >= 0.7:
#         state["mission_phase"] = "analysis"
#         state["coordination_needed"] = True
#     elif current_phase == "analysis" and state["strategic_plan_ready"]:
#         state["mission_phase"] = "construction"
#     elif current_phase == "construction" and state["buildings_built"] >= 5:
#         state["mission_phase"] = "optimization"

# # def build_agent_flow():
# #     """Build enhanced agent coordination flow with conditional routing and error handling"""
    
# #     # Create state graph with checkpointing capability
# #     checkpointer = MemorySaver()
# #     graph = StateGraph(AgentState)
    
# #     # Add all phase nodes
# #     graph.add_node("initialization_phase", initialization_phase)
# #     graph.add_node("exploration_phase", exploration_phase)
# #     graph.add_node("analysis_phase", analysis_phase)
# #     graph.add_node("construction_phase", construction_phase)
# #     graph.add_node("optimization_phase", optimization_phase)
# #     graph.add_node("completion_phase", completion_phase)
# #     graph.add_node("parallel_execution", parallel_execution)
# #     graph.add_node("coordination_phase", coordination_phase)
# #     graph.add_node("emergency_response", emergency_response)
# #     graph.add_node("error_recovery", error_recovery)
# #     graph.add_node("update_metrics", update_state_metrics)
    
# #     # Set entry point
# #     graph.set_entry_point("initialization_phase")
    
# #     # Define ALL possible routes as a comprehensive mapping
# #     all_routes = {
# #         "initialization_phase": "initialization_phase",
# #         "exploration_phase": "exploration_phase",
# #         "analysis_phase": "analysis_phase",
# #         "construction_phase": "construction_phase",
# #         "optimization_phase": "optimization_phase",
# #         "completion_phase": "completion_phase",
# #         "parallel_execution": "parallel_execution",
# #         "coordination_phase": "coordination_phase",
# #         "emergency_response": "emergency_response",
# #         "error_recovery": "error_recovery",
# #         "update_metrics": "update_metrics"
# #     }
    
# #     # Add conditional routing from initialization
# #     graph.add_conditional_edges(
# #         "initialization_phase",
# #         route_next_action,
# #         all_routes
# #     )
    
# #     # Add conditional routing from exploration
# #     graph.add_conditional_edges(
# #         "exploration_phase",
# #         route_next_action,
# #         all_routes
# #     )
    
# #     # Add conditional routing from analysis
# #     graph.add_conditional_edges(
# #         "analysis_phase", 
# #         route_next_action,
# #         all_routes
# #     )
    
# #     # Add conditional routing from construction
# #     graph.add_conditional_edges(
# #         "construction_phase",
# #         route_next_action,
# #         all_routes
# #     )
    
# #     # Add conditional routing from optimization
# #     graph.add_conditional_edges(
# #         "optimization_phase",
# #         route_next_action,
# #         all_routes
# #     )
    
# #     # Add conditional routing from parallel execution
# #     graph.add_conditional_edges(
# #         "parallel_execution",
# #         route_next_action,
# #         all_routes
# #     )
    
# #     # Add conditional routing from coordination
# #     graph.add_conditional_edges(
# #         "coordination_phase",
# #         route_next_action,
# #         all_routes
# #     )
    
# #     # Add conditional routing from emergency
# #     graph.add_conditional_edges(
# #         "emergency_response",
# #         route_next_action,
# #         all_routes
# #     )
    
# #     # Add conditional routing from error recovery
# #     graph.add_conditional_edges(
# #         "error_recovery",
# #         route_next_action,
# #         all_routes
# #     )
    
# #     # Update metrics can route to any phase or END
# #     graph.add_conditional_edges(
# #         "update_metrics",
# #         lambda state: "END" if state["mission_phase"] == "completion" else route_next_action(state),
# #         {**all_routes, "END": END}
# #     )
    
# #     # Completion phase goes to END
# #     graph.add_edge("completion_phase", END)
    
# #     # Compile with checkpointing for state recovery
# #     try:
# #         return graph.compile(checkpointer=checkpointer)
# #     except Exception as e:
# #         logger.error(f"Failed to compile graph with checkpointer: {e}")
# #         # Fallback to compilation without checkpointer
# #         return graph.compile()
# def build_agent_flow():
#     """Build enhanced agent coordination flow with conditional routing"""
    
#     # Create state graph WITHOUT checkpointing to avoid serialization issues
#     graph = StateGraph(AgentState)
    
#     # Add all phase nodes
#     graph.add_node("initialization_phase", initialization_phase)
#     graph.add_node("exploration_phase", exploration_phase)
#     graph.add_node("analysis_phase", analysis_phase)
#     graph.add_node("construction_phase", construction_phase)
#     graph.add_node("optimization_phase", optimization_phase)
#     graph.add_node("completion_phase", completion_phase)
#     graph.add_node("parallel_execution", parallel_execution)
#     graph.add_node("coordination_phase", coordination_phase)
#     graph.add_node("emergency_response", emergency_response)
#     graph.add_node("error_recovery", error_recovery)
#     graph.add_node("update_metrics", update_state_metrics)
    
#     # Set entry point
#     graph.set_entry_point("initialization_phase")
    
#     # Define ALL possible routes as a comprehensive mapping
#     all_routes = {
#         "initialization_phase": "initialization_phase",
#         "exploration_phase": "exploration_phase",
#         "analysis_phase": "analysis_phase",
#         "construction_phase": "construction_phase",
#         "optimization_phase": "optimization_phase",
#         "completion_phase": "completion_phase",
#         "parallel_execution": "parallel_execution",
#         "coordination_phase": "coordination_phase",
#         "emergency_response": "emergency_response",
#         "error_recovery": "error_recovery",
#         "update_metrics": "update_metrics"
#     }
    
#     # Add conditional routing from initialization
#     graph.add_conditional_edges(
#         "initialization_phase",
#         route_next_action,
#         all_routes
#     )
    
#     # Add conditional routing from exploration
#     graph.add_conditional_edges(
#         "exploration_phase",
#         route_next_action,
#         all_routes
#     )
    
#     # Add conditional routing from analysis
#     graph.add_conditional_edges(
#         "analysis_phase", 
#         route_next_action,
#         all_routes
#     )
    
#     # Add conditional routing from construction
#     graph.add_conditional_edges(
#         "construction_phase",
#         route_next_action,
#         all_routes
#     )
    
#     # Add conditional routing from optimization
#     graph.add_conditional_edges(
#         "optimization_phase",
#         route_next_action,
#         all_routes
#     )
    
#     # Add conditional routing from parallel execution
#     graph.add_conditional_edges(
#         "parallel_execution",
#         route_next_action,
#         all_routes
#     )
    
#     # Add conditional routing from coordination
#     graph.add_conditional_edges(
#         "coordination_phase",
#         route_next_action,
#         all_routes
#     )
    
#     # Add conditional routing from emergency
#     graph.add_conditional_edges(
#         "emergency_response",
#         route_next_action,
#         all_routes
#     )
    
#     # Add conditional routing from error recovery
#     graph.add_conditional_edges(
#         "error_recovery",
#         route_next_action,
#         all_routes
#     )
    
#     # Update metrics can route to any phase or END
#     graph.add_conditional_edges(
#         "update_metrics",
#         lambda state: "END" if state["mission_phase"] == "completion" else route_next_action(state),
#         {**all_routes, "END": END}
#     )
    
#     # Completion phase goes to END
#     graph.add_edge("completion_phase", END)
    
#     # Compile WITHOUT checkpointing to avoid serialization issues
#     logger.info("Compiling LangGraph flow without checkpointing (to avoid serialization issues)")
#     return graph.compile()

# # Helper functions with enhanced error handling
# def _calculate_exploration_progress(grid: Grid) -> float:
#     """Calculate exploration progress with error handling"""
#     try:
#         if scout_agent and hasattr(scout_agent, 'visited_cells'):
#             total_cells = grid.width * grid.height
#             explored_cells = len(scout_agent.visited_cells)
#             progress = min(explored_cells / total_cells, 1.0)
#             logger.debug(f"Exploration progress: {explored_cells}/{total_cells} = {progress:.1%}")
#             return progress
#         return 0.0
#     except Exception as e:
#         logger.error(f"Error calculating exploration progress: {e}")
#         return 0.0

# def _count_buildings(grid: Grid) -> int:
#     """Count buildings with error handling"""
#     try:
#         count = 0
#         for cell in grid.grid.values():
#             if cell.structure and hasattr(cell.structure, 'built_by'):
#                 count += 1
#         logger.debug(f"Buildings count: {count}")
#         return count
#     except Exception as e:
#         logger.error(f"Error counting buildings: {e}")
#         return 0

# Fix for apps/backend/app/langgraph/agent_flow.py
# The key fix: Each phase should execute once then EXIT the flow
# Let the simulation.py handle step counting and phase transitions

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
        
        logger.info("Initialization complete")
        return state
        
    except Exception as e:
        logger.error(f"Initialization phase error: {e}")
        state["mission_phase"] = "completion"
        return state

def exploration_phase(state: AgentState) -> AgentState:
    """Execute ONE exploration step"""
    logger.info("Executing exploration phase")
    
    try:
        # Execute scout with resource considerations
        if scout_agent and coordination_manager:
            scout_messages = coordination_manager.get_messages_for_agent("scout")
            result = scout_agent.step(scout_messages)
            
            if result:
                coordination_manager.send_message(result)
                state["last_activity"]["scout"] = "exploration"
        
        # Update exploration progress
        state["exploration_progress"] = _calculate_exploration_progress(state["grid"])
        
        logger.info(f"Exploration step complete. Progress: {state['exploration_progress']:.1%}")
        
        # Check if we should transition to analysis
        if state["exploration_progress"] >= 0.3 or state["step_count"] >= 10:
            state["mission_phase"] = "analysis"
            logger.info("Transitioning to analysis phase")
        
        return state
        
    except Exception as e:
        logger.error(f"Exploration phase error: {e}")
        state["mission_phase"] = "analysis"
        return state

def analysis_phase(state: AgentState) -> AgentState:
    """Execute ONE analysis step"""
    logger.info("Executing analysis phase")
    
    try:
        if strategist_agent and coordination_manager:
            strategist_messages = coordination_manager.get_messages_for_agent("strategist")
            result = strategist_agent.step(strategist_messages)
            
            if result:
                coordination_manager.send_message(result)
                state["last_activity"]["strategist"] = "analysis"
        
        # Mark strategic plan as ready and move to construction
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
            result = builder_agent.step(builder_messages)
            
            if result:
                coordination_manager.send_message(result)
                state["last_activity"]["builder"] = "construction"
        
        # Update buildings count
        state["buildings_built"] = _count_buildings(state["grid"])
        
        logger.info(f"Construction step complete. Buildings: {state['buildings_built']}")
        
        # Check if we should transition to completion
        if state["buildings_built"] >= 5:
            state["mission_phase"] = "completion"
            logger.info("Transitioning to completion phase")
        
        return state
        
    except Exception as e:
        logger.error(f"Construction phase error: {e}")
        return state

def completion_phase(state: AgentState) -> AgentState:
    """Final completion phase"""
    logger.info("Mission completed successfully")
    
    state["mission_phase"] = "completion"
    state["last_activity"].update({agent: "completed" for agent in ["scout", "strategist", "builder"]})
    
    return state

def build_agent_flow():
    """Build simple linear flow - each phase executes once then exits"""
    
    # Create state graph - NO CHECKPOINTING AT ALL
    graph = StateGraph(AgentState)
    
    # Add phase nodes
    graph.add_node("initialization_phase", initialization_phase)
    graph.add_node("exploration_phase", exploration_phase)
    graph.add_node("analysis_phase", analysis_phase)
    graph.add_node("construction_phase", construction_phase)
    graph.add_node("completion_phase", completion_phase)
    
    # Set entry point
    graph.set_entry_point("initialization_phase")
    
    # Simple linear flow - each phase goes to END after executing
    # The simulation.py will handle calling the flow again for the next step
    graph.add_edge("initialization_phase", END)
    graph.add_edge("exploration_phase", END)
    graph.add_edge("analysis_phase", END)
    graph.add_edge("construction_phase", END)
    graph.add_edge("completion_phase", END)
    
    logger.info("Compiling simple linear LangGraph flow")
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
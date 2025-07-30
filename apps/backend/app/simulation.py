import logging
from typing import Dict, List, Set
from app.env.grid import Grid
from app.agents.builder import BuilderAgent
from app.agents.scout import ScoutAgent
from app.agents.strategist import StrategistAgent
from app.langgraph.agent_flow import build_agent_flow, AgentState
from app.tools.message import Message

logger = logging.getLogger(__name__)

class SimulationGoals:
    """Define clear objectives for the simulation"""
    
    EXPLORATION_TARGET = 0.8  # Explore 80% of the grid
    BUILDING_TARGET = 5       # Build 5 structures
    MAX_STEPS = 50           # Complete goals within 50 steps
    
    @staticmethod
    def get_current_objectives(step_count: int, mission_phase: str) -> List[str]:
        """Return current objectives based on simulation state and phase"""
        if mission_phase == "initialization":
            return [
                "🎯 Initialize all agents and establish communication",
                "🎯 Begin systematic grid exploration",
                "🎯 Set up coordination protocols"
            ]
        elif mission_phase == "exploration":
            return [
                "🎯 Scout should systematically explore the grid",
                "🎯 Map terrain and identify key locations",
                "🎯 Report findings to strategist for analysis"
            ]
        elif mission_phase == "analysis":
            return [
                "🎯 Strategist should analyze exploration data",
                "🎯 Identify optimal building locations",
                "🎯 Create strategic construction plan"
            ]
        elif mission_phase == "construction":
            return [
                "🎯 Builder should execute construction orders",
                "🎯 Coordinate with strategist for optimal placement",
                "🎯 Progress toward building target completion"
            ]
        elif mission_phase == "optimization":
            return [
                "🎯 Optimize existing structures and placement",
                "🎯 Fine-tune agent coordination",
                "🎯 Prepare for mission completion"
            ]
        else:
            return [
                "🎯 Mission objectives complete",
                "🎯 All targets achieved successfully"
            ]

class Simulation:
    def __init__(self, width: int = 6, height: int = 5):
        self.grid = Grid(width, height)
        
        # Track exploration properly - this will sync with scout's visited_cells
        self.visited_cells: Set[tuple[int, int]] = set()
        
        # self.agents = {
        #     "scout": ScoutAgent("scout", self.grid),
        #     "strategist": StrategistAgent("strategist", self.grid),
        #     "builder": BuilderAgent("builder", self.grid),
        # }

        # # Place agents in starting positions with better spacing
        # success = []
        # success.append(self.grid.place_agent("scout", (0, 0)))
        # success.append(self.grid.place_agent("strategist", (1, 0)))
        # success.append(self.grid.place_agent("builder", (2, 0)))
        
        # # Mark starting positions as visited
        # self.visited_cells.add((0, 0))
        # self.visited_cells.add((1, 0))
        # self.visited_cells.add((2, 0))
        
        # # Also mark them in the scout's visited cells
        # self.agents["scout"].visited_cells.update(self.visited_cells)
        
        # if not all(success):
        #     logger.warning("Some agents could not be placed in initial positions")
        # Initialize agents
        self.agents = {
            "scout": ScoutAgent("scout", self.grid),
            "strategist": StrategistAgent("strategist", self.grid),
            "builder": BuilderAgent("builder", self.grid),
        }

        # FIX: Ensure all agents are properly placed
        placements = [
            ("scout", (0, 0)),
            ("strategist", (1, 0)), 
            ("builder", (2, 0))  # Make sure builder has a position!
        ]
        
        for agent_id, position in placements:
            success = self.grid.place_agent(agent_id, position)
            if not success:
                logger.error(f"Failed to place {agent_id} at {position}")
                # Try alternative position
                for x in range(width):
                    for y in range(height):
                        if self.grid.is_empty(x, y):
                            success = self.grid.place_agent(agent_id, (x, y))
                            if success:
                                logger.info(f"Placed {agent_id} at alternative position ({x}, {y})")
                                break
                    if success:
                        break
        
        # Verify all agents have positions
        for agent_id in self.agents:
            pos = self.grid.get_agent_position(agent_id)
            if pos is None:
                logger.error(f"CRITICAL: {agent_id} has no position after initialization!")

        # Initialize enhanced conditional flow
        self.flow = build_agent_flow()
        
        # Enhanced state with conditional logic support
        self.state = {
            "agents": self.agents,
            "messages": [],
            "grid": self.grid,
            "logs": [],
            "step_count": 0,
            "errors": [],
            "goals": SimulationGoals(),
            "exploration_progress": 0.0,
            "buildings_built": 0,
            "mission_status": "ACTIVE",
            "mission_phase": "initialization",
            "active_threats": 0,
            "resource_constraints": False,
            "coordination_needed": False,
            "emergency_mode": False,
            "strategic_plan_ready": False,
            "last_activity": {"scout": "none", "strategist": "none", "builder": "none"},
            "phase_transitions": [],
            "coordination_events": [],
            "error_recovery_attempts": 0,
            "performance_metrics": {},
            "parallel_execution_enabled": True,
            "shared_state": None,
            "coordination_manager": None,
            "agent_states": {},
            "previous_messages": []  # Track previous messages
        }
        
        # Add initial mission briefing
        initial_briefing = [
            "🚀 MISSION BRIEFING: Enhanced Multi-Agent Grid Development",
            "📋 Scout: Systematically explore and report findings",
            "📋 Strategist: Analyze reports and plan optimal building locations", 
            "📋 Builder: Construct buildings at strategically chosen locations",
            f"🎯 TARGET: Explore {SimulationGoals.EXPLORATION_TARGET*100}% of grid and build {SimulationGoals.BUILDING_TARGET} structures",
            "🔄 ENHANCED: Conditional flows and adaptive coordination enabled"
        ]
        self.state["logs"].extend(initial_briefing)
        
        logger.info(f"Enhanced conditional simulation initialized with {len(self.agents)} agents on {width}x{height} grid")

    def step(self) -> dict:
        """Execute one simulation step with enhanced conditional logic."""
        try:
            self.state["step_count"] += 1
            step_num = self.state["step_count"]
            
            logger.info(f"Starting enhanced mission step {step_num} - Phase: {self.state['mission_phase']}")
            
            # Update visited cells before processing
            self._sync_exploration_data()
            
            # Check for phase transitions and emergencies
            self._check_emergency_conditions()
            
            # Check mission status
            if step_num > SimulationGoals.MAX_STEPS:
                self.state["mission_status"] = "TIMEOUT"
                self.state["logs"].append(f"🚨 MISSION TIMEOUT: Exceeded {SimulationGoals.MAX_STEPS} steps")

            # Prepare enhanced state for the conditional flow
            flow_state: AgentState = {
                "grid": self.grid,
                "messages": self.state["messages"],
                "step_count": step_num,
                "mission_phase": self.state["mission_phase"],
                "objectives": SimulationGoals.get_current_objectives(step_num, self.state["mission_phase"]),
                "exploration_progress": self._calculate_exploration_progress(),
                "buildings_built": self._count_buildings(),
                "active_threats": self.state["active_threats"],
                "resource_constraints": self.state["resource_constraints"],
                "coordination_needed": self.state["coordination_needed"],
                "emergency_mode": self.state["emergency_mode"],
                "last_activity": self.state["last_activity"].copy(),
                "strategic_plan_ready": self.state["strategic_plan_ready"],
                "shared_state": self.state["shared_state"],
                "coordination_manager": self.state["coordination_manager"],
                "agent_states": self.state["agent_states"],
                "error_recovery_attempts": self.state["error_recovery_attempts"],
                "performance_metrics": self.state["performance_metrics"],
                "parallel_execution_enabled": self.state["parallel_execution_enabled"]
            }

            logger.info(f"Flow state prepared: Phase={flow_state['mission_phase']}, "
                    f"Exploration={flow_state['exploration_progress']:.1%}, "
                    f"Buildings={flow_state['buildings_built']}, "
                    f"Emergency={flow_state['emergency_mode']}")

            # Store previous phase for comparison
            previous_phase = self.state["mission_phase"]
            
            # Run the enhanced conditional flow - it will execute the current phase
            result_state = self.flow.invoke(flow_state)

            # Update our state with the results
            self.state["messages"] = result_state["messages"]
            self.state["grid"] = result_state["grid"]
            
            # IMPORTANT: Preserve phase transitions from the flow
            if result_state["mission_phase"] != previous_phase:
                logger.info(f"Phase transition detected: {previous_phase} → {result_state['mission_phase']}")
                self.state["phase_transitions"].append({
                    "step": step_num,
                    "from": previous_phase,
                    "to": result_state["mission_phase"]
                })
            
            self.state["mission_phase"] = result_state["mission_phase"]
            self.state["coordination_needed"] = result_state["coordination_needed"]
            self.state["emergency_mode"] = result_state["emergency_mode"]
            self.state["last_activity"] = result_state["last_activity"]
            self.state["strategic_plan_ready"] = result_state.get("strategic_plan_ready", False)
            self.state["error_recovery_attempts"] = result_state.get("error_recovery_attempts", 0)
            self.state["performance_metrics"] = result_state.get("performance_metrics", {})
            self.state["shared_state"] = result_state.get("shared_state")
            self.state["coordination_manager"] = result_state.get("coordination_manager")
            self.state["agent_states"] = result_state.get("agent_states", {})
            
            # Sync exploration data after agent movements
            self._sync_exploration_data()
            
            # Process new messages and extract meaningful actions
            new_logs = []
            
            # Get only the new messages from this step
            step_messages = []
            prev_msg_count = len(self.state.get("previous_messages", []))
            current_msg_count = len(result_state["messages"])
            
            if current_msg_count > prev_msg_count:
                step_messages = result_state["messages"][prev_msg_count:]
                
                for msg in step_messages:
                    if hasattr(msg, 'content') and msg.content:
                        log_entry = f"[Step {step_num}] {msg.sender}: {msg.content}"
                        new_logs.append(log_entry)
                        logger.info(f"New agent message: {msg.sender} - {msg.content}")
            
            # Store previous messages for next step comparison
            self.state["previous_messages"] = result_state["messages"].copy()
            
            # Add enhanced step summary with phase and conditional info
            exploration_progress = self._calculate_exploration_progress()
            buildings_built = self._count_buildings()
            
            step_summary = (f"📊 Step {step_num} Summary: Phase={self.state['mission_phase']}, "
                          f"{exploration_progress:.0%} explored, {buildings_built} buildings built")
            new_logs.append(step_summary)
            
            # Log phase transitions
            if self.state["mission_phase"] != previous_phase:
                transition_log = f"🔄 PHASE TRANSITION: {previous_phase} → {self.state['mission_phase']}"
                new_logs.append(transition_log)
            
            # Check for goal completion
            if exploration_progress >= SimulationGoals.EXPLORATION_TARGET and buildings_built >= SimulationGoals.BUILDING_TARGET:
                self.state["mission_status"] = "SUCCESS"
                self.state["mission_phase"] = "completion"
                new_logs.append("🎉 MISSION ACCOMPLISHED: All objectives completed!")
            elif buildings_built >= SimulationGoals.BUILDING_TARGET:
                self.state["mission_status"] = "BUILDING_TARGET_REACHED"
                new_logs.append(f"🏗️ BUILDING TARGET REACHED: {buildings_built}/{SimulationGoals.BUILDING_TARGET} buildings completed!")
            
            self.state["logs"].extend(new_logs)
            self.state["exploration_progress"] = exploration_progress
            self.state["buildings_built"] = buildings_built
            
            # Limit log history to prevent memory issues
            if len(self.state["logs"]) > 100:
                self.state["logs"] = self.state["logs"][-100:]
            
            # Force sync agent status data to ensure frontend gets updated info
            agent_status = self._get_fresh_agent_status()
            
            logger.info(f"Enhanced step {step_num} completed - Phase: {self.state['mission_phase']}, "
                       f"Progress: {exploration_progress:.0%} explored, {buildings_built} buildings")
            
            return {
                "logs": self.state["logs"],
                "grid": self.grid.serialize(),
                "agents": agent_status,
                "step_count": step_num,
                "mission_status": self.state["mission_status"],
                "mission_phase": self.state["mission_phase"],
                "exploration_progress": exploration_progress,
                "buildings_built": buildings_built,
                "current_objectives": SimulationGoals.get_current_objectives(step_num, self.state["mission_phase"]),
                "visited_cells": len(self.visited_cells),
                "coordination_needed": self.state["coordination_needed"],
                "emergency_mode": self.state["emergency_mode"],
                "phase_transitions": self.state["phase_transitions"],
                "coordination_events": self.state["coordination_events"],
                "status": "success"
            }
            
        except Exception as e:
            error_msg = f"Error in enhanced mission step {self.state['step_count']}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            self.state["errors"].append(error_msg)
            self.state["logs"].append(f"[ERROR] {error_msg}")
            
            return {
                "logs": self.state["logs"],
                "grid": self.grid.serialize(),
                "agents": self._get_fresh_agent_status(),
                "step_count": self.state["step_count"],
                "mission_status": "ERROR",
                "mission_phase": self.state["mission_phase"],
                "status": "error",
                "error": error_msg
            }

    def _check_emergency_conditions(self):
        """Check for conditions that trigger emergency mode"""
        # Example emergency conditions
        if self.state["step_count"] > 30 and self.state["buildings_built"] == 0:
            self.state["emergency_mode"] = True
            self.state["logs"].append("🚨 EMERGENCY: No buildings constructed after 30 steps")
        
        # Reset emergency mode if conditions improve
        if self.state["emergency_mode"] and self.state["buildings_built"] > 0:
            self.state["emergency_mode"] = False
            self.state["logs"].append("✅ EMERGENCY RESOLVED: Construction progress detected")

    def _sync_exploration_data(self):
        """Sync exploration data between simulation and scout agent"""
        # Get scout's visited cells
        scout = self.agents.get("scout")
        if scout and hasattr(scout, 'visited_cells'):
            # Update simulation's visited cells with scout's data
            self.visited_cells.update(scout.visited_cells)
            
            # Also add current positions of all agents
            for agent_id, agent in self.agents.items():
                position = self.grid.get_agent_position(agent_id)
                if position:
                    self.visited_cells.add(position)
                    # Update scout's visited cells too
                    scout.visited_cells.add(position)
        
        logger.debug(f"Synced exploration: Scout has {len(scout.visited_cells) if scout else 0} cells, "
                    f"Simulation tracks {len(self.visited_cells)} cells")

    def _get_fresh_agent_status(self) -> dict:
        """Get fresh agent status with enhanced conditional information."""
        try:
            status = {}
            for agent_id, agent in self.agents.items():
                # Get the agent's current status
                agent_status = agent.get_status()
                
                # Add current position (force refresh)
                current_position = self.grid.get_agent_position(agent_id)
                if current_position:
                    agent_status["position"] = current_position
                
                # Add enhanced mission context and conditional state info
                agent_status["mission_phase"] = self.state["mission_phase"]
                agent_status["last_activity"] = self.state["last_activity"].get(agent_id, "none")
                agent_status["coordination_status"] = "needed" if self.state["coordination_needed"] else "active"
                
                if agent_id == "scout":
                    agent_status["mission_role"] = "Explorer & Intelligence Gatherer"
                    # Force refresh exploration data
                    if hasattr(agent, 'visited_cells'):
                        agent_status["cells_visited"] = len(agent.visited_cells)
                        agent_status["exploration_percentage"] = (len(agent.visited_cells) / (self.grid.width * self.grid.height)) * 100
                        agent_status["exploration_target"] = SimulationGoals.EXPLORATION_TARGET * 100
                    
                elif agent_id == "strategist":
                    agent_status["mission_role"] = "Tactical Coordinator & Planner"
                    # Force refresh strategist data
                    if hasattr(agent, 'scout_reports'):
                        agent_status["scout_reports_received"] = len(agent.scout_reports)
                    if hasattr(agent, 'suggested_locations'):
                        agent_status["build_orders_issued"] = len(agent.suggested_locations)
                    if hasattr(agent, 'analysis_count'):
                        agent_status["analysis_cycles"] = agent.analysis_count
                    agent_status["strategic_plan_ready"] = self.state["strategic_plan_ready"]
                    if hasattr(agent, 'BUILD_TARGET'):
                        agent_status["building_target"] = agent.BUILD_TARGET
                        agent_status["buildings_completed"] = self._count_buildings()
                
                elif agent_id == "builder":
                    agent_status["mission_role"] = "Construction & Infrastructure"
                    # Force refresh builder data
                    if hasattr(agent, 'buildings_completed'):
                        agent_status["buildings_completed"] = agent.buildings_completed
                    if hasattr(agent, 'last_built_location'):
                        agent_status["last_built_location"] = agent.last_built_location
                    if hasattr(agent, 'processed_messages'):
                        agent_status["processed_messages_count"] = len(agent.processed_messages)
                    if hasattr(agent, 'current_target'):
                        agent_status["current_target"] = agent.current_target
                    if hasattr(agent, 'movement_path'):
                        agent_status["movement_steps_remaining"] = len(agent.movement_path)
                    agent_status["construction_target"] = SimulationGoals.BUILDING_TARGET
                
                status[agent_id] = agent_status
                logger.debug(f"Enhanced agent {agent_id} status: phase={self.state['mission_phase']}, "
                           f"activity={self.state['last_activity'].get(agent_id, 'none')}")
            
            return status
        except Exception as e:
            logger.error(f"Error getting fresh agent status: {e}")
            return {}

    def _calculate_exploration_progress(self) -> float:
        """Calculate what percentage of the grid has been explored."""
        total_cells = self.grid.width * self.grid.height
        explored_cells = len(self.visited_cells)
        progress = min(explored_cells / total_cells, 1.0)
        logger.debug(f"Exploration progress: {explored_cells}/{total_cells} = {progress:.2%}")
        return progress

    def _count_buildings(self) -> int:
        """Count the number of buildings constructed."""
        building_count = 0
        for cell in self.grid.grid.values():
            if cell.structure and cell.structure != "scanned":
                building_count += 1
        logger.debug(f"Buildings count: {building_count}")
        return building_count

    def get_grid_state(self) -> dict:
        """Get current grid state with enhanced progress metrics."""
        base_state = self.grid.serialize()
        base_state["exploration_progress"] = self._calculate_exploration_progress()
        base_state["buildings_built"] = self._count_buildings()
        base_state["mission_status"] = self.state.get("mission_status", "ACTIVE")
        base_state["mission_phase"] = self.state.get("mission_phase", "initialization")
        base_state["visited_cells"] = len(self.visited_cells)
        base_state["coordination_needed"] = self.state.get("coordination_needed", False)
        base_state["emergency_mode"] = self.state.get("emergency_mode", False)
        base_state["strategic_plan_ready"] = self.state.get("strategic_plan_ready", False)
        return base_state

    def get_logs(self) -> list[str]:
        """Get simulation logs."""
        return self.state["logs"]

    def get_agent_status(self) -> dict:
        """Get status of all agents with enhanced mission context."""
        return self._get_fresh_agent_status()
    
    def get_conditional_metrics(self) -> dict:
        """Get metrics specific to conditional flow behavior."""
        return {
            "mission_phase": self.state["mission_phase"],
            "phase_transitions": len(self.state["phase_transitions"]),
            "coordination_events": len(self.state["coordination_events"]),
            "emergency_activations": sum(1 for log in self.state["logs"] if "EMERGENCY" in log),
            "last_activity": self.state["last_activity"],
            "coordination_needed": self.state["coordination_needed"],
            "strategic_plan_ready": self.state["strategic_plan_ready"],
            "active_threats": self.state["active_threats"],
            "resource_constraints": self.state["resource_constraints"]
        }
import logging
from typing import Dict, List, Set
from app.env.grid import Grid
from app.agents.builder import BuilderAgent
from app.agents.scout import ScoutAgent
from app.agents.strategist import StrategistAgent
from app.langgraph.agent_flow import build_agent_flow
from app.tools.message import Message

logger = logging.getLogger(__name__)

class SimulationGoals:
    """Define clear objectives for the simulation"""
    
    EXPLORATION_TARGET = 0.8  # Explore 80% of the grid
    BUILDING_TARGET = 5       # Build 5 structures
    MAX_STEPS = 50           # Complete goals within 50 steps
    
    @staticmethod
    def get_current_objectives(step_count: int) -> List[str]:
        """Return current objectives based on simulation state"""
        if step_count < 10:
            return [
                "🎯 Primary Goal: Scout should explore and map the grid",
                "🎯 Secondary Goal: Strategist should analyze scout reports", 
                "🎯 Tertiary Goal: Builder should wait for building instructions"
            ]
        elif step_count < 30:
            return [
                "🎯 Primary Goal: Complete grid exploration",
                "🎯 Secondary Goal: Strategist should identify optimal building locations",
                "🎯 Tertiary Goal: Begin strategic construction"
            ]
        else:
            return [
                "🎯 Primary Goal: Complete remaining buildings",
                "🎯 Secondary Goal: Optimize existing structures",
                "🎯 Tertiary Goal: Prepare mission summary"
            ]

class Simulation:
    def __init__(self, width: int = 12, height: int = 5):  # Default to match your grid
        self.grid = Grid(width, height)
        
        # Track exploration properly - this will sync with scout's visited_cells
        self.visited_cells: Set[tuple[int, int]] = set()
        
        self.agents = {
            "scout": ScoutAgent("scout", self.grid),
            "strategist": StrategistAgent("strategist", self.grid),
            "builder": BuilderAgent("builder", self.grid),
        }

        # Place agents in starting positions with better spacing
        success = []
        success.append(self.grid.place_agent("scout", (0, 0)))
        success.append(self.grid.place_agent("strategist", (1, 0)))
        success.append(self.grid.place_agent("builder", (2, 0)))
        
        # Mark starting positions as visited
        self.visited_cells.add((0, 0))
        self.visited_cells.add((1, 0))
        self.visited_cells.add((2, 0))
        
        # Also mark them in the scout's visited cells
        self.agents["scout"].visited_cells.update(self.visited_cells)
        
        if not all(success):
            logger.warning("Some agents could not be placed in initial positions")

        self.flow = build_agent_flow()
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
            "mission_status": "ACTIVE"
        }
        
        # Add initial mission briefing
        initial_briefing = [
            "🚀 MISSION BRIEFING: Multi-Agent Grid Development",
            "📋 Scout: Systematically explore and report findings",
            "📋 Strategist: Analyze reports and plan optimal building locations", 
            "📋 Builder: Construct buildings at strategically chosen locations",
            f"🎯 TARGET: Explore {SimulationGoals.EXPLORATION_TARGET*100}% of grid and build {SimulationGoals.BUILDING_TARGET} structures"
        ]
        self.state["logs"].extend(initial_briefing)
        
        logger.info(f"Mission-oriented simulation initialized with {len(self.agents)} agents on {width}x{height} grid")

    def step(self) -> dict:
        """Execute one simulation step with goal tracking."""
        try:
            self.state["step_count"] += 1
            step_num = self.state["step_count"]
            
            logger.info(f"Starting mission step {step_num}")
            
            # Update visited cells before processing
            self._sync_exploration_data()
            
            # Check mission status
            if step_num > SimulationGoals.MAX_STEPS:
                self.state["mission_status"] = "TIMEOUT"
                self.state["logs"].append(f"🚨 MISSION TIMEOUT: Exceeded {SimulationGoals.MAX_STEPS} steps")
            
            # Add current objectives to context
            current_objectives = SimulationGoals.get_current_objectives(step_num)
            
            # Prepare enhanced state for the flow
            flow_state = {
                "grid": self.grid,
                "messages": self.state["messages"],
                "step_count": step_num,
                "objectives": current_objectives,
                "exploration_progress": self._calculate_exploration_progress(),
                "buildings_built": self._count_buildings()
            }
            
            # Run the agent flow (each agent acts once)
            result_state = self.flow.invoke(flow_state)

            # Update our state with the results
            self.state["messages"] = result_state["messages"]
            self.state["grid"] = result_state["grid"]
            
            # Sync exploration data after agent movements
            self._sync_exploration_data()
            
            # Process new messages and extract meaningful actions
            new_logs = []
            
            # Get only the new messages from this step
            step_messages = []
            if len(result_state["messages"]) > len(self.state.get("previous_messages", [])):
                start_idx = len(self.state.get("previous_messages", []))
                step_messages = result_state["messages"][start_idx:]
            
            for msg in step_messages:
                if hasattr(msg, 'content') and msg.content:
                    log_entry = f"[Step {step_num}] {msg.content}"
                    new_logs.append(log_entry)
                    logger.debug(f"Agent message: {msg.content}")
            
            # Store previous messages for next step comparison
            self.state["previous_messages"] = result_state["messages"].copy()
            
            # Add step summary with progress tracking
            exploration_progress = self._calculate_exploration_progress()
            buildings_built = self._count_buildings()
            
            step_summary = f"📊 Step {step_num} Summary: {exploration_progress:.0%} explored, {buildings_built} buildings built"
            new_logs.append(step_summary)
            
            # Check for goal completion
            if exploration_progress >= SimulationGoals.EXPLORATION_TARGET and buildings_built >= SimulationGoals.BUILDING_TARGET:
                self.state["mission_status"] = "SUCCESS"
                new_logs.append("🎉 MISSION ACCOMPLISHED: All objectives completed!")
            elif buildings_built >= SimulationGoals.BUILDING_TARGET:
                self.state["mission_status"] = "BUILDING_TARGET_REACHED"
                new_logs.append(f"🏗️ BUILDING TARGET REACHED: {buildings_built}/{SimulationGoals.BUILDING_TARGET} buildings completed!")
            
            # Add progress update every 5 steps
            if step_num % 5 == 0:
                progress_update = f"🔄 Progress Update: {current_objectives[0]}"
                new_logs.append(progress_update)
            
            self.state["logs"].extend(new_logs)
            self.state["exploration_progress"] = exploration_progress
            self.state["buildings_built"] = buildings_built
            
            # Limit log history to prevent memory issues
            if len(self.state["logs"]) > 100:
                self.state["logs"] = self.state["logs"][-100:]
            
            # Force sync agent status data to ensure frontend gets updated info
            agent_status = self._get_fresh_agent_status()
            
            logger.info(f"Step {step_num} completed - Progress: {exploration_progress:.0%} explored, {buildings_built} buildings")
            logger.info(f"Agent status sync: Scout {agent_status.get('scout', {}).get('cells_visited', 0)} cells, Builder {agent_status.get('builder', {}).get('buildings_completed', 0)} buildings")
            
            return {
                "logs": self.state["logs"],
                "grid": self.grid.serialize(),
                "agents": agent_status,  # Use fresh status
                "step_count": step_num,
                "mission_status": self.state["mission_status"],
                "exploration_progress": exploration_progress,
                "buildings_built": buildings_built,
                "current_objectives": current_objectives,
                "visited_cells": len(self.visited_cells),
                "status": "success"
            }
            
        except Exception as e:
            error_msg = f"Error in mission step {self.state['step_count']}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            self.state["errors"].append(error_msg)
            self.state["logs"].append(f"[ERROR] {error_msg}")
            
            return {
                "logs": self.state["logs"],
                "grid": self.grid.serialize(),
                "agents": self._get_fresh_agent_status(),
                "step_count": self.state["step_count"],
                "mission_status": "ERROR",
                "status": "error",
                "error": error_msg
            }

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
        
        logger.debug(f"Synced exploration: Scout has {len(scout.visited_cells) if scout else 0} cells, Simulation tracks {len(self.visited_cells)} cells")

    def _get_fresh_agent_status(self) -> dict:
        """Get fresh agent status with forced updates."""
        try:
            status = {}
            for agent_id, agent in self.agents.items():
                # Get the agent's current status
                agent_status = agent.get_status()
                
                # Add current position (force refresh)
                current_position = self.grid.get_agent_position(agent_id)
                if current_position:
                    agent_status["position"] = current_position
                
                # Add mission-specific context and ensure data is fresh
                if agent_id == "scout":
                    agent_status["mission_role"] = "Explorer & Intelligence Gatherer"
                    # Force refresh exploration data
                    if hasattr(agent, 'visited_cells'):
                        agent_status["cells_visited"] = len(agent.visited_cells)
                        agent_status["exploration_percentage"] = (len(agent.visited_cells) / (self.grid.width * self.grid.height)) * 100
                    
                elif agent_id == "strategist":
                    agent_status["mission_role"] = "Tactical Coordinator & Planner"
                    # Force refresh strategist data
                    if hasattr(agent, 'scout_reports'):
                        agent_status["scout_reports_received"] = len(agent.scout_reports)
                    if hasattr(agent, 'suggested_locations'):
                        agent_status["build_orders_issued"] = len(agent.suggested_locations)
                    if hasattr(agent, 'analysis_count'):
                        agent_status["analysis_cycles"] = agent.analysis_count
                
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
                
                status[agent_id] = agent_status
                logger.debug(f"Agent {agent_id} status refreshed: {agent_status.get('cells_visited', 'N/A')} cells, {agent_status.get('buildings_completed', 'N/A')} buildings")
            
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
        """Get current grid state with progress metrics."""
        base_state = self.grid.serialize()
        base_state["exploration_progress"] = self._calculate_exploration_progress()
        base_state["buildings_built"] = self._count_buildings()
        base_state["mission_status"] = self.state.get("mission_status", "ACTIVE")
        base_state["visited_cells"] = len(self.visited_cells)
        return base_state

    def get_logs(self) -> list[str]:
        """Get simulation logs."""
        return self.state["logs"]

    def get_agent_status(self) -> dict:
        """Get status of all agents with mission context."""
        return self._get_fresh_agent_status()
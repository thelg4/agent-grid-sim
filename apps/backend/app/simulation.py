# import logging
# from app.env.grid import Grid
# from app.agents.builder import BuilderAgent
# from app.agents.scout import ScoutAgent
# from app.agents.strategist import StrategistAgent
# from app.langgraph.agent_flow import build_agent_flow
# from app.tools.message import Message

# logger = logging.getLogger(__name__)

# class Simulation:
#     def __init__(self, width: int = 6, height: int = 5):
#         self.grid = Grid(width, height)
#         self.agents = {
#             "builder": BuilderAgent("builder", self.grid),
#             "scout": ScoutAgent("scout", self.grid),
#             "strategist": StrategistAgent("strategist", self.grid),
#         }

#         # Place agents in starting positions
#         success = []
#         success.append(self.grid.place_agent("builder", (0, 0)))
#         success.append(self.grid.place_agent("strategist", (1, 0)))
#         success.append(self.grid.place_agent("scout", (2, 0)))
        
#         if not all(success):
#             logger.warning("Some agents could not be placed in initial positions")

#         self.flow = build_agent_flow()
#         self.state = {
#             "agents": self.agents,
#             "messages": [],
#             "grid": self.grid,
#             "logs": [],
#             "step_count": 0,
#             "errors": []
#         }
        
#         logger.info(f"Simulation initialized with {len(self.agents)} agents on {width}x{height} grid")

#     def step(self) -> dict:
#         """Execute one simulation step with error handling."""
#         try:
#             self.state["step_count"] += 1
#             step_num = self.state["step_count"]
            
#             logger.info(f"Starting simulation step {step_num}")
            
#             # Prepare state for the flow (only grid and messages)
#             flow_state = {
#                 "grid": self.grid,
#                 "messages": self.state["messages"]
#             }
            
#             # Run the agent flow
#             result_state = self.flow.invoke(flow_state)
            
#             # Update our state with the results
#             self.state["messages"] = result_state["messages"]
#             self.state["grid"] = result_state["grid"]
            
#             # Convert messages to logs for the frontend
#             new_logs = []
#             for msg in result_state["messages"]:
#                 if hasattr(msg, 'content') and msg.content:
#                     log_entry = f"[Step {step_num}] {msg.content}"
#                     new_logs.append(log_entry)
#                     logger.debug(f"Agent message: {msg.content}")
            
#             self.state["logs"].extend(new_logs)
            
#             # Limit log history to prevent memory issues
#             if len(self.state["logs"]) > 100:
#                 self.state["logs"] = self.state["logs"][-100:]
            
#             logger.info(f"Step {step_num} completed successfully with {len(new_logs)} new messages")
            
#             return {
#                 "logs": self.state["logs"],
#                 "grid": self.grid.serialize(),
#                 "agents": {
#                     agent_id: agent.get_status()
#                     for agent_id, agent in self.agents.items()
#                 },
#                 "step_count": step_num,
#                 "status": "success"
#             }
            
#         except Exception as e:
#             error_msg = f"Error in simulation step {self.state['step_count']}: {str(e)}"
#             logger.error(error_msg, exc_info=True)
            
#             self.state["errors"].append(error_msg)
#             self.state["logs"].append(f"[ERROR] {error_msg}")
            
#             # Return current state even if step failed
#             return {
#                 "logs": self.state["logs"],
#                 "grid": self.grid.serialize(),
#                 "agents": {
#                     agent_id: agent.get_status()
#                     for agent_id, agent in self.agents.items()
#                 },
#                 "step_count": self.state["step_count"],
#                 "status": "error",
#                 "error": error_msg
#             }

#     def get_grid_state(self) -> dict:
#         """Get current grid state."""
#         return self.grid.serialize()

#     def get_logs(self) -> list[str]:
#         """Get simulation logs."""
#         return self.state["logs"]

#     def get_agent_status(self) -> dict:
#         """Get status of all agents."""
#         try:
#             return {
#                 agent_id: agent.get_status()
#                 for agent_id, agent in self.agents.items()
#             }
#         except Exception as e:
#             logger.error(f"Error getting agent status: {e}")
#             return {}

# app/simulation.py
import logging
from typing import Dict, List
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
    def __init__(self, width: int = 6, height: int = 5):
        self.grid = Grid(width, height)
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
            
            # Run the agent flow
            result_state = self.flow.invoke(flow_state)
            
            # Update our state with the results
            self.state["messages"] = result_state["messages"]
            self.state["grid"] = result_state["grid"]
            
            # Process new messages and extract meaningful actions
            new_logs = []
            agent_actions = {"scout": [], "strategist": [], "builder": []}
            
            for msg in result_state["messages"]:
                if hasattr(msg, 'content') and msg.content:
                    # Categorize messages by agent
                    sender = getattr(msg, 'sender', 'unknown')
                    if sender in agent_actions:
                        agent_actions[sender].append(msg.content)
                    
                    log_entry = f"[Step {step_num}] {msg.content}"
                    new_logs.append(log_entry)
                    logger.debug(f"Agent message: {msg.content}")
            
            # Add step summary with progress tracking
            exploration_progress = self._calculate_exploration_progress()
            buildings_built = self._count_buildings()
            
            step_summary = f"📊 Step {step_num} Summary: {exploration_progress:.0%} explored, {buildings_built} buildings built"
            new_logs.append(step_summary)
            
            # Check for goal completion
            if exploration_progress >= SimulationGoals.EXPLORATION_TARGET and buildings_built >= SimulationGoals.BUILDING_TARGET:
                self.state["mission_status"] = "SUCCESS"
                new_logs.append("🎉 MISSION ACCOMPLISHED: All objectives completed!")
            
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
            
            logger.info(f"Step {step_num} completed - Progress: {exploration_progress:.0%} explored, {buildings_built} buildings")
            
            return {
                "logs": self.state["logs"],
                "grid": self.grid.serialize(),
                "agents": {
                    agent_id: agent.get_status()
                    for agent_id, agent in self.agents.items()
                },
                "step_count": step_num,
                "mission_status": self.state["mission_status"],
                "exploration_progress": exploration_progress,
                "buildings_built": buildings_built,
                "current_objectives": current_objectives,
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
                "agents": {
                    agent_id: agent.get_status()
                    for agent_id, agent in self.agents.items()
                },
                "step_count": self.state["step_count"],
                "mission_status": "ERROR",
                "status": "error",
                "error": error_msg
            }

    def _calculate_exploration_progress(self) -> float:
        """Calculate what percentage of the grid has been explored by agents."""
        total_cells = self.grid.width * self.grid.height
        explored_cells = 0
        
        # Count cells that have been visited by agents or have structures
        for (x, y), cell in self.grid.grid.items():
            if cell.occupied_by or cell.structure:
                explored_cells += 1
        
        # For demo purposes, also count cells adjacent to visited cells as "observed"
        observed_cells = set()
        for (x, y), cell in self.grid.grid.items():
            if cell.occupied_by:
                # Add adjacent cells as observed
                for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                    nx, ny = x + dx, y + dy
                    if self.grid.is_within_bounds(nx, ny):
                        observed_cells.add((nx, ny))
        
        total_explored = min(explored_cells + len(observed_cells), total_cells)
        return total_explored / total_cells

    def _count_buildings(self) -> int:
        """Count the number of buildings constructed."""
        building_count = 0
        for cell in self.grid.grid.values():
            if cell.structure and cell.structure != "scanned":
                building_count += 1
        return building_count

    def get_grid_state(self) -> dict:
        """Get current grid state with progress metrics."""
        base_state = self.grid.serialize()
        base_state["exploration_progress"] = self._calculate_exploration_progress()
        base_state["buildings_built"] = self._count_buildings()
        base_state["mission_status"] = self.state.get("mission_status", "ACTIVE")
        return base_state

    def get_logs(self) -> list[str]:
        """Get simulation logs."""
        return self.state["logs"]

    def get_agent_status(self) -> dict:
        """Get status of all agents with mission context."""
        try:
            status = {}
            for agent_id, agent in self.agents.items():
                agent_status = agent.get_status()
                # Add mission-specific context
                if agent_id == "scout":
                    agent_status["mission_role"] = "Explorer & Intelligence Gatherer"
                elif agent_id == "strategist":
                    agent_status["mission_role"] = "Tactical Coordinator & Planner"
                elif agent_id == "builder":
                    agent_status["mission_role"] = "Construction & Infrastructure"
                status[agent_id] = agent_status
            return status
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {}
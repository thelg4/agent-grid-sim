# # app/sim/simulation.py

# from app.env.grid import Grid
# from app.agents.builder import BuilderAgent
# from app.agents.scout import ScoutAgent
# from app.agents.strategist import StrategistAgent
# from app.langgraph.agent_flow import build_agent_flow
# from app.tools.message import Message

# class Simulation:
#     def __init__(self, width: int = 6, height: int = 5):
#         self.grid = Grid(width, height)
#         self.agents = {
#             "builder": BuilderAgent("builder", self.grid),
#             "scout": ScoutAgent("scout", self.grid),
#             "strategist": StrategistAgent("strategist", self.grid),
#         }

#         # Place agents in starting positions
#         self.grid.place_agent("builder", (0, 0))
#         self.grid.place_agent("strategist", (1, 0))
#         self.grid.place_agent("scout", (2, 0))

#         self.flow = build_agent_flow()
#         self.state = {
#             "agents": self.agents,
#             "messages": [],
#             "grid": self.grid,
#             "logs": [],
#         }

#     def step(self) -> dict:
#         self.state = self.flow.invoke(self.state)
#         return {
#             "logs": self.state["logs"],
#             "grid": self.grid.to_dict(),
#             "agents": {
#                 agent_id: {
#                     "status": agent.get_status(),
#                     "memory": agent.memory.get_recent()
#                 }
#                 for agent_id, agent in self.agents.items()
#             }
#         }

#     def get_grid_state(self) -> dict:
#         return self.grid.to_dict()

#     def get_logs(self) -> list[str]:
#         return self.state["logs"]

#     def get_agent_status(self) -> dict:
#         return {
#             agent_id: {
#                 "status": agent.get_status(),
#                 "memory": agent.memory.get_recent()
#             }
#             for agent_id, agent in self.agents.items()
#         }

import logging
from app.env.grid import Grid
from app.agents.builder import BuilderAgent
from app.agents.scout import ScoutAgent
from app.agents.strategist import StrategistAgent
from app.langgraph.agent_flow import build_agent_flow
from app.tools.message import Message

logger = logging.getLogger(__name__)

class Simulation:
    def __init__(self, width: int = 6, height: int = 5):
        self.grid = Grid(width, height)
        self.agents = {
            "builder": BuilderAgent("builder", self.grid),
            "scout": ScoutAgent("scout", self.grid),
            "strategist": StrategistAgent("strategist", self.grid),
        }

        # Place agents in starting positions
        success = []
        success.append(self.grid.place_agent("builder", (0, 0)))
        success.append(self.grid.place_agent("strategist", (1, 0)))
        success.append(self.grid.place_agent("scout", (2, 0)))
        
        if not all(success):
            logger.warning("Some agents could not be placed in initial positions")

        self.flow = build_agent_flow()
        self.state = {
            "agents": self.agents,
            "messages": [],
            "grid": self.grid,
            "logs": [],
            "step_count": 0,
            "errors": []
        }
        
        logger.info(f"Simulation initialized with {len(self.agents)} agents on {width}x{height} grid")

    def step(self) -> dict:
        """Execute one simulation step with error handling."""
        try:
            self.state["step_count"] += 1
            step_num = self.state["step_count"]
            
            logger.info(f"Starting simulation step {step_num}")
            
            # Prepare state for the flow (only grid and messages)
            flow_state = {
                "grid": self.grid,
                "messages": self.state["messages"]
            }
            
            # Run the agent flow
            result_state = self.flow.invoke(flow_state)
            
            # Update our state with the results
            self.state["messages"] = result_state["messages"]
            self.state["grid"] = result_state["grid"]
            
            # Convert messages to logs for the frontend
            new_logs = []
            for msg in result_state["messages"]:
                if hasattr(msg, 'content') and msg.content:
                    log_entry = f"[Step {step_num}] {msg.content}"
                    new_logs.append(log_entry)
                    logger.debug(f"Agent message: {msg.content}")
            
            self.state["logs"].extend(new_logs)
            
            # Limit log history to prevent memory issues
            if len(self.state["logs"]) > 100:
                self.state["logs"] = self.state["logs"][-100:]
            
            logger.info(f"Step {step_num} completed successfully with {len(new_logs)} new messages")
            
            return {
                "logs": self.state["logs"],
                "grid": self.grid.serialize(),
                "agents": {
                    agent_id: agent.get_status()
                    for agent_id, agent in self.agents.items()
                },
                "step_count": step_num,
                "status": "success"
            }
            
        except Exception as e:
            error_msg = f"Error in simulation step {self.state['step_count']}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            self.state["errors"].append(error_msg)
            self.state["logs"].append(f"[ERROR] {error_msg}")
            
            # Return current state even if step failed
            return {
                "logs": self.state["logs"],
                "grid": self.grid.serialize(),
                "agents": {
                    agent_id: agent.get_status()
                    for agent_id, agent in self.agents.items()
                },
                "step_count": self.state["step_count"],
                "status": "error",
                "error": error_msg
            }

    def get_grid_state(self) -> dict:
        """Get current grid state."""
        return self.grid.serialize()

    def get_logs(self) -> list[str]:
        """Get simulation logs."""
        return self.state["logs"]

    def get_agent_status(self) -> dict:
        """Get status of all agents."""
        try:
            return {
                agent_id: agent.get_status()
                for agent_id, agent in self.agents.items()
            }
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {}
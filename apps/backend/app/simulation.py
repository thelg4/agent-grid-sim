# app/sim/simulation.py

from app.env.grid import Grid
from app.agents.builder import BuilderAgent
from app.agents.scout import ScoutAgent
from app.agents.strategist import StrategistAgent
from app.langgraph.agent_flow import build_agent_flow
from app.tools.message import Message

class Simulation:
    def __init__(self, width: int = 6, height: int = 5):
        self.grid = Grid(width, height)
        self.agents = {
            "builder": BuilderAgent("builder", self.grid),
            "scout": ScoutAgent("scout", self.grid),
            "strategist": StrategistAgent("strategist", self.grid),
        }

        # Place agents in starting positions
        self.grid.place_agent("builder", (0, 0))
        self.grid.place_agent("strategist", (1, 0))
        self.grid.place_agent("scout", (2, 0))

        self.flow = build_agent_flow()
        self.state = {
            "agents": self.agents,
            "messages": [],
            "grid": self.grid,
            "logs": [],
        }

    def step(self) -> dict:
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
        new_logs = [msg.content for msg in result_state["messages"] if hasattr(msg, 'content')]
        self.state["logs"].extend(new_logs)
        
        return {
            "logs": self.state["logs"],
            "grid": self.grid.serialize(),
            "agents": {
                agent_id: agent.get_status()
                for agent_id, agent in self.agents.items()
            }
        }

    def get_grid_state(self) -> dict:
        return self.grid.serialize()

    def get_logs(self) -> list[str]:
        return self.state["logs"]

    def get_agent_status(self) -> dict:
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self.agents.items()
        }

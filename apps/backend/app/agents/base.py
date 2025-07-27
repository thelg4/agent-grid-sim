from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from app.env.grid import Grid


class BaseAgent(ABC):
    def __init__(self, agent_id: str, role: str, grid: Grid):
        self.agent_id = agent_id
        self.role = role
        self.grid = grid
        self.status = "Idle"
        self.memory: List[str] = []

    @abstractmethod
    def step(self):
        """Perform a single step in the simulation."""
        pass

    def observe(self) -> Dict:
        """Get local view of the grid (stub for now)."""
        return {
            "location": self.grid.find_agent(self.agent_id),
            "surroundings": [],  # could be expanded later
        }

    def send_message(self, message: str):
        self.memory.append(message)

    def get_status(self) -> Dict:
        return {
            "id": self.agent_id,
            "role": self.role,
            "status": self.status,
            "memory": self.memory[-5:],  # return last 5 messages
        }

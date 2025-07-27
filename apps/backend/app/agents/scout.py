import random
from typing import Optional
from .base import BaseAgent
from app.tools.message import Message
from app.env.grid import Grid
from app.env.entities import Structure

class ScoutAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid):
        super().__init__(agent_id, "scout", grid)

    def step(self, messages: list[Message]) -> Optional[Message]:
    
        observation = self.observe()
        location = observation["location"]

        if location:
            x, y = location
            random.shuffle(self.grid.directions)
            for dx, dy in self.grid.directions:
                nx, ny = x + dx, y + dy
                if self.grid.is_within_bounds(nx, ny) and self.grid.is_empty(nx, ny):
                    self.grid.move_agent(self.agent_id, (nx, ny))
                    self.status = f"Moved to ({nx}, {ny})"
                    return self.send_message(f"Scout moved to ({nx}, {ny})")

        self.status = "No available moves"
        return None

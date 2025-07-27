from .base import BaseAgent
from app.tools.message import Message
from app.env.grid import Grid
from app.env.entities import Structure

class StrategistAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid):
        super().__init__(agent_id, "strategist", grid)

    def step(self, messages: list[Message]) -> Message | None:
        """
        Strategist scans grid and suggests build locations.
        """
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if self.grid.is_empty(x, y):
                    suggestion = f"Build at ({x}, {y})"
                    self.status = f"Suggested {suggestion}"
                    return self.send_message(suggestion)
        self.status = "No empty space to suggest"
        return None
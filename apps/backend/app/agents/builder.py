from typing import Union, Optional
from .base import BaseAgent
from app.tools.message import Message
from app.env.grid import Grid
from app.env.entities import Structure

class BuilderAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid):
        super().__init__(agent_id, "builder", grid)
        self.build_target = None

    def step(self, messages: list[Message]) -> Optional[Message]:
        """
        Process incoming messages and take action if any suggest building.
        Returns a message describing the result.
        """
        for message in messages:
            if message.content.startswith("Build at"):
                # Parse coordinates
                try:
                    _, coords = message.content.split("Build at")
                    x, y = map(int, coords.strip()[1:-1].split(","))
                    if self.grid.is_empty(x, y):
                        self.grid.place(x, y, Structure(self.agent_id))
                        self.status = f"Built at ({x}, {y})"
                        return self.send_message(f"Started construction at ({x}, {y})")
                    else:
                        self.status = f"Build target occupied"
                        return None
                except Exception as e:
                    self.status = f"Invalid build message"
                    return None

        self.status = "Idle"
        return None

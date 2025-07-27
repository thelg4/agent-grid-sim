# import random
# from typing import Optional
# from .base import BaseAgent
# from app.tools.message import Message
# from app.env.grid import Grid
# from app.env.entities import Structure

# class ScoutAgent(BaseAgent):
#     def __init__(self, agent_id: str, grid: Grid):
#         super().__init__(agent_id, "scout", grid)

#     def step(self, messages: list[Message]) -> Optional[Message]:
    
#         observation = self.observe()
#         location = observation["location"]

#         if location:
#             x, y = location
#             random.shuffle(self.grid.directions)
#             for dx, dy in self.grid.directions:
#                 nx, ny = x + dx, y + dy
#                 if self.grid.is_within_bounds(nx, ny) and self.grid.is_empty(nx, ny):
#                     self.grid.move_agent(self.agent_id, (nx, ny))
#                     self.status = f"Moved to ({nx}, {ny})"
#                     return self.send_message(f"Scout moved to ({nx}, {ny})")

#         self.status = "No available moves"
#         return None

import random
from typing import Optional
from .base import BaseAgent
from app.tools.message import Message
from app.env.grid import Grid

class ScoutAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid):
        super().__init__(agent_id, "scout", grid)
        self.exploration_pattern = []
        self.visited_cells = set()

    def step(self, messages: list[Message]) -> Optional[Message]:
        # Get LLM decision
        llm_action = self.get_llm_decision(messages)
        
        # Parse and execute action
        action_parts = llm_action.split()
        if not action_parts:
            return None
            
        action = action_parts[0].upper()
        
        if action == "MOVE" and len(action_parts) > 1:
            direction = action_parts[1].lower()
            return self._move(direction)
        elif action == "OBSERVE":
            return self._observe_and_report()
        elif action == "REPORT" and len(action_parts) > 1:
            report_content = " ".join(action_parts[1:])
            return self._send_report(report_content)
        else:
            # Fallback to basic exploration
            return self._basic_exploration()

    def _move(self, direction: str) -> Optional[Message]:
        """Move in specified direction."""
        direction_map = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0)
        }
        
        if direction not in direction_map:
            return None
            
        current_pos = self.grid.get_agent_position(self.agent_id)
        if not current_pos:
            return None
            
        dx, dy = direction_map[direction]
        new_x, new_y = current_pos[0] + dx, current_pos[1] + dy
        
        if self.grid.is_within_bounds(new_x, new_y) and self.grid.is_empty(new_x, new_y):
            self.grid.move_agent(self.agent_id, (new_x, new_y))
            self.visited_cells.add((new_x, new_y))
            self.status = f"Moved {direction} to ({new_x}, {new_y})"
            return self.send_message(f"Scout moved {direction} to ({new_x}, {new_y})")
        else:
            self.status = f"Cannot move {direction} - blocked or out of bounds"
            return None

    def _observe_and_report(self) -> Optional[Message]:
        """Observe surroundings and report findings."""
        observation = self.observe()
        findings = []
        
        for cell in observation["surroundings"]:
            if cell["structure"]:
                findings.append(f"Structure at {cell['position']}: {cell['structure']}")
            if cell["occupied_by"]:
                findings.append(f"Agent at {cell['position']}: {cell['occupied_by']}")
        
        if findings:
            report = f"Scout reporting from {observation['location']}: " + "; ".join(findings)
        else:
            report = f"Scout at {observation['location']}: Area clear, no structures or agents nearby"
            
        self.status = "Observing and reporting"
        return self.send_message(report)

    def _send_report(self, content: str) -> Optional[Message]:
        """Send a custom report message."""
        self.status = "Sending report"
        return self.send_message(f"Scout report: {content}")

    def _basic_exploration(self) -> Optional[Message]:
        """Fallback exploration behavior."""
        current_pos = self.grid.get_agent_position(self.agent_id)
        if not current_pos:
            return None
            
        x, y = current_pos
        directions = ["north", "south", "east", "west"]
        random.shuffle(directions)
        
        for direction in directions:
            direction_map = {
                "north": (0, -1),
                "south": (0, 1), 
                "east": (1, 0),
                "west": (-1, 0)
            }
            dx, dy = direction_map[direction]
            new_x, new_y = x + dx, y + dy
            
            if (self.grid.is_within_bounds(new_x, new_y) and 
                self.grid.is_empty(new_x, new_y) and 
                (new_x, new_y) not in self.visited_cells):
                
                return self._move(direction)
        
        # If no unvisited cells, move randomly
        for direction in directions:
            if self._move(direction):
                return self.send_message(f"Scout exploring randomly: moved {direction}")
                
        self.status = "No available moves"
        return None
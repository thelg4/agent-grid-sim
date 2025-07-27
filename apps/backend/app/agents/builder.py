# from typing import Union, Optional
# from .base import BaseAgent
# from app.tools.message import Message
# from app.env.grid import Grid
# from app.env.entities import Structure

# class BuilderAgent(BaseAgent):
#     def __init__(self, agent_id: str, grid: Grid):
#         super().__init__(agent_id, "builder", grid)
#         self.build_target = None

#     def step(self, messages: list[Message]) -> Optional[Message]:
#         """
#         Process incoming messages and take action if any suggest building.
#         Returns a message describing the result.
#         """
#         for message in messages:
#             if message.content.startswith("Build at"):
#                 # Parse coordinates
#                 try:
#                     _, coords = message.content.split("Build at")
#                     x, y = map(int, coords.strip()[1:-1].split(","))
#                     if self.grid.is_empty(x, y):
#                         self.grid.place(x, y, Structure(self.agent_id))
#                         self.status = f"Built at ({x}, {y})"
#                         return self.send_message(f"Started construction at ({x}, {y})")
#                     else:
#                         self.status = f"Build target occupied"
#                         return None
#                 except Exception as e:
#                     self.status = f"Invalid build message"
#                     return None

#         self.status = "Idle"
#         return None

from typing import Union, Optional
from .base import BaseAgent
from app.tools.message import Message
from app.env.grid import Grid
from app.env.entities import Structure

class BuilderAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid):
        super().__init__(agent_id, "builder", grid)
        self.build_queue = []
        self.buildings_completed = 0

    def step(self, messages: list[Message]) -> Optional[Message]:
        """
        Process messages and build strategically.
        """
        # Process strategic build orders from strategist
        for message in messages:
            if message.sender == "strategist" and "STRATEGIC_BUILD_ORDER" in message.content:
                coords = self._extract_coordinates_from_message(message.content)
                if coords and coords not in self.build_queue:
                    self.build_queue.append(coords)

        # Get LLM decision
        llm_action = self.get_llm_decision(messages)
        
        # Parse and execute action
        action_parts = llm_action.split()
        if not action_parts:
            return self._default_build_behavior()
            
        action = action_parts[0].upper()
        
        if action == "BUILD" and len(action_parts) > 1:
            coords_str = action_parts[1]
            return self._build_at_coordinates(coords_str)
        elif action == "MOVE" and len(action_parts) > 1:
            direction = action_parts[1].lower()
            return self._move_toward_build_site(direction)
        elif action == "WAIT":
            return self._wait_for_orders()
        else:
            return self._default_build_behavior()

    def _extract_coordinates_from_message(self, message: str) -> Optional[tuple[int, int]]:
        """Extract coordinates from a strategist message."""
        try:
            # Look for pattern like "Build at (x, y)"
            import re
            pattern = r'Build at \((\d+),\s*(\d+)\)'
            match = re.search(pattern, message)
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                return (x, y)
        except:
            pass
        return None

    def _build_at_coordinates(self, coords_str: str) -> Optional[Message]:
        """Build at specified coordinates."""
        try:
            # Parse coordinates
            coords = coords_str.strip("()")
            x, y = map(int, coords.split(","))
            
            if self._attempt_build(x, y):
                return self.send_message(f"CONSTRUCTION_COMPLETE: Building constructed at ({x}, {y})")
            else:
                return self.send_message(f"CONSTRUCTION_FAILED: Cannot build at ({x}, {y}) - location unavailable")
                
        except Exception as e:
            self.status = f"Invalid build coordinates: {coords_str}"
            return None

    def _attempt_build(self, x: int, y: int) -> bool:
        """Attempt to build at the specified location."""
        if not self.grid.is_within_bounds(x, y):
            self.status = f"Build failed: ({x}, {y}) out of bounds"
            return False
            
        if not self.grid.is_empty(x, y):
            self.status = f"Build failed: ({x}, {y}) occupied"
            return False
        
        # Check if we can reach the location (simple adjacency check)
        builder_pos = self.grid.get_agent_position(self.agent_id)
        if builder_pos:
            bx, by = builder_pos
            distance = abs(x - bx) + abs(y - by)
            if distance > 2:  # Can only build within 2 spaces
                self.status = f"Build failed: ({x}, {y}) too far away"
                return False
        
        # Place the structure
        try:
            structure = Structure(self.agent_id)
            self.grid.place(x, y, structure)
            self.buildings_completed += 1
            self.status = f"Built structure #{self.buildings_completed} at ({x}, {y})"
            
            # Remove from build queue if it was there
            if (x, y) in self.build_queue:
                self.build_queue.remove((x, y))
                
            return True
        except Exception as e:
            self.status = f"Build error: {str(e)}"
            return False

    def _move_toward_build_site(self, direction: str) -> Optional[Message]:
        """Move toward the next build site."""
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
            self.status = f"Moved {direction} to ({new_x}, {new_y})"
            return self.send_message(f"Builder repositioning: moved {direction} to ({new_x}, {new_y})")
        else:
            self.status = f"Cannot move {direction} - blocked"
            return None

    def _wait_for_orders(self) -> Optional[Message]:
        """Wait for build orders from strategist."""
        self.status = "Awaiting strategic build orders"
        return self.send_message("Builder ready: Awaiting construction orders from strategist")

    def _default_build_behavior(self) -> Optional[Message]:
        """Default building behavior when no specific orders."""
        # If we have items in build queue, work on them
        if self.build_queue:
            target_x, target_y = self.build_queue[0]
            
            # Try to build at the target location
            if self._attempt_build(target_x, target_y):
                return self.send_message(f"CONSTRUCTION_COMPLETE: Building constructed at ({target_x}, {target_y})")
            else:
                # Remove invalid target from queue
                self.build_queue.remove((target_x, target_y))
                return self.send_message(f"CONSTRUCTION_FAILED: Removed invalid target ({target_x}, {target_y}) from queue")
        
        # No build orders, look for adjacent empty spaces to build
        builder_pos = self.grid.get_agent_position(self.agent_id)
        if builder_pos:
            x, y = builder_pos
            
            # Check adjacent spaces for building opportunities
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # Adjacent cardinal directions
                nx, ny = x + dx, y + dy
                if self.grid.is_within_bounds(nx, ny) and self.grid.is_empty(nx, ny):
                    if self._attempt_build(nx, ny):
                        return self.send_message(f"OPPORTUNISTIC_BUILD: Constructed building at ({nx}, {ny})")
        
        # Nothing to do
        self.status = "No construction opportunities"
        return None

    def get_status(self) -> dict:
        """Get builder status with construction metrics."""
        base_status = super().get_status()
        base_status.update({
            "buildings_completed": self.buildings_completed,
            "build_queue_length": len(self.build_queue),
            "next_target": self.build_queue[0] if self.build_queue else None
        })
        return base_status
import random
import logging
from typing import Optional
from .base import BaseAgent
from app.tools.message import Message
from app.env.grid import Grid

logger = logging.getLogger(__name__)

class ScoutAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid):
        super().__init__(agent_id, "scout", grid)
        self.exploration_pattern = []
        self.visited_cells = set()
        self.update_status("Ready for exploration")
        
    def step(self, messages: list[Message]) -> Optional[Message]:
        """Scout explores the grid systematically"""
        logger.info(f"Scout step starting - current position: {self.grid.get_agent_position(self.agent_id)}")
        
        # Mark current position as visited
        current_pos = self.grid.get_agent_position(self.agent_id)
        if current_pos:
            self.visited_cells.add(current_pos)
        
        # Try LLM decision first, with fallback to deterministic behavior
        try:
            llm_action = self.get_llm_decision(messages)
            logger.info(f"Scout LLM decision: {llm_action}")
            
            # Parse and execute action
            action_parts = llm_action.split()
            if action_parts:
                action = action_parts[0].upper()
                
                if action == "MOVE" and len(action_parts) > 1:
                    direction = action_parts[1].lower()
                    result = self._move(direction)
                    if result:
                        return result
                elif action == "OBSERVE":
                    return self._observe_and_report()
                elif action == "REPORT" and len(action_parts) > 1:
                    report_content = " ".join(action_parts[1:])
                    return self._send_report(report_content)
        except Exception as e:
            logger.warning(f"Scout LLM decision failed: {e}, using fallback behavior")
            self._add_to_memory(f"LLM failed, using fallback")
        
        # Fallback to systematic exploration
        return self._systematic_exploration()

    def _systematic_exploration(self) -> Optional[Message]:
        """Systematic exploration with guaranteed movement"""
        current_pos = self.grid.get_agent_position(self.agent_id)
        if not current_pos:
            logger.error("Scout has no position!")
            return None
            
        x, y = current_pos
        logger.info(f"Scout systematic exploration from ({x}, {y})")
        
        # Priority order for exploration: right, down, left, up
        exploration_directions = [
            ("east", (1, 0)),
            ("south", (0, 1)), 
            ("west", (-1, 0)),
            ("north", (0, -1))
        ]
        
        # First, try to move to an unvisited adjacent cell
        for direction_name, (dx, dy) in exploration_directions:
            new_x, new_y = x + dx, y + dy
            
            if (self.grid.is_within_bounds(new_x, new_y) and 
                self.grid.is_empty(new_x, new_y) and 
                (new_x, new_y) not in self.visited_cells):
                
                logger.info(f"Scout moving {direction_name} to unvisited cell ({new_x}, {new_y})")
                return self._move(direction_name)
        
        # If no unvisited cells, move to any available adjacent cell
        for direction_name, (dx, dy) in exploration_directions:
            new_x, new_y = x + dx, y + dy
            
            if (self.grid.is_within_bounds(new_x, new_y) and 
                self.grid.is_empty(new_x, new_y)):
                
                logger.info(f"Scout moving {direction_name} to visited cell ({new_x}, {new_y})")
                return self._move(direction_name)
        
        # If can't move anywhere, report current status
        logger.info("Scout cannot move, sending observation report")
        return self._observe_and_report()

    def _move(self, direction: str) -> Optional[Message]:
        """Move in specified direction."""
        direction_map = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0)
        }
        
        if direction not in direction_map:
            logger.warning(f"Invalid direction: {direction}")
            return None
            
        current_pos = self.grid.get_agent_position(self.agent_id)
        if not current_pos:
            logger.error("Scout has no current position for movement")
            return None
            
        dx, dy = direction_map[direction]
        new_x, new_y = current_pos[0] + dx, current_pos[1] + dy
        
        logger.info(f"Scout attempting to move {direction} from {current_pos} to ({new_x}, {new_y})")
        
        if self.grid.is_within_bounds(new_x, new_y) and self.grid.is_empty(new_x, new_y):
            success = self.grid.move_agent(self.agent_id, (new_x, new_y))
            if success:
                self.visited_cells.add((new_x, new_y))
                self.update_status(f"Moved {direction} to ({new_x}, {new_y})")
                
                # Add detailed movement to memory
                self._add_to_memory(f"Moved {direction}: ({current_pos[0]},{current_pos[1]}) → ({new_x},{new_y})")
                
                message = f"SCOUT_REPORT: Moved {direction} to ({new_x}, {new_y}) - continuing exploration"
                logger.info(f"Scout move successful: {message}")
                return self.send_message(message)
            else:
                logger.warning(f"Scout move failed - grid.move_agent returned False")
                self.update_status(f"Move {direction} failed")
                return None
        else:
            logger.warning(f"Scout cannot move {direction} - blocked or out of bounds")
            self.update_status(f"Cannot move {direction} - blocked")
            return None

    def _observe_and_report(self) -> Optional[Message]:
        """Observe surroundings and report findings."""
        observation = self.observe()
        current_pos = observation["location"]
        
        findings = []
        for cell in observation["surroundings"]:
            if cell["structure"]:
                findings.append(f"Structure at {cell['position']}")
            if cell["occupied_by"] and cell["occupied_by"] != self.agent_id:
                findings.append(f"Agent {cell['occupied_by']} at {cell['position']}")
        
        visited_count = len(self.visited_cells)
        total_cells = self.grid.width * self.grid.height
        exploration_percent = (visited_count / total_cells) * 100
        
        # Add observation to memory
        self._add_to_memory(f"Observed from {current_pos}: {len(findings)} findings")
        
        if findings:
            report = f"SCOUT_REPORT: At {current_pos}, found: {'; '.join(findings)}. Progress: {exploration_percent:.1f}%"
        else:
            report = f"SCOUT_REPORT: At {current_pos}, area clear. Exploration: {exploration_percent:.1f}% ({visited_count}/{total_cells})"
            
        self.update_status("Observing and reporting")
        logger.info(f"Scout observation report: {report}")
        return self.send_message(report)

    def _send_report(self, content: str) -> Optional[Message]:
        """Send a custom report message."""
        self.update_status("Sending custom report")
        self._add_to_memory(f"Custom report: {content[:30]}...")
        report_msg = f"SCOUT_REPORT: {content}"
        logger.info(f"Scout custom report: {report_msg}")
        return self.send_message(report_msg)

    def get_status(self) -> dict:
        """Get scout status with exploration metrics."""
        base_status = super().get_status()
        base_status.update({
            "cells_visited": len(self.visited_cells),
            "exploration_percentage": (len(self.visited_cells) / (self.grid.width * self.grid.height)) * 100,
            "mission_role": "Explorer & Intelligence Gatherer"
        })
        return base_status
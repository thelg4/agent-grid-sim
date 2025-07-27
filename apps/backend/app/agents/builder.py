from typing import Union, Optional
import re
import logging
from .base import BaseAgent
from app.tools.message import Message
from app.env.grid import Grid
from app.env.entities import Structure

logger = logging.getLogger(__name__)

class BuilderAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid):
        super().__init__(agent_id, "builder", grid)
        self.build_queue = []
        self.buildings_completed = 0
        self.last_built_location = None
        self.processed_messages = set()  # Track processed messages

    def step(self, messages: list[Message]) -> Optional[Message]:
        """
        Process strategic build orders and execute construction.
        """
        logger.info(f"Builder step starting - total messages: {len(messages)}")
        
        # Find the MOST RECENT strategic build order from this step
        latest_strategic_order = None
        
        # Process messages in reverse order to get the most recent first
        for message in reversed(messages):
            if (hasattr(message, 'sender') and 
                message.sender == "strategist" and 
                "STRATEGIC_BUILD_ORDER" in message.content):
                
                # Create a unique message ID to avoid processing the same message twice
                message_id = f"{message.sender}_{message.content}_{len(messages)}"
                
                if message_id not in self.processed_messages:
                    latest_strategic_order = message
                    self.processed_messages.add(message_id)
                    logger.info(f"Builder found NEW strategic order: {message.content}")
                    break
                else:
                    logger.info(f"Builder skipping already processed message: {message.content}")
        
        # Process the latest strategic order
        if latest_strategic_order:
            coords = self._extract_coordinates_from_message(latest_strategic_order.content)
            
            if coords:
                x, y = coords
                logger.info(f"Builder processing NEW coordinates: ({x}, {y})")
                
                # Execute immediately
                if self._attempt_build(x, y):
                    self.last_built_location = (x, y)
                    return self.send_message(f"CONSTRUCTION_COMPLETE: Strategic building constructed at ({x}, {y})")
                else:
                    return self.send_message(f"CONSTRUCTION_FAILED: Cannot build at ({x}, {y}) - location unavailable")
            else:
                logger.warning(f"Failed to extract coordinates from: {latest_strategic_order.content}")
        else:
            logger.info("Builder: No new strategic orders found")

        # If no strategic orders processed, try opportunistic building
        return self._opportunistic_build()

    def _extract_coordinates_from_message(self, message: str) -> Optional[tuple[int, int]]:
        """Extract coordinates from a strategist message."""
        try:
            logger.info(f"Extracting coordinates from message: '{message}'")
            
            # Look for pattern like "Build at (x, y)" or "(x, y)"
            patterns = [
                r'Build at \((\d+),\s*(\d+)\)',
                r'\((\d+),\s*(\d+)\)',
                r'at \((\d+),\s*(\d+)\)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    x, y = int(match.group(1)), int(match.group(2))
                    logger.info(f"Successfully extracted coordinates ({x}, {y}) using pattern: {pattern}")
                    return (x, y)
            
            logger.warning(f"No coordinate patterns matched in message: {message}")
        except Exception as e:
            logger.error(f"Failed to extract coordinates from: {message}, error: {e}")
        return None

    def _attempt_build(self, x: int, y: int) -> bool:
        """Attempt to build at the specified location."""
        logger.info(f"Builder attempting to build at ({x}, {y})")
        
        # Check bounds
        if not self.grid.is_within_bounds(x, y):
            logger.warning(f"Build failed: ({x}, {y}) out of bounds (grid: {self.grid.width}x{self.grid.height})")
            self.status = f"Build failed: ({x}, {y}) out of bounds"
            return False
            
        # Check if location is empty
        if not self.grid.is_empty(x, y):
            cell = self.grid.grid.get((x, y))
            logger.warning(f"Build failed: ({x}, {y}) occupied by {cell.occupied_by if cell else 'unknown'}, structure: {cell.structure if cell else 'unknown'}")
            self.status = f"Build failed: ({x}, {y}) occupied"
            return False
        
        # Place the structure
        try:
            logger.info(f"Attempting grid.place({x}, {y}, Structure)")
            success = self.grid.place(x, y, Structure(self.agent_id))
            
            if success:
                self.buildings_completed += 1
                self.status = f"Built structure #{self.buildings_completed} at ({x}, {y})"
                logger.info(f"BUILD SUCCESS: Structure #{self.buildings_completed} built at ({x}, {y})")
                
                # Verify the build actually happened
                cell = self.grid.grid.get((x, y))
                if cell and cell.structure:
                    logger.info(f"Verification: Cell at ({x}, {y}) now has structure: {cell.structure}")
                else:
                    logger.error(f"Verification FAILED: Cell at ({x}, {y}) still empty after build!")
                
                return True
            else:
                logger.warning(f"Build failed: grid.place returned False for ({x}, {y})")
                self.status = f"Build failed: grid placement failed"
                return False
                
        except Exception as e:
            logger.error(f"Build error at ({x}, {y}): {str(e)}")
            self.status = f"Build error: {str(e)}"
            return False

    def _opportunistic_build(self) -> Optional[Message]:
        """Look for nearby opportunities to build."""
        builder_pos = self.grid.get_agent_position(self.agent_id)
        if builder_pos:
            x, y = builder_pos
            logger.info(f"Builder opportunistic build from position ({x}, {y})")
            
            # Check adjacent spaces for building opportunities
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if self.grid.is_within_bounds(nx, ny) and self.grid.is_empty(nx, ny):
                    logger.info(f"Opportunistic build attempt at ({nx}, {ny})")
                    if self._attempt_build(nx, ny):
                        self.last_built_location = (nx, ny)
                        return self.send_message(f"OPPORTUNISTIC_BUILD: Constructed building at ({nx}, {ny})")
        
        # Nothing to do
        self.status = "No construction opportunities"
        logger.info("Builder: No construction opportunities found")
        return self.send_message("Builder standing by: No immediate construction opportunities")

    def get_status(self) -> dict:
        """Get builder status with construction metrics."""
        base_status = super().get_status()
        base_status.update({
            "buildings_completed": self.buildings_completed,
            "last_built_location": self.last_built_location,
            "processed_messages_count": len(self.processed_messages)
        })
        return base_status
from typing import Union, Optional
import re
import logging
from .base import BaseAgent
from app.tools.message import Message, MessageType, MessagePriority
from app.env.grid import Grid
from app.env.entities import Structure

logger = logging.getLogger(__name__)

class BuilderAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid, coordination_manager=None, shared_state=None):
        super().__init__(agent_id, "builder", grid, coordination_manager, shared_state)
        self.build_queue = []
        self.buildings_completed = 0
        self.last_built_location = None
        self.processed_messages = set()  # Track processed messages
        self.current_target = None  # Track current movement target
        self.movement_path = []  # Path to target

    # def step(self, messages: list[Message]) -> Optional[Message]:
    #     """
    #     Process strategic build orders and execute construction.
    #     """
    #     logger.info(f"Builder step starting - total messages: {len(messages)}")
        
    #     # If we're already moving toward a target, continue that first
    #     if self.current_target and self.movement_path:
    #         return self._continue_movement()
        
    #     # Find the MOST RECENT strategic build order from this step
    #     latest_strategic_order = None
        
    #     # Process messages in reverse order to get the most recent first
    #     for message in reversed(messages):
    #         if (hasattr(message, 'sender') and 
    #             message.sender == "strategist" and 
    #             "STRATEGIC_BUILD_ORDER" in message.content):
                
    #             # Create a unique message ID to avoid processing the same message twice
    #             message_id = f"{message.sender}_{message.content}_{len(messages)}"
                
    #             if message_id not in self.processed_messages:
    #                 latest_strategic_order = message
    #                 self.processed_messages.add(message_id)
    #                 logger.info(f"Builder found NEW strategic order: {message.content}")
    #                 break
    #             else:
    #                 logger.info(f"Builder skipping already processed message: {message.content}")
        
    #     # Process the latest strategic order
    #     if latest_strategic_order:
    #         coords = self._extract_coordinates_from_message(latest_strategic_order.content)
            
    #         if coords:
    #             x, y = coords
    #             logger.info(f"Builder processing NEW coordinates: ({x}, {y})")
                
    #             # Check if we can build immediately (already at location or adjacent)
    #             current_pos = self.grid.get_agent_position(self.agent_id)
    #             if current_pos:
    #                 current_x, current_y = current_pos
    #                 distance = abs(x - current_x) + abs(y - current_y)
                    
    #                 if distance <= 1:  # At location or adjacent
    #                     logger.info(f"Builder close enough to build at ({x}, {y})")
    #                     if self._attempt_build(x, y):
    #                         self.last_built_location = (x, y)
    #                         return self.send_message(
    #                             f"CONSTRUCTION_COMPLETE: Strategic building constructed at ({x}, {y})",
    #                             MessageType.REPORT,
    #                             MessagePriority.HIGH
    #                         )
    #                     else:
    #                         return self.send_message(
    #                             f"CONSTRUCTION_FAILED: Cannot build at ({x}, {y}) - location unavailable",
    #                             MessageType.ERROR,
    #                             MessagePriority.HIGH
    #                         )
    #                 else:
    #                     # Start movement toward target
    #                     logger.info(f"Builder needs to move to ({x}, {y}), distance: {distance}")
    #                     self.current_target = (x, y)
    #                     self.movement_path = self._calculate_path(current_pos, (x, y))
    #                     return self._continue_movement()
    #         else:
    #             logger.warning(f"Failed to extract coordinates from: {latest_strategic_order.content}")
    #     else:
    #         logger.info("Builder: No new strategic orders found")

    #     # If no strategic orders processed, try opportunistic building
    #     return self._opportunistic_build()
    def step(self, messages: list[Message]) -> Optional[Message]:
        """
        Process strategic build orders and execute construction.
        """
        logger.info(f"Builder step starting - total messages: {len(messages)}")
        
        # ADD THIS: Check if builder has a position
        current_pos = self.grid.get_agent_position(self.agent_id)
        if current_pos is None:
            logger.error("Builder has no position! Attempting emergency placement...")
            # Try to place builder somewhere
            for x in range(self.grid.width):
                for y in range(self.grid.height):
                    if self.grid.is_empty(x, y):
                        if self.grid.place_agent(self.agent_id, (x, y)):
                            logger.info(f"Emergency placement: Builder placed at ({x}, {y})")
                            current_pos = (x, y)
                            break
                if current_pos:
                    break
            
            if current_pos is None:
                return self.send_message(
                    "CRITICAL_ERROR: Builder has no position and grid is full",
                    MessageType.ERROR,
                    MessagePriority.URGENT
                )
        
        # If we're already moving toward a target, continue that first
        if self.current_target and self.movement_path:
            return self._continue_movement()
        
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
                
                # Check if we can build immediately (already at location or adjacent)
                current_pos = self.grid.get_agent_position(self.agent_id)
                if current_pos:
                    current_x, current_y = current_pos
                    distance = abs(x - current_x) + abs(y - current_y)
                    
                    if distance <= 1:  # At location or adjacent
                        logger.info(f"Builder close enough to build at ({x}, {y})")
                        if self._attempt_build(x, y):
                            self.last_built_location = (x, y)
                            return self.send_message(
                                f"CONSTRUCTION_COMPLETE: Strategic building constructed at ({x}, {y})",
                                MessageType.REPORT,
                                MessagePriority.HIGH
                            )
                        else:
                            return self.send_message(
                                f"CONSTRUCTION_FAILED: Cannot build at ({x}, {y}) - location unavailable",
                                MessageType.ERROR,
                                MessagePriority.HIGH
                            )
                    else:
                        # Start movement toward target
                        logger.info(f"Builder needs to move to ({x}, {y}), distance: {distance}")
                        self.current_target = (x, y)
                        self.movement_path = self._calculate_path(current_pos, (x, y))
                        return self._continue_movement()
            else:
                logger.warning(f"Failed to extract coordinates from: {latest_strategic_order.content}")
        else:
            logger.info("Builder: No new strategic orders found")

        # If no strategic orders processed, try opportunistic building
        return self._opportunistic_build()

    def _continue_movement(self) -> Optional[Message]:
        """Continue moving toward the current target."""
        if not self.current_target or not self.movement_path:
            return None
            
        current_pos = self.grid.get_agent_position(self.agent_id)
        if not current_pos:
            logger.error("Builder has no current position!")
            return None
        
        # Get next step in path
        next_pos = self.movement_path[0]
        
        # Try to move to next position
        if self.grid.is_within_bounds(next_pos[0], next_pos[1]) and self.grid.is_empty(next_pos[0], next_pos[1]):
            success = self.grid.move_agent(self.agent_id, next_pos)
            if success:
                self.movement_path.pop(0)  # Remove completed step
                self.status = f"Moving toward ({self.current_target[0]}, {self.current_target[1]}) - {len(self.movement_path)} steps remaining"
                self._add_to_memory(f"Moved to {next_pos} toward build site")
                
                # Check if we've reached the target or are adjacent
                target_x, target_y = self.current_target
                current_x, current_y = next_pos
                distance = abs(target_x - current_x) + abs(target_y - current_y)
                
                if distance <= 1:  # At target or adjacent
                    logger.info(f"Builder reached build location ({target_x}, {target_y})")
                    if self._attempt_build(target_x, target_y):
                        self.last_built_location = (target_x, target_y)
                        self.current_target = None
                        self.movement_path = []
                        return self.send_message(
                            f"CONSTRUCTION_COMPLETE: Strategic building constructed at ({target_x}, {target_y})",
                            MessageType.REPORT,
                            MessagePriority.HIGH
                        )
                    else:
                        self.current_target = None
                        self.movement_path = []
                        return self.send_message(
                            f"CONSTRUCTION_FAILED: Cannot build at ({target_x}, {target_y}) - location unavailable",
                            MessageType.ERROR,
                            MessagePriority.HIGH
                        )
                
                return self.send_message(
                    f"MOVEMENT_PROGRESS: Moving toward ({target_x}, {target_y}) - {len(self.movement_path)} steps remaining",
                    MessageType.REPORT,
                    MessagePriority.NORMAL
                )
            else:
                logger.warning(f"Builder movement blocked at {next_pos}")
                # Clear movement plan if blocked
                self.current_target = None
                self.movement_path = []
                return self.send_message(
                    f"MOVEMENT_FAILED: Path blocked, abandoning build target",
                    MessageType.ERROR,
                    MessagePriority.HIGH
                )
        else:
            logger.warning(f"Next step {next_pos} is blocked or invalid")
            self.current_target = None
            self.movement_path = []
            return self.send_message(
                f"MOVEMENT_FAILED: Cannot reach build location",
                MessageType.ERROR,
                MessagePriority.HIGH
            )

    def _calculate_path(self, start: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
        """Calculate a simple path from start to target."""
        path = []
        current_x, current_y = start
        target_x, target_y = target
        
        # Simple pathfinding: move horizontally first, then vertically
        while current_x != target_x:
            if current_x < target_x:
                current_x += 1
            else:
                current_x -= 1
            path.append((current_x, current_y))
        
        while current_y != target_y:
            if current_y < target_y:
                current_y += 1
            else:
                current_y -= 1
            path.append((current_x, current_y))
        
        logger.info(f"Calculated path from {start} to {target}: {path}")
        return path

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
            
        # Check if location is empty (no other agents, but builder can build where it stands)
        cell = self.grid.grid.get((x, y))
        if cell and cell.structure:
            logger.warning(f"Build failed: ({x}, {y}) already has structure: {cell.structure}")
            self.status = f"Build failed: ({x}, {y}) has structure"
            return False
        
        # Check if there's another agent at this location (not the builder)
        if cell and cell.occupied_by and cell.occupied_by != self.agent_id:
            logger.warning(f"Build failed: ({x}, {y}) occupied by {cell.occupied_by}")
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
                
                self._add_to_memory(f"Built structure #{self.buildings_completed} at ({x}, {y})")
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
            
            # Check current position first (can build where standing)
            if self.grid.is_within_bounds(x, y):
                cell = self.grid.grid.get((x, y))
                if not cell or not cell.structure:  # No structure here yet
                    logger.info(f"Opportunistic build attempt at current position ({x}, {y})")
                    if self._attempt_build(x, y):
                        self.last_built_location = (x, y)
                        return self.send_message(
                            f"OPPORTUNISTIC_BUILD: Constructed building at ({x}, {y})",
                            MessageType.REPORT,
                            MessagePriority.NORMAL
                        )
            
            # Check adjacent spaces for building opportunities
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if self.grid.is_within_bounds(nx, ny) and self.grid.is_empty(nx, ny):
                    cell = self.grid.grid.get((nx, ny))
                    if not cell or not cell.structure:
                        logger.info(f"Opportunistic build attempt at ({nx}, {ny})")
                        if self._attempt_build(nx, ny):
                            self.last_built_location = (nx, ny)
                            return self.send_message(
                                f"OPPORTUNISTIC_BUILD: Constructed building at ({nx}, {ny})",
                                MessageType.REPORT,
                                MessagePriority.NORMAL
                            )
        
        # Nothing to do
        self.status = "No construction opportunities"
        logger.info("Builder: No construction opportunities found")
        return self.send_message(
            "Builder standing by: No immediate construction opportunities",
            MessageType.REPORT,
            MessagePriority.LOW
        )

    def get_status(self) -> dict:
        """Get builder status with construction metrics."""
        base_status = super().get_status()
        base_status.update({
            "buildings_completed": self.buildings_completed,
            "last_built_location": self.last_built_location,
            "processed_messages_count": len(self.processed_messages),
            "current_target": self.current_target,
            "movement_steps_remaining": len(self.movement_path)
        })
        return base_status
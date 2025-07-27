from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

GridLocation = Tuple[int, int]

class Cell:
    def __init__(self):
        self.occupied_by: Optional[str] = None  # agent_id
        self.structure: Optional[str] = None    # e.g., 'building', 'scanned'

    def __repr__(self):
        return f"Cell(occupied_by={self.occupied_by}, structure={self.structure})"


class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: Dict[GridLocation, Cell] = {
            (x, y): Cell() for x in range(width) for y in range(height)
        }
        self.agent_positions: Dict[str, GridLocation] = {}  # agent_id -> (x, y)
        self.directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # left, right, up, down
        logger.info(f"Grid initialized: {width}x{height} = {len(self.grid)} cells")

    def place_agent(self, agent_id: str, position: GridLocation) -> bool:
        if position not in self.grid or self.grid[position].occupied_by:
            return False
        self.grid[position].occupied_by = agent_id
        self.agent_positions[agent_id] = position
        logger.info(f"Agent {agent_id} placed at {position}")
        return True

    def move_agent(self, agent_id: str, new_position: GridLocation) -> bool:
        if agent_id not in self.agent_positions:
            logger.warning(f"Cannot move agent {agent_id}: not found in agent_positions")
            return False
        if new_position not in self.grid:
            logger.warning(f"Cannot move agent {agent_id} to {new_position}: position invalid")
            return False
        if self.grid[new_position].occupied_by and self.grid[new_position].occupied_by != agent_id:
            logger.warning(f"Cannot move agent {agent_id} to {new_position}: position occupied by {self.grid[new_position].occupied_by}")
            return False

        old_position = self.agent_positions[agent_id]
        self.grid[old_position].occupied_by = None
        self.grid[new_position].occupied_by = agent_id
        self.agent_positions[agent_id] = new_position
        logger.info(f"Agent {agent_id} moved from {old_position} to {new_position}")
        return True

    def get_agent_position(self, agent_id: str) -> Optional[GridLocation]:
        return self.agent_positions.get(agent_id)

    def build_structure(self, position: GridLocation, structure: str) -> bool:
        if position in self.grid:
            self.grid[position].structure = structure
            logger.info(f"Structure '{structure}' built at {position}")
            return True
        return False

    def place(self, x: int, y: int, structure) -> bool:
        """Place a structure at the given coordinates - agents can build where they stand"""
        position = (x, y)
        logger.info(f"Grid.place called: position=({x}, {y}), structure={structure}")
        
        # Check if position exists in grid
        if position not in self.grid:
            logger.error(f"Position {position} not in grid bounds")
            return False
            
        cell = self.grid[position]
        logger.info(f"Cell at {position}: occupied_by={cell.occupied_by}, structure={cell.structure}")
        
        # Check if there's already a structure
        if cell.structure is not None:
            logger.warning(f"Cannot place structure at {position}: already has structure {cell.structure}")
            return False
        
        # IMPORTANT: Allow building where an agent stands (builders can build on their location)
        # This is realistic - a builder can construct a building where they are standing
        
        # Place the structure
        cell.structure = "building"
        logger.info(f"SUCCESS: Structure placed at {position}")
        
        # Verify the placement
        verification_cell = self.grid[position]
        logger.info(f"Verification: Cell at {position} now has structure={verification_cell.structure}, occupied_by={verification_cell.occupied_by}")
        
        return True

    def serialize(self) -> Dict:
        return {
            "width": self.width,
            "height": self.height,
            "cells": {
                f"{x},{y}": {
                    "occupied_by": cell.occupied_by,
                    "structure": cell.structure
                }
                for (x, y), cell in self.grid.items()
            }
        }
    
    def is_within_bounds(self, x: int, y: int) -> bool:
        result = 0 <= x < self.width and 0 <= y < self.height
        # FIXED: Changed self.grid.height to self.height
        logger.debug(f"is_within_bounds({x}, {y}) = {result} (grid: {self.width}x{self.height})")
        return result

    def is_empty(self, x: int, y: int) -> bool:
        """Check if a position is empty (no other agents, structures are checked separately)"""
        if (x, y) not in self.grid:
            return False
        cell = self.grid[(x, y)]
        # For movement purposes, only check if occupied by another agent
        # Structures don't prevent movement, they're just there
        is_empty = cell.occupied_by is None
        logger.debug(f"is_empty({x}, {y}) = {is_empty} (occupied_by={cell.occupied_by}, structure={cell.structure})")
        return is_empty
    
    def is_completely_empty(self, x: int, y: int) -> bool:
        """Check if a position has no agents AND no structures"""
        if (x, y) not in self.grid:
            return False
        cell = self.grid[(x, y)]
        is_completely_empty = cell.occupied_by is None and cell.structure is None
        logger.debug(f"is_completely_empty({x}, {y}) = {is_completely_empty} (occupied_by={cell.occupied_by}, structure={cell.structure})")
        return is_completely_empty
        
    def debug_grid_state(self):
        """Debug method to print grid state"""
        logger.info(f"=== GRID DEBUG STATE ===")
        logger.info(f"Grid size: {self.width}x{self.height}")
        logger.info(f"Agent positions: {self.agent_positions}")
        
        structure_count = 0
        agent_count = 0
        for (x, y), cell in self.grid.items():
            if cell.structure:
                structure_count += 1
                logger.info(f"Structure at ({x}, {y}): {cell.structure} (occupied_by: {cell.occupied_by})")
            if cell.occupied_by:
                agent_count += 1
                logger.info(f"Agent at ({x}, {y}): {cell.occupied_by} (structure: {cell.structure})")
        
        logger.info(f"Total structures: {structure_count}")
        logger.info(f"Total agents: {agent_count}")
        logger.info(f"=== END GRID DEBUG ===")
        
        return structure_count
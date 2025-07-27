from typing import Dict, Tuple, Optional

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

    def place_agent(self, agent_id: str, position: GridLocation) -> bool:
        if position not in self.grid or self.grid[position].occupied_by:
            return False
        self.grid[position].occupied_by = agent_id
        self.agent_positions[agent_id] = position
        return True

    def move_agent(self, agent_id: str, new_position: GridLocation) -> bool:
        if agent_id not in self.agent_positions:
            return False
        if new_position not in self.grid or self.grid[new_position].occupied_by:
            return False

        old_position = self.agent_positions[agent_id]
        self.grid[old_position].occupied_by = None
        self.grid[new_position].occupied_by = agent_id
        self.agent_positions[agent_id] = new_position
        return True

    def get_agent_position(self, agent_id: str) -> Optional[GridLocation]:
        return self.agent_positions.get(agent_id)

    def build_structure(self, position: GridLocation, structure: str) -> bool:
        if position in self.grid:
            self.grid[position].structure = structure
            return True
        return False

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
        return 0 <= x < self.width and 0 <= y < self.height

    def is_empty(self, x: int, y: int) -> bool:
        return (x, y) in self.grid and self.grid[(x, y)].occupied_by is None


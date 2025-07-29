# apps/backend/app/env/grid.py

from typing import Dict, Tuple, Optional, List, Set
import logging
import random
from enum import Enum
from dataclasses import dataclass, field
import time

logger = logging.getLogger(__name__)

GridLocation = Tuple[int, int]

class TerrainType(Enum):
    PLAIN = "plain"
    OBSTACLE = "obstacle"
    RESOURCE_RICH = "resource_rich"
    DIFFICULT = "difficult"
    WATER = "water"

class ResourceType(Enum):
    MATERIALS = "materials"
    ENERGY = "energy"
    TOOLS = "tools"
    RARE_MINERALS = "rare_minerals"

@dataclass
class ResourceDeposit:
    resource_type: ResourceType
    amount: int
    regeneration_rate: float = 0.0
    last_harvested: float = field(default_factory=time.time)
    max_amount: int = 100
    
    def harvest(self, amount: int) -> int:
        """Harvest resources, returns amount actually harvested"""
        available = min(amount, self.amount)
        self.amount -= available
        self.last_harvested = time.time()
        return available
    
    def regenerate(self):
        """Regenerate resources over time"""
        if self.regeneration_rate > 0:
            time_passed = time.time() - self.last_harvested
            regenerated = min(
                int(time_passed * self.regeneration_rate),
                self.max_amount - self.amount
            )
            self.amount += regenerated

@dataclass 
class TerrainInfo:
    terrain_type: TerrainType
    movement_cost: float = 1.0  # Multiplier for movement through this terrain
    build_difficulty: float = 1.0  # Multiplier for building difficulty
    visibility_modifier: float = 1.0  # Affects scanning range
    resources: Dict[ResourceType, ResourceDeposit] = field(default_factory=dict)
    
    def can_build_on(self) -> bool:
        """Check if this terrain allows building"""
        return self.terrain_type not in [TerrainType.WATER, TerrainType.OBSTACLE]
    
    def can_move_through(self) -> bool:
        """Check if agents can move through this terrain"""
        return self.terrain_type != TerrainType.OBSTACLE

class Cell:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.occupied_by: Optional[str] = None  # agent_id
        self.structure: Optional[str] = None    # e.g., 'building', 'scanned'
        self.terrain: TerrainInfo = TerrainInfo(TerrainType.PLAIN)
        self.last_visited: Dict[str, float] = {}  # agent_id -> timestamp
        self.visibility: float = 1.0  # How visible this cell is (affects detection)
        self.metadata: Dict[str, any] = {}  # Additional cell-specific data
        
    def visit(self, agent_id: str):
        """Mark cell as visited by an agent"""
        self.last_visited[agent_id] = time.time()
    
    def get_movement_cost(self) -> float:
        """Get movement cost for this cell"""
        base_cost = self.terrain.movement_cost
        # Increase cost if occupied by another agent
        if self.occupied_by:
            base_cost *= 2.0
        return base_cost
    
    def get_resources(self) -> Dict[ResourceType, int]:
        """Get available resources in this cell"""
        return {rt: rd.amount for rt, rd in self.terrain.resources.items()}
    
    def harvest_resource(self, resource_type: ResourceType, amount: int) -> int:
        """Harvest resources from this cell"""
        if resource_type in self.terrain.resources:
            return self.terrain.resources[resource_type].harvest(amount)
        return 0
    
    def update_resources(self):
        """Update resource regeneration"""
        for resource_deposit in self.terrain.resources.values():
            resource_deposit.regenerate()

    def __repr__(self):
        return f"Cell({self.x},{self.y}, occupied_by={self.occupied_by}, structure={self.structure}, terrain={self.terrain.terrain_type.value})"

class CollisionAvoidanceSystem:
    """System to handle multi-agent collision avoidance"""
    
    def __init__(self):
        self.movement_requests: Dict[str, GridLocation] = {}
        self.movement_priorities: Dict[str, float] = {}
        
    def request_movement(self, agent_id: str, target: GridLocation, priority: float = 1.0):
        """Request movement to a target location"""
        self.movement_requests[agent_id] = target
        self.movement_priorities[agent_id] = priority
    
    def resolve_conflicts(self, grid: 'Grid') -> Dict[str, bool]:
        """Resolve movement conflicts and return which agents can move"""
        results = {}
        
        # Group agents by target location
        target_groups = {}
        for agent_id, target in self.movement_requests.items():
            if target not in target_groups:
                target_groups[target] = []
            target_groups[target].append(agent_id)
        
        # Resolve conflicts for each target
        for target, agents in target_groups.items():
            if len(agents) == 1:
                # No conflict
                results[agents[0]] = True
            else:
                # Conflict - resolve by priority
                agents.sort(key=lambda a: self.movement_priorities.get(a, 1.0), reverse=True)
                results[agents[0]] = True  # Highest priority agent moves
                for agent in agents[1:]:
                    results[agent] = False  # Others blocked
        
        # Clear requests after resolution
        self.movement_requests.clear()
        self.movement_priorities.clear()
        
        return results

class Grid:
    def __init__(self, width: int, height: int, terrain_seed: int = None):
        self.width = width
        self.height = height
        self.grid: Dict[GridLocation, Cell] = {}
        self.agent_positions: Dict[str, GridLocation] = {}  # agent_id -> (x, y)
        self.directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # left, right, up, down
        self.collision_system = CollisionAvoidanceSystem()
        
        # Initialize cells with terrain
        self._initialize_terrain(terrain_seed)
        
        # Performance tracking
        self.movement_history: List[Dict] = []
        self.resource_extraction_log: List[Dict] = []
        
        logger.info(f"Enhanced Grid initialized: {width}x{height} = {len(self.grid)} cells")

    def _initialize_terrain(self, seed: int = None):
        """Initialize grid with varied terrain"""
        if seed:
            random.seed(seed)
        
        for x in range(self.width):
            for y in range(self.height):
                cell = Cell(x, y)
                
                # Generate terrain based on position and randomness
                terrain_roll = random.random()
                
                if terrain_roll < 0.1:  # 10% obstacles
                    cell.terrain = TerrainInfo(
                        TerrainType.OBSTACLE,
                        movement_cost=float('inf'),
                        build_difficulty=float('inf')
                    )
                elif terrain_roll < 0.2:  # 10% difficult terrain
                    cell.terrain = TerrainInfo(
                        TerrainType.DIFFICULT,
                        movement_cost=2.0,
                        build_difficulty=1.5
                    )
                elif terrain_roll < 0.3:  # 10% resource-rich areas
                    cell.terrain = TerrainInfo(
                        TerrainType.RESOURCE_RICH,
                        movement_cost=1.0,
                        build_difficulty=0.8
                    )
                    # Add random resources
                    if random.random() < 0.7:
                        resource_type = random.choice(list(ResourceType))
                        amount = random.randint(10, 50)
                        cell.terrain.resources[resource_type] = ResourceDeposit(
                            resource_type, amount, regeneration_rate=0.1
                        )
                else:  # 70% plain terrain
                    cell.terrain = TerrainInfo(TerrainType.PLAIN)
                
                self.grid[(x, y)] = cell

    def place_agent(self, agent_id: str, position: GridLocation) -> bool:
        """Place an agent at a specific position"""
        if position not in self.grid:
            return False
            
        cell = self.grid[position]
        if cell.occupied_by or not cell.terrain.can_move_through():
            return False
            
        cell.occupied_by = agent_id
        cell.visit(agent_id)
        self.agent_positions[agent_id] = position
        
        logger.info(f"Agent {agent_id} placed at {position}")
        return True

    def get_agent_position(self, agent_id: str) -> Optional[GridLocation]:
        """Get the current position of an agent"""
        return self.agent_positions.get(agent_id)

    def find_agent(self, agent_id: str) -> Optional[GridLocation]:
        """Find an agent's position (alias for get_agent_position for backward compatibility)"""
        return self.get_agent_position(agent_id)

    def move_agent(self, agent_id: str, new_position: GridLocation) -> bool:
        """Move an agent to a new position"""
        if agent_id not in self.agent_positions:
            logger.warning(f"Cannot move agent {agent_id}: not found in agent_positions")
            return False
            
        if new_position not in self.grid:
            logger.warning(f"Cannot move agent {agent_id} to {new_position}: position invalid")
            return False
        
        old_position = self.agent_positions[agent_id]
        new_cell = self.grid[new_position]
        old_cell = self.grid[old_position]
        
        # Check if target cell is occupied by another agent
        if new_cell.occupied_by and new_cell.occupied_by != agent_id:
            logger.warning(f"Movement blocked: {new_position} occupied by {new_cell.occupied_by}")
            return False
        
        # Check if target cell allows movement
        if not new_cell.terrain.can_move_through():
            logger.warning(f"Movement blocked: {new_position} terrain impassable")
            return False
        
        # Execute movement
        old_cell.occupied_by = None
        new_cell.occupied_by = agent_id
        new_cell.visit(agent_id)
        self.agent_positions[agent_id] = new_position
        
        # Record movement in history
        self.movement_history.append({
            "agent_id": agent_id,
            "from": old_position,
            "to": new_position,
            "timestamp": time.time()
        })
        
        logger.debug(f"Agent {agent_id} moved from {old_position} to {new_position}")
        return True

    def request_movement(self, agent_id: str, new_position: GridLocation, priority: float = 1.0) -> bool:
        """Request movement with collision avoidance"""
        if agent_id not in self.agent_positions:
            logger.warning(f"Cannot move agent {agent_id}: not found in agent_positions")
            return False
            
        if new_position not in self.grid:
            logger.warning(f"Cannot move agent {agent_id} to {new_position}: position invalid")
            return False
        
        target_cell = self.grid[new_position]
        if not target_cell.terrain.can_move_through():
            logger.warning(f"Cannot move agent {agent_id} to {new_position}: terrain impassable")
            return False
        
        # Add to collision avoidance system
        self.collision_system.request_movement(agent_id, new_position, priority)
        return True

    def execute_movements(self) -> Dict[str, bool]:
        """Execute all pending movements with conflict resolution"""
        movement_results = self.collision_system.resolve_conflicts(self)
        
        for agent_id, can_move in movement_results.items():
            if can_move:
                target = self.collision_system.movement_requests.get(agent_id)
                if target:
                    self.move_agent(agent_id, target)
        
        return movement_results

    def is_within_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within grid bounds"""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_empty(self, x: int, y: int) -> bool:
        """Check if a cell is empty (no agent, passable terrain)"""
        if not self.is_within_bounds(x, y):
            return False
        
        cell = self.grid.get((x, y))
        if not cell:
            return True
        
        return (cell.occupied_by is None and 
                cell.terrain.can_move_through())

    def place(self, x: int, y: int, structure) -> bool:
        """Place a structure at the given coordinates"""
        if not self.is_within_bounds(x, y):
            logger.warning(f"Cannot place structure at ({x}, {y}): out of bounds")
            return False
        
        cell = self.grid.get((x, y))
        if not cell:
            # Create cell if it doesn't exist
            cell = Cell(x, y)
            self.grid[(x, y)] = cell
        
        if cell.structure:
            logger.warning(f"Cannot place structure at ({x}, {y}): already has structure")
            return False
        
        if not cell.terrain.can_build_on():
            logger.warning(f"Cannot place structure at ({x}, {y}): terrain not suitable")
            return False
        
        # Set the structure (assuming it has a built_by attribute)
        if hasattr(structure, 'built_by'):
            cell.structure = structure
        else:
            cell.structure = "building"  # Generic structure type
        
        logger.info(f"Structure placed at ({x}, {y})")
        return True

    def harvest_resources(self, position: GridLocation, resource_type: ResourceType, 
                         amount: int, agent_id: str) -> int:
        """Harvest resources from a cell"""
        if position not in self.grid:
            return 0
        
        cell = self.grid[position]
        harvested = cell.harvest_resource(resource_type, amount)
        
        if harvested > 0:
            self.resource_extraction_log.append({
                "agent_id": agent_id,
                "position": position,
                "resource_type": resource_type.value,
                "amount": harvested,
                "timestamp": time.time()
            })
            logger.debug(f"Agent {agent_id} harvested {harvested} {resource_type.value} at {position}")
        
        return harvested

    def find_path_with_terrain(self, start: GridLocation, goal: GridLocation) -> List[GridLocation]:
        """Find path considering terrain costs (A* pathfinding)"""
        if start == goal:
            return [start]
        
        from heapq import heappush, heappop
        
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}
        
        while open_set:
            current = heappop(open_set)[1]
            
            if current == goal:
                return self._reconstruct_path(came_from, current)
            
            for dx, dy in self.directions:
                neighbor = (current[0] + dx, current[1] + dy)
                
                if not self.is_within_bounds(neighbor[0], neighbor[1]):
                    continue
                
                cell = self.grid.get(neighbor)
                if not cell or not cell.terrain.can_move_through():
                    continue
                
                tentative_g_score = g_score[current] + cell.get_movement_cost()
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal)
                    heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # No path found

    def _heuristic(self, a: GridLocation, b: GridLocation) -> float:
        """Manhattan distance heuristic for pathfinding"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _reconstruct_path(self, came_from: Dict, current: GridLocation) -> List[GridLocation]:
        """Reconstruct path from A* pathfinding"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]

    def serialize(self) -> Dict:
        """Serialize grid state for API responses"""
        cells = {}
        for (x, y), cell in self.grid.items():
            cells[f"{x},{y}"] = {
                "x": x,
                "y": y,
                "occupied_by": cell.occupied_by,
                "structure": "building" if hasattr(cell.structure, 'built_by') else cell.structure,
                "terrain_type": cell.terrain.terrain_type.value,
                "movement_cost": cell.terrain.movement_cost,
                "can_build": cell.terrain.can_build_on(),
                "resources": {rt.value: dep.amount for rt, dep in cell.terrain.resources.items()}
            }
        
        return {
            "width": self.width,
            "height": self.height,
            "cells": cells,
            "agent_positions": self.agent_positions,
            "total_cells": len(self.grid)
        }

    def update_resources(self):
        """Update resource regeneration for all cells"""
        for cell in self.grid.values():
            cell.update_resources()

    def get_performance_metrics(self) -> Dict:
        """Get grid performance metrics"""
        return {
            "total_movements": len(self.movement_history),
            "resource_extractions": len(self.resource_extraction_log),
            "active_agents": len(self.agent_positions),
            "occupied_cells": sum(1 for cell in self.grid.values() if cell.occupied_by),
            "structures": sum(1 for cell in self.grid.values() if cell.structure),
            "recent_movements": self.movement_history[-10:] if self.movement_history else []
        }
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
                    self._execute_single_movement(agent_id, target)
        
        return movement_results

    def _execute_single_movement(self, agent_id: str, new_position: GridLocation) -> bool:
        """Execute a single agent movement"""
        old_position = self.agent_positions[agent_id]
        old_cell = self.grid[old_position]
        new_cell = self.grid[new_position]
        
        # Check if target cell is occupied
        if new_cell.occupied_by and new_cell.occupied_by != agent_id:
            logger.warning(f"Movement blocked: {new_position} occupied by {new_cell.occupied_by}")
            return False
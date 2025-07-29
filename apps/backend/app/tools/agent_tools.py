# apps/backend/app/tools/agent_tools.py

import logging
import time
import heapq
from typing import List, Tuple, Dict, Set, Optional
from app.agents.base import BaseTool, ToolResult
from app.env.grid import Grid
from app.tools.message import Message, MessageType, MessagePriority

logger = logging.getLogger(__name__)

class PathfindingTool(BaseTool):
    """A* pathfinding algorithm for navigation"""
    
    def __init__(self, grid: Grid):
        super().__init__("pathfinding", "Find optimal path between two points using A* algorithm")
        self.grid = grid
    
    def execute(self, agent_id: str, start: Tuple[int, int], goal: Tuple[int, int], 
                avoid_agents: bool = True) -> ToolResult:
        """Find path from start to goal"""
        try:
            path = self._a_star(start, goal, avoid_agents)
            return ToolResult(
                success=True,
                result=path,
                metadata={
                    "path_length": len(path),
                    "start": start,
                    "goal": goal,
                    "avoid_agents": avoid_agents
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
    
    def _a_star(self, start: Tuple[int, int], goal: Tuple[int, int], avoid_agents: bool) -> List[Tuple[int, int]]:
        """A* pathfinding implementation"""
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == goal:
                return self._reconstruct_path(came_from, current)
            
            for neighbor in self._get_neighbors(current):
                if not self._is_valid_move(neighbor, avoid_agents):
                    continue
                
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # No path found
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Manhattan distance heuristic"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions"""
        x, y = pos
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.grid.is_within_bounds(nx, ny):
                neighbors.append((nx, ny))
        return neighbors
    
    def _is_valid_move(self, pos: Tuple[int, int], avoid_agents: bool) -> bool:
        """Check if position is valid for movement"""
        if avoid_agents:
            return self.grid.is_empty(pos[0], pos[1])
        else:
            cell = self.grid.grid.get(pos)
            return cell is None or cell.structure != "wall"  # Avoid walls but allow agents
    
    def _reconstruct_path(self, came_from: Dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Reconstruct path from A* result"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]

class AreaScanTool(BaseTool):
    """Scan a larger area around the agent"""
    
    def __init__(self, grid: Grid):
        super().__init__("area_scan", "Scan area around current position for detailed reconnaissance")
        self.grid = grid
    
    def execute(self, agent_id: str, radius: int = 2) -> ToolResult:
        """Scan area around agent position"""
        try:
            agent_pos = self.grid.get_agent_position(agent_id)
            if not agent_pos:
                return ToolResult(success=False, error="Agent position not found")
            
            scan_results = self._scan_area(agent_pos, radius)
            
            return ToolResult(
                success=True,
                result=scan_results,
                metadata={
                    "center": agent_pos,
                    "radius": radius,
                    "cells_scanned": len(scan_results["cells"]),
                    "agents_detected": len(scan_results["agents"]),
                    "structures_found": len(scan_results["structures"])
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _scan_area(self, center: Tuple[int, int], radius: int) -> Dict:
        """Perform area scan"""
        cx, cy = center
        scan_data = {
            "cells": [],
            "agents": [],
            "structures": [],
            "empty_spaces": [],
            "terrain_analysis": {}
        }
        
        for x in range(max(0, cx - radius), min(self.grid.width, cx + radius + 1)):
            for y in range(max(0, cy - radius), min(self.grid.height, cy + radius + 1)):
                cell = self.grid.grid.get((x, y))
                cell_info = {
                    "position": (x, y),
                    "distance": abs(x - cx) + abs(y - cy),
                    "occupied_by": cell.occupied_by if cell else None,
                    "structure": cell.structure if cell else None
                }
                
                scan_data["cells"].append(cell_info)
                
                if cell and cell.occupied_by:
                    scan_data["agents"].append(cell_info)
                elif cell and cell.structure:
                    scan_data["structures"].append(cell_info)
                elif not cell or (not cell.occupied_by and not cell.structure):
                    scan_data["empty_spaces"].append(cell_info)
        
        # Add terrain analysis
        scan_data["terrain_analysis"] = {
            "density": len(scan_data["structures"]) / len(scan_data["cells"]),
            "open_space_ratio": len(scan_data["empty_spaces"]) / len(scan_data["cells"]),
            "agent_presence": len(scan_data["agents"]) > 0
        }
        
        return scan_data

class ResourceManagementTool(BaseTool):
    """Manage and track resources"""
    
    def __init__(self, shared_state):
        super().__init__("resource_management", "Request, track, and manage resources")
        self.shared_state = shared_state
    
    def execute(self, agent_id: str, action: str, resource_type: str = None, 
                amount: int = 0) -> ToolResult:
        """Execute resource management action"""
        try:
            if action == "request":
                success = self.shared_state.allocate_resource(agent_id, resource_type, amount)
                return ToolResult(
                    success=success,
                    result={"allocated": amount if success else 0},
                    metadata={"action": action, "resource_type": resource_type, "amount": amount}
                )
            
            elif action == "release":
                self.shared_state.release_resource(agent_id, resource_type, amount)
                return ToolResult(
                    success=True,
                    result={"released": amount},
                    metadata={"action": action, "resource_type": resource_type, "amount": amount}
                )
            
            elif action == "check":
                resources = self.shared_state.get_agent_resources(agent_id)
                return ToolResult(
                    success=True,
                    result=resources,
                    metadata={"action": action, "total_types": len(resources)}
                )
            
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
                
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class ConstructionPlannerTool(BaseTool):
    """Plan construction projects with resource and location optimization"""
    
    def __init__(self, grid: Grid, shared_state):
        super().__init__("construction_planner", "Plan optimal construction projects")
        self.grid = grid
        self.shared_state = shared_state
    
    def execute(self, agent_id: str, project_type: str, constraints: Dict = None) -> ToolResult:
        """Plan a construction project"""
        try:
            constraints = constraints or {}
            plan = self._create_construction_plan(project_type, constraints)
            
            return ToolResult(
                success=True,
                result=plan,
                metadata={
                    "project_type": project_type,
                    "estimated_duration": plan.get("estimated_duration", 0),
                    "resource_requirements": plan.get("resource_requirements", {}),
                    "optimal_locations": len(plan.get("candidate_locations", []))
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _create_construction_plan(self, project_type: str, constraints: Dict) -> Dict:
        """Create detailed construction plan"""
        plan = {
            "project_type": project_type,
            "phases": [],
            "resource_requirements": {},
            "candidate_locations": [],
            "estimated_duration": 0,
            "risk_assessment": {}
        }
        
        if project_type == "basic_building":
            plan.update({
                "phases": [
                    {"name": "site_preparation", "duration": 1, "resources": {"tools": 1}},
                    {"name": "foundation", "duration": 2, "resources": {"materials": 5}},
                    {"name": "construction", "duration": 3, "resources": {"materials": 10, "tools": 2}},
                    {"name": "finishing", "duration": 1, "resources": {"materials": 2}}
                ],
                "resource_requirements": {"materials": 17, "tools": 3},
                "estimated_duration": 7
            })
            
            # Find candidate locations
            plan["candidate_locations"] = self._find_optimal_locations(constraints)
        
        return plan
    
    def _find_optimal_locations(self, constraints: Dict) -> List[Dict]:
        """Find optimal construction locations"""
        candidates = []
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if self.grid.is_empty(x, y):
                    score = self._score_location(x, y, constraints)
                    candidates.append({
                        "position": (x, y),
                        "score": score,
                        "reasons": self._get_location_reasons(x, y)
                    })
        
        # Sort by score and return top candidates
        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[:5]
    
    def _score_location(self, x: int, y: int, constraints: Dict) -> float:
        """Score a location for construction suitability"""
        score = 1.0
        
        # Prefer central locations
        center_x, center_y = self.grid.width // 2, self.grid.height // 2
        distance_from_center = abs(x - center_x) + abs(y - center_y)
        score += (1.0 - distance_from_center / (self.grid.width + self.grid.height)) * 2
        
        # Avoid edges
        if x == 0 or x == self.grid.width - 1 or y == 0 or y == self.grid.height - 1:
            score -= 1.0
        
        # Consider proximity to existing structures
        nearby_structures = 0
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.grid.is_within_bounds(nx, ny):
                cell = self.grid.grid.get((nx, ny))
                if cell and cell.structure:
                    nearby_structures += 1
        
        # Moderate proximity to structures is good (not isolated, not crowded)
        if nearby_structures == 1 or nearby_structures == 2:
            score += 1.0
        elif nearby_structures > 2:
            score -= 0.5
        
        return score
    
    def _get_location_reasons(self, x: int, y: int) -> List[str]:
        """Get reasons why a location is good/bad"""
        reasons = []
        
        center_x, center_y = self.grid.width // 2, self.grid.height // 2
        if abs(x - center_x) <= 1 and abs(y - center_y) <= 1:
            reasons.append("Central location")
        
        if x == 0 or x == self.grid.width - 1 or y == 0 or y == self.grid.height - 1:
            reasons.append("Edge location (less optimal)")
        
        return reasons

class CoordinationTool(BaseTool):
    """Coordinate with other agents and resolve conflicts"""
    
    def __init__(self, coordination_manager):
        super().__init__("coordination", "Coordinate actions and resolve conflicts with other agents")
        self.coordination_manager = coordination_manager
    
    def execute(self, agent_id: str, action: str, target_agent: str = None, 
                message: str = None, conflict_type: str = None) -> ToolResult:
        """Execute coordination action"""
        try:
            if action == "send_coordination_message":
                coord_message = Message(
                    sender=agent_id,
                    recipient=target_agent,
                    content=message,
                    message_type=MessageType.COORDINATION,
                    priority=MessagePriority.HIGH
                )
                success = self.coordination_manager.send_message(coord_message)
                
                return ToolResult(
                    success=success,
                    result={"message_sent": True, "recipient": target_agent},
                    metadata={"action": action, "target": target_agent}
                )
            
            elif action == "detect_conflicts":
                conflicts = self.coordination_manager.detect_conflicts()
                return ToolResult(
                    success=True,
                    result={"conflicts": conflicts},
                    metadata={"action": action, "conflicts_found": len(conflicts)}
                )
            
            elif action == "request_status":
                # Request status from other agents
                status_request = Message(
                    sender=agent_id,
                    recipient=target_agent,
                    content="REQUEST_STATUS",
                    message_type=MessageType.QUERY,
                    priority=MessagePriority.NORMAL,
                    requires_ack=True
                )
                success = self.coordination_manager.send_message(status_request)
                
                return ToolResult(
                    success=success,
                    result={"status_requested": True},
                    metadata={"action": action, "target": target_agent}
                )
            
            else:
                return ToolResult(success=False, error=f"Unknown coordination action: {action}")
                
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class PerformanceMonitorTool(BaseTool):
    """Monitor and analyze agent performance"""
    
    def __init__(self, shared_state):
        super().__init__("performance_monitor", "Monitor and analyze performance metrics")
        self.shared_state = shared_state
    
    def execute(self, agent_id: str, metric_type: str = "all") -> ToolResult:
        """Get performance metrics"""
        try:
            if metric_type == "all":
                metrics = self.shared_state.get_metrics()
            else:
                metrics = {metric_type: self.shared_state.get_metrics().get(metric_type, 0)}
            
            # Add performance analysis
            analysis = self._analyze_performance(metrics)
            
            return ToolResult(
                success=True,
                result={
                    "metrics": metrics,
                    "analysis": analysis,
                    "timestamp": time.time()
                },
                metadata={"metric_type": metric_type, "metrics_count": len(metrics)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _analyze_performance(self, metrics: Dict) -> Dict:
        """Analyze performance metrics"""
        analysis = {
            "trends": {},
            "recommendations": [],
            "efficiency_score": 0.0
        }
        
        # Simple performance analysis
        exploration_progress = metrics.get("exploration_progress", 0)
        buildings_built = metrics.get("buildings_built", 0)
        step_count = metrics.get("step_count", 1)
        
        # Calculate efficiency score
        efficiency = (exploration_progress * 0.5 + buildings_built * 0.1) / (step_count * 0.01)
        analysis["efficiency_score"] = min(efficiency, 1.0)
        
        # Generate recommendations
        if exploration_progress < 0.5:
            analysis["recommendations"].append("Increase exploration efforts")
        if buildings_built == 0 and step_count > 10:
            analysis["recommendations"].append("Begin construction phase")
        if efficiency < 0.3:
            analysis["recommendations"].append("Improve coordination between agents")
        
        return analysis

# Tool factory functions for easy agent initialization
def create_scout_tools(grid: Grid, coordination_manager, shared_state) -> Dict[str, BaseTool]:
    """Create tools specific to scout agents"""
    return {
        "pathfinding": PathfindingTool(grid),
        "area_scan": AreaScanTool(grid),
        "coordination": CoordinationTool(coordination_manager),
        "performance_monitor": PerformanceMonitorTool(shared_state)
    }

def create_builder_tools(grid: Grid, coordination_manager, shared_state) -> Dict[str, BaseTool]:
    """Create tools specific to builder agents"""
    return {
        "resource_management": ResourceManagementTool(shared_state),
        "construction_planner": ConstructionPlannerTool(grid, shared_state),
        "pathfinding": PathfindingTool(grid),
        "coordination": CoordinationTool(coordination_manager)
    }

def create_strategist_tools(grid: Grid, coordination_manager, shared_state) -> Dict[str, BaseTool]:
    """Create tools specific to strategist agents"""
    return {
        "area_scan": AreaScanTool(grid),
        "coordination": CoordinationTool(coordination_manager),
        "performance_monitor": PerformanceMonitorTool(shared_state),
        "resource_management": ResourceManagementTool(shared_state),
        "construction_planner": ConstructionPlannerTool(grid, shared_state)
    }
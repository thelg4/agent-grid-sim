from typing import Optional
import re
from .base import BaseAgent
from app.tools.message import Message
from app.env.grid import Grid
import logging

logger = logging.getLogger(__name__)

class StrategistAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid):
        super().__init__(agent_id, "strategist", grid)
        self.suggested_locations = set()
        self.scout_reports = []
        self.analysis_count = 0
        self.BUILD_TARGET = 5  # Stop at 5 buildings as per mission

    def step(self, messages: list[Message]) -> Optional[Message]:
        """
        Strategist analyzes scout reports and gives strategic build orders.
        """
        # Process scout reports
        new_scout_reports = 0
        for message in messages:
            if hasattr(message, 'sender') and message.sender == "scout" and "SCOUT_REPORT" in message.content:
                self.scout_reports.append(message.content)
                new_scout_reports += 1
        
        self.analysis_count += 1
        
        # Get current buildings count
        buildings_built = self._count_buildings()
        
        logger.info(f"Strategist step {self.analysis_count}: {new_scout_reports} new scout reports, {buildings_built} buildings built")
        logger.info(f"Grid dimensions: {self.grid.width}x{self.grid.height} (0-{self.grid.width-1}, 0-{self.grid.height-1})")
        
        # IMPORTANT: Stop building when we reach the target
        if buildings_built >= self.BUILD_TARGET:
            logger.info(f"Mission complete: {buildings_built} buildings built (target: {self.BUILD_TARGET})")
            self.status = f"Mission complete: {buildings_built}/{self.BUILD_TARGET} buildings"
            return self.send_message(f"MISSION_COMPLETE: Target of {self.BUILD_TARGET} buildings achieved! Total built: {buildings_built}")
        
        # Strategic decision making based on mission phase
        if buildings_built < 2:
            # Early phase: Give specific build orders
            return self._issue_build_order()
        elif buildings_built < 4:
            # Mid phase: Strategic placement
            return self._strategic_placement()
        else:
            # Late phase: Final optimization
            return self._final_optimization()

    def _issue_build_order(self) -> Optional[Message]:
        """Issue specific build orders to the builder."""
        # Get builder's current position to prioritize nearby locations
        builder_pos = self.grid.get_agent_position("builder")
        
        optimal_locations = self._find_optimal_building_locations(builder_pos)
        
        logger.info(f"Found {len(optimal_locations)} optimal locations: {optimal_locations}")
        logger.info(f"Builder is at: {builder_pos}")
        
        for location in optimal_locations:
            x, y = location
            if ((x, y) not in self.suggested_locations and 
                self.grid.is_within_bounds(x, y) and 
                self.grid.is_empty(x, y)):
                
                self.suggested_locations.add((x, y))
                distance_to_builder = abs(x - builder_pos[0]) + abs(y - builder_pos[1]) if builder_pos else "unknown"
                self.status = f"Ordered build at ({x}, {y}) - distance {distance_to_builder}"
                order = f"STRATEGIC_BUILD_ORDER: Build at ({x}, {y}) - high strategic value location"
                logger.info(f"Strategist issuing build order: {order}")
                return self.send_message(order)
        
        # If no optimal locations, analyze situation
        logger.warning("No valid optimal locations found, analyzing situation")
        return self._analyze_situation()

    def _find_optimal_building_locations(self, builder_pos: Optional[tuple[int, int]]) -> list[tuple[int, int]]:
        """Find strategically optimal locations for buildings that are actually valid."""
        candidates = []
        
        logger.info(f"Finding optimal locations on {self.grid.width}x{self.grid.height} grid")
        logger.info(f"Valid coordinates: x=0-{self.grid.width-1}, y=0-{self.grid.height-1}")
        
        # Get scout's explored areas to prioritize building in explored regions
        scout_positions = self._get_scout_explored_areas()
        logger.info(f"Scout has explored areas around: {scout_positions}")
        
        # Calculate actual center coordinates (properly bounded)
        center_x = (self.grid.width - 1) // 2
        center_y = (self.grid.height - 1) // 2
        
        logger.info(f"Grid center calculated as: ({center_x}, {center_y})")
        logger.info(f"Builder position: {builder_pos}")
        
        # Define strategic positions relative to builder, scout exploration, and grid center
        strategic_positions = []
        
        # PRIORITY 1: Locations near builder (within 3 steps)
        if builder_pos:
            bx, by = builder_pos
            for radius in range(1, 4):  # 1-3 steps away
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if abs(dx) + abs(dy) <= radius:  # Manhattan distance
                            x, y = bx + dx, by + dy
                            if self.grid.is_within_bounds(x, y):
                                strategic_positions.append((x, y))
        
        # PRIORITY 2: Locations near scout exploration
        for scout_x, scout_y in scout_positions[:5]:  # Top 5 scout positions
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:
                x, y = scout_x + dx, scout_y + dy
                if (self.grid.is_within_bounds(x, y) and 
                    (x, y) not in strategic_positions):
                    strategic_positions.append((x, y))
        
        # PRIORITY 3: Center positions
        for dx, dy in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            x, y = center_x + dx, center_y + dy
            if (self.grid.is_within_bounds(x, y) and 
                (x, y) not in strategic_positions):
                strategic_positions.append((x, y))
        
        logger.info(f"Strategic positions to evaluate: {strategic_positions[:10]}")  # Log first 10
        
        # Filter and evaluate valid strategic positions
        for x, y in strategic_positions:
            if (self.grid.is_within_bounds(x, y) and 
                self.grid.is_empty(x, y) and 
                (x, y) not in self.suggested_locations):
                
                value = self._calculate_location_value(x, y, scout_positions, builder_pos)
                candidates.append(((x, y), value))
                logger.debug(f"Strategic position ({x}, {y}) has value {value}")
        
        # Sort by strategic value (higher is better)
        candidates.sort(key=lambda item: item[1], reverse=True)
        
        logger.info(f"Final candidates (top 5): {candidates[:5]}")
        
        # Return top 3 locations
        return [location for location, value in candidates[:3]]

    def _get_scout_explored_areas(self) -> list[tuple[int, int]]:
        """Extract scout positions from scout reports."""
        scout_positions = []
        
        for report in self.scout_reports:
            # Parse scout reports for position information
            patterns = [
                r'to \((\d+),\s*(\d+)\)',
                r'At \((\d+),\s*(\d+)\)',
                r'\((\d+),\s*(\d+)\)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, report)
                if match:
                    x, y = int(match.group(1)), int(match.group(2))
                    if self.grid.is_within_bounds(x, y):
                        scout_positions.append((x, y))
                    break
        
        # Remove duplicates and sort by recency (most recent first)
        scout_positions = list(dict.fromkeys(reversed(scout_positions)))
        return scout_positions

    def _strategic_placement(self) -> Optional[Message]:
        """Strategic placement for mid-game."""
        builder_pos = self.grid.get_agent_position("builder")
        best_location = self._find_coverage_location(builder_pos)
        if best_location:
            x, y = best_location
            if ((x, y) not in self.suggested_locations and 
                self.grid.is_within_bounds(x, y) and 
                self.grid.is_empty(x, y)):
                
                self.suggested_locations.add((x, y))
                self.status = f"Strategic placement at ({x}, {y})"
                order = f"STRATEGIC_BUILD_ORDER: Build at ({x}, {y}) - optimal coverage position"
                logger.info(f"Strategist strategic placement: {order}")
                return self.send_message(order)
        
        # Fallback to regular build order
        return self._issue_build_order()

    def _final_optimization(self) -> Optional[Message]:
        """Final phase optimization."""
        # Check if we're at or near the building limit
        buildings_built = self._count_buildings()
        if buildings_built >= self.BUILD_TARGET:
            self.status = f"Mission complete: {buildings_built}/{self.BUILD_TARGET} buildings"
            return self.send_message(f"MISSION_COMPLETE: Target achieved with {buildings_built} buildings")
        
        builder_pos = self.grid.get_agent_position("builder")
        remaining_spots = self._find_remaining_build_spots(builder_pos)
        if remaining_spots:
            x, y = remaining_spots[0]
            if (x, y) not in self.suggested_locations:
                self.suggested_locations.add((x, y))
                self.status = f"Final build at ({x}, {y})"
                order = f"STRATEGIC_BUILD_ORDER: Build at ({x}, {y}) - mission completion"
                logger.info(f"Strategist final build order: {order}")
                return self.send_message(order)
        
        return self._coordinate_agents("Mission nearing completion, maintain current positions")

    def _find_coverage_location(self, builder_pos: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
        """Find location that provides good coverage, preferring locations near builder."""
        candidates = []
        
        center_x = (self.grid.width - 1) // 2
        center_y = (self.grid.height - 1) // 2
        
        # Look for positions in expanding radius from center, but prioritize near builder
        max_radius = min(self.grid.width, self.grid.height) // 2
        for radius in range(1, max_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x, y = center_x + dx, center_y + dy
                    if (self.grid.is_within_bounds(x, y) and 
                        self.grid.is_empty(x, y) and
                        (x, y) not in self.suggested_locations):
                        
                        # Calculate distance to builder
                        builder_distance = 999
                        if builder_pos:
                            builder_distance = abs(x - builder_pos[0]) + abs(y - builder_pos[1])
                        
                        candidates.append((x, y, builder_distance))
        
        # Sort by builder distance (closer is better)
        candidates.sort(key=lambda item: item[2])
        
        return candidates[0][:2] if candidates else None

    def _find_remaining_build_spots(self, builder_pos: Optional[tuple[int, int]]) -> list[tuple[int, int]]:
        """Find remaining good spots for building, prioritizing near builder."""
        spots = []
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if (self.grid.is_empty(x, y) and 
                    (x, y) not in self.suggested_locations):
                    
                    # Calculate distance to builder
                    builder_distance = 999
                    if builder_pos:
                        builder_distance = abs(x - builder_pos[0]) + abs(y - builder_pos[1])
                    
                    spots.append((x, y, builder_distance))
        
        # Sort by distance to builder (closer first)
        spots.sort(key=lambda item: item[2])
        return [(x, y) for x, y, _ in spots]

    def _count_buildings(self) -> int:
        """Count existing buildings on the grid."""
        count = 0
        for cell in self.grid.grid.values():
            if cell.structure and cell.structure != "scanned":
                count += 1
        return count

    def _analyze_situation(self) -> Optional[Message]:
        """Analyze current grid state and provide strategic assessment."""
        # Count empty spaces and existing structures
        empty_spaces = 0
        structures = 0
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if self.grid.is_empty(x, y):
                    empty_spaces += 1
                cell = self.grid.grid.get((x, y))
                if cell and cell.structure:
                    structures += 1
        
        scout_reports_count = len([msg for msg in self.scout_reports if "SCOUT_REPORT" in msg])
        builder_pos = self.grid.get_agent_position("builder")
        
        analysis = f"STRATEGIC_ANALYSIS: {empty_spaces} empty spaces, {structures}/{self.BUILD_TARGET} buildings built, {scout_reports_count} scout reports, builder at {builder_pos}"
        self.status = "Analyzing battlefield"
        logger.info(f"Strategist analysis: {analysis}")
        return self.send_message(analysis)

    def _coordinate_agents(self, message: str) -> Optional[Message]:
        """Send coordination message to other agents."""
        self.status = "Coordinating team"
        coord_msg = f"COORDINATION: {message}"
        logger.info(f"Strategist coordination: {coord_msg}")
        return self.send_message(coord_msg)

    def _calculate_location_value(self, x: int, y: int, scout_positions: list[tuple[int, int]], builder_pos: Optional[tuple[int, int]]) -> float:
        """Calculate strategic value of a location."""
        value = 0.0
        
        # HIGHEST PRIORITY: Distance to builder (closer is much better)
        if builder_pos:
            builder_distance = abs(x - builder_pos[0]) + abs(y - builder_pos[1])
            value += max(0, 10 - builder_distance)  # Heavy weight for builder proximity
        
        # Higher value for locations near scout's explored areas
        if scout_positions:
            min_distance_to_scout = min(
                abs(x - sx) + abs(y - sy) for sx, sy in scout_positions
            )
            value += max(0, 5 - min_distance_to_scout)
        
        # Prefer locations near the center (but lower priority)
        center_x = (self.grid.width - 1) // 2
        center_y = (self.grid.height - 1) // 2
        distance_from_center = abs(x - center_x) + abs(y - center_y)
        max_distance = max(self.grid.width, self.grid.height)
        value += (max_distance - distance_from_center) * 0.3
        
        # Avoid locations too close to existing structures
        min_distance_to_structure = float('inf')
        for (sx, sy), cell in self.grid.grid.items():
            if cell.structure:
                distance = abs(x - sx) + abs(y - sy)
                min_distance_to_structure = min(min_distance_to_structure, distance)
        
        if min_distance_to_structure != float('inf') and min_distance_to_structure > 0:
            value += min(min_distance_to_structure, 2)
        
        # Small penalty for edge locations
        if x == 0 or x == self.grid.width - 1 or y == 0 or y == self.grid.height - 1:
            value -= 1
        
        return value

    def get_status(self) -> dict:
        """Get strategist status with analysis metrics."""
        base_status = super().get_status()
        base_status.update({
            "scout_reports_received": len(self.scout_reports),
            "build_orders_issued": len(self.suggested_locations),
            "analysis_cycles": self.analysis_count,
            "building_target": self.BUILD_TARGET,
            "buildings_completed": self._count_buildings()
        })
        return base_status
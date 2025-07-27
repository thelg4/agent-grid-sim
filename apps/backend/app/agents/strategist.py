from typing import Optional
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
        logger.info(f"Grid dimensions: {self.grid.width}x{self.grid.height}")
        
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
        optimal_locations = self._find_optimal_building_locations()
        
        logger.info(f"Found {len(optimal_locations)} optimal locations: {optimal_locations}")
        
        for location in optimal_locations:
            x, y = location
            if ((x, y) not in self.suggested_locations and 
                self.grid.is_within_bounds(x, y) and 
                self.grid.is_empty(x, y)):
                
                self.suggested_locations.add((x, y))
                self.status = f"Ordered build at ({x}, {y})"
                order = f"STRATEGIC_BUILD_ORDER: Build at ({x}, {y}) - high strategic value location"
                logger.info(f"Strategist issuing build order: {order}")
                return self.send_message(order)
        
        # If no optimal locations, analyze situation
        logger.warning("No valid optimal locations found, analyzing situation")
        return self._analyze_situation()

    def _find_optimal_building_locations(self) -> list[tuple[int, int]]:
        """Find strategically optimal locations for buildings that are actually valid."""
        candidates = []
        
        logger.info(f"Finding optimal locations on {self.grid.width}x{self.grid.height} grid")
        
        # Create strategic positions based on actual grid size
        center_x, center_y = self.grid.width // 2, self.grid.height // 2
        
        # Define strategic positions relative to grid size
        strategic_positions = [
            (center_x, center_y),  # Center
            (center_x - 1, center_y),  # Left of center
            (center_x + 1, center_y),  # Right of center
            (center_x, center_y - 1),  # Above center
            (center_x, center_y + 1),  # Below center
            (1, 1),  # Corner strategic position
            (self.grid.width - 2, 1),  # Other corner
            (1, self.grid.height - 2),  # Another corner
        ]
        
        logger.info(f"Strategic positions to evaluate: {strategic_positions}")
        
        # Filter and evaluate valid strategic positions
        for x, y in strategic_positions:
            if (self.grid.is_within_bounds(x, y) and 
                self.grid.is_empty(x, y) and 
                (x, y) not in self.suggested_locations):
                
                value = self._calculate_location_value(x, y)
                candidates.append(((x, y), value))
                logger.info(f"Strategic position ({x}, {y}) has value {value}")
        
        # Also evaluate all empty positions if we need more options
        if len(candidates) < 3:
            logger.info("Not enough strategic positions, evaluating all empty cells")
            for x in range(self.grid.width):
                for y in range(self.grid.height):
                    if (self.grid.is_empty(x, y) and 
                        (x, y) not in self.suggested_locations and
                        (x, y) not in [pos for pos, _ in candidates]):
                        
                        value = self._calculate_location_value(x, y)
                        if value > 3:  # Only consider decent positions
                            candidates.append(((x, y), value))
        
        # Sort by strategic value (higher is better)
        candidates.sort(key=lambda item: item[1], reverse=True)
        
        logger.info(f"Final candidates: {candidates[:5]}")  # Log top 5
        
        # Return top 3 locations
        return [location for location, value in candidates[:3]]

    def _strategic_placement(self) -> Optional[Message]:
        """Strategic placement for mid-game."""
        best_location = self._find_coverage_location()
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
        remaining_spots = self._find_remaining_build_spots()
        if remaining_spots:
            x, y = remaining_spots[0]
            if (x, y) not in self.suggested_locations:
                self.suggested_locations.add((x, y))
                self.status = f"Final build at ({x}, {y})"
                order = f"STRATEGIC_BUILD_ORDER: Build at ({x}, {y}) - mission completion"
                logger.info(f"Strategist final build order: {order}")
                return self.send_message(order)
        
        return self._coordinate_agents("Mission nearing completion, maintain current positions")

    def _find_coverage_location(self) -> Optional[tuple[int, int]]:
        """Find location that provides good coverage."""
        center_x, center_y = self.grid.width // 2, self.grid.height // 2
        
        # Look for positions near center that aren't taken
        for radius in range(1, max(self.grid.width, self.grid.height) // 2):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x, y = center_x + dx, center_y + dy
                    if (self.grid.is_within_bounds(x, y) and 
                        self.grid.is_empty(x, y) and
                        (x, y) not in self.suggested_locations):
                        return (x, y)
        return None

    def _find_remaining_build_spots(self) -> list[tuple[int, int]]:
        """Find remaining good spots for building."""
        spots = []
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if (self.grid.is_empty(x, y) and 
                    (x, y) not in self.suggested_locations):
                    spots.append((x, y))
        return spots

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
        
        analysis = f"STRATEGIC_ANALYSIS: {empty_spaces} empty spaces available, {structures} structures built, {scout_reports_count} scout reports received"
        self.status = "Analyzing battlefield"
        logger.info(f"Strategist analysis: {analysis}")
        return self.send_message(analysis)

    def _coordinate_agents(self, message: str) -> Optional[Message]:
        """Send coordination message to other agents."""
        self.status = "Coordinating team"
        coord_msg = f"COORDINATION: {message}"
        logger.info(f"Strategist coordination: {coord_msg}")
        return self.send_message(coord_msg)

    def _calculate_location_value(self, x: int, y: int) -> float:
        """Calculate strategic value of a location."""
        value = 0.0
        
        # Prefer locations near the center
        center_x, center_y = self.grid.width // 2, self.grid.height // 2
        distance_from_center = abs(x - center_x) + abs(y - center_y)
        max_distance = max(self.grid.width, self.grid.height)
        value += (max_distance - distance_from_center)  # Closer to center = higher value
        
        # Avoid locations too close to existing structures
        min_distance_to_structure = float('inf')
        for (sx, sy), cell in self.grid.grid.items():
            if cell.structure:
                distance = abs(x - sx) + abs(y - sy)
                min_distance_to_structure = min(min_distance_to_structure, distance)
        
        if min_distance_to_structure != float('inf') and min_distance_to_structure > 0:
            value += min(min_distance_to_structure, 3)  # Reward some distance from existing structures
        
        # Prefer locations with good coverage (not in corners unless strategic)
        if x == 0 or x == self.grid.width - 1 or y == 0 or y == self.grid.height - 1:
            value -= 1  # Small penalty for edge locations
        
        return value

    def get_status(self) -> dict:
        """Get strategist status with analysis metrics."""
        base_status = super().get_status()
        base_status.update({
            "scout_reports_received": len(self.scout_reports),
            "build_orders_issued": len(self.suggested_locations),
            "analysis_cycles": self.analysis_count
        })
        return base_status
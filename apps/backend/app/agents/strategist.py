from typing import Optional
from .base import BaseAgent
from app.tools.message import Message
from app.env.grid import Grid

class StrategistAgent(BaseAgent):
    def __init__(self, agent_id: str, grid: Grid):
        super().__init__(agent_id, "strategist", grid)
        self.suggested_locations = set()
        self.scout_reports = []

    def step(self, messages: list[Message]) -> Optional[Message]:
        """
        Strategist analyzes scout reports and suggests optimal building locations.
        """
        # Process scout reports
        for message in messages:
            if message.sender == "scout" and "report" in message.content.lower():
                self.scout_reports.append(message.content)
        
        # Get LLM decision based on current state and scout reports
        llm_action = self.get_llm_decision(messages)
        
        # Parse and execute action
        action_parts = llm_action.split()
        if not action_parts:
            return None
            
        action = action_parts[0].upper()
        
        if action == "SUGGEST_BUILD" and len(action_parts) > 1:
            return self._suggest_building_location(action_parts[1])
        elif action == "ANALYZE":
            return self._analyze_situation()
        elif action == "COORDINATE" and len(action_parts) > 1:
            message_content = " ".join(action_parts[1:])
            return self._coordinate_agents(message_content)
        else:
            # Default strategic behavior
            return self._default_strategy()

    def _suggest_building_location(self, location_str: str) -> Optional[Message]:
        """Suggest a specific building location to the builder."""
        try:
            # Parse coordinates from format like "(2,3)" or "2,3"
            coords = location_str.strip("()")
            x, y = map(int, coords.split(","))
            
            if self.grid.is_within_bounds(x, y) and self.grid.is_empty(x, y):
                if (x, y) not in self.suggested_locations:
                    self.suggested_locations.add((x, y))
                    self.status = f"Suggested building at ({x}, {y})"
                    return self.send_message(f"STRATEGIC_BUILD_ORDER: Build at ({x}, {y}) - optimal location identified")
                else:
                    self.status = "Location already suggested"
                    return None
            else:
                self.status = f"Invalid location ({x}, {y})"
                return None
                
        except Exception as e:
            self.status = f"Failed to parse location: {location_str}"
            return None

    def _analyze_situation(self) -> Optional[Message]:
        """Analyze current grid state and provide strategic assessment."""
        observation = self.observe()
        
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
        
        analysis = f"STRATEGIC_ANALYSIS: {empty_spaces} empty spaces available, {structures} structures built, {len(self.scout_reports)} scout reports received"
        self.status = "Analyzing battlefield"
        return self.send_message(analysis)

    def _coordinate_agents(self, message: str) -> Optional[Message]:
        """Send coordination message to other agents."""
        self.status = "Coordinating team"
        return self.send_message(f"COORDINATION: {message}")

    def _default_strategy(self) -> Optional[Message]:
        """Default strategic behavior when no specific action is determined."""
        # Look for empty spaces to suggest for building
        best_locations = self._find_optimal_building_locations()
        
        if best_locations:
            x, y = best_locations[0]  # Take the first optimal location
            if (x, y) not in self.suggested_locations:
                self.suggested_locations.add((x, y))
                self.status = f"Identified optimal location ({x}, {y})"
                return self.send_message(f"STRATEGIC_BUILD_ORDER: Build at ({x}, {y}) - strategic value high")
        
        # If no building locations, analyze situation
        return self._analyze_situation()

    def _find_optimal_building_locations(self) -> list[tuple[int, int]]:
        """Find strategically optimal locations for buildings."""
        candidates = []
        
        # Strategy: Prefer locations that are:
        # 1. Not too close to existing structures
        # 2. Have good coverage of the grid
        # 3. Are accessible
        
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if self.grid.is_empty(x, y):
                    # Calculate strategic value
                    value = self._calculate_location_value(x, y)
                    candidates.append(((x, y), value))
        
        # Sort by strategic value (higher is better)
        candidates.sort(key=lambda item: item[1], reverse=True)
        
        # Return top 3 locations
        return [location for location, value in candidates[:3]]

    def _calculate_location_value(self, x: int, y: int) -> float:
        """Calculate strategic value of a location."""
        value = 0.0
        
        # Prefer locations near the center
        center_x, center_y = self.grid.width // 2, self.grid.height // 2
        distance_from_center = abs(x - center_x) + abs(y - center_y)
        value += 10 - distance_from_center  # Closer to center = higher value
        
        # Avoid locations too close to existing structures
        min_distance_to_structure = float('inf')
        for (sx, sy), cell in self.grid.grid.items():
            if cell.structure:
                distance = abs(x - sx) + abs(y - sy)
                min_distance_to_structure = min(min_distance_to_structure, distance)
        
        if min_distance_to_structure != float('inf'):
            value += min_distance_to_structure  # Further from structures = higher value
        
        # Prefer locations with good coverage (not in corners)
        if x == 0 or x == self.grid.width - 1 or y == 0 or y == self.grid.height - 1:
            value -= 2  # Penalty for edge locations
        
        return value
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import openai
import os
import logging
from app.env.grid import Grid
from app.tools.message import Message

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_id: str, role: str, grid: Grid):
        self.agent_id = agent_id
        self.role = role
        self.grid = grid
        self.status = "Initializing"
        self.memory: List[str] = []
        
        # Initialize OpenAI client with better error handling
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error(f"OPENAI_API_KEY not found for agent {agent_id}")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        try:
            self.client = openai.OpenAI(api_key=api_key)
            self._add_to_memory(f"Agent {agent_id} initialized successfully")
            logger.info(f"OpenAI client initialized for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client for {agent_id}: {e}")
            raise
        
        # Define role-specific system prompts
        self.system_prompts = {
            "scout": """You are a Scout agent in a grid-based simulation. Your role is to explore the environment and gather information.
            
            Available actions:
            - MOVE <direction>: Move in a direction (north, south, east, west)
            - OBSERVE: Get detailed information about your surroundings
            - REPORT <message>: Send information to other agents

            Current objective: Explore the grid systematically and report findings to other agents.
            Always respond with a single action in the format above.""",

                        "builder": """You are a Builder agent in a grid-based simulation. Your role is to construct buildings when instructed.
                        
            Available actions:
            - BUILD <x,y>: Construct a building at coordinates (x,y)
            - MOVE <direction>: Move in a direction (north, south, east, west)
            - WAIT: Wait for instructions

            Current objective: Build structures when requested by the Strategist or when you identify good locations.
            Always respond with a single action in the format above.""",

                        "strategist": """You are a Strategist agent in a grid-based simulation. Your role is to analyze the situation and make strategic decisions.
                        
            Available actions:
            - ANALYZE: Analyze the current grid state and agent positions
            - SUGGEST_BUILD <x,y>: Suggest a building location to the Builder
            - COORDINATE <message>: Send coordination messages to other agents

            Current objective: Develop strategic plans and coordinate other agents effectively.
            Always respond with a single action in the format above."""
        }

    @abstractmethod
    def step(self, messages: List[Message]) -> Optional[Message]:
        """Perform a single step in the simulation."""
        pass

    def _add_to_memory(self, entry: str):
        """Add an entry to agent memory with timestamp-like info."""
        # Truncate entry if too long
        if len(entry) > 100:
            entry = entry[:97] + "..."
        
        self.memory.append(entry)
        
        # Keep only the last 10 entries to prevent memory bloat
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]
        
        logger.debug(f"Agent {self.agent_id} memory updated: {entry}")

    def observe(self) -> Dict:
        """Get local view of the grid."""
        position = self.grid.get_agent_position(self.agent_id)
        if not position:
            return {"location": None, "surroundings": []}
            
        x, y = position
        surroundings = []
        
        # Check adjacent cells
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.grid.is_within_bounds(nx, ny):
                cell_key = f"{nx},{ny}"
                cell = self.grid.grid.get((nx, ny))
                if cell:
                    surroundings.append({
                        "position": (nx, ny),
                        "occupied_by": cell.occupied_by,
                        "structure": cell.structure
                    })
        
        return {
            "location": position,
            "surroundings": surroundings,
            "grid_size": (self.grid.width, self.grid.height)
        }

    def get_llm_decision(self, messages: List[Message]) -> str:
        """Get decision from LLM based on current state and messages."""
        try:
            # Prepare context
            observation = self.observe()
            recent_messages = [msg.content for msg in messages[-5:]]  # Last 5 messages
            
            user_prompt = f"""Current situation:
                - My position: {observation['location']}
                - Grid size: {observation['grid_size']}
                - Nearby cells: {observation['surroundings']}
                - Recent messages: {recent_messages}
                - My recent memory: {self.memory[-3:]}

                Based on this information, what should I do next?"""

            response = self.client.chat.completions.create(
                model=os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": self.system_prompts.get(self.role, "You are a helpful agent.")},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=int(os.getenv("MAX_TOKENS", 100)),
                temperature=float(os.getenv("TEMPERATURE", 0.7))
            )
            
            decision = response.choices[0].message.content.strip()
            self._add_to_memory(f"LLM decision: {decision}")
            logger.debug(f"Agent {self.agent_id} LLM decision: {decision}")
            return decision
        
        except Exception as e:
            logger.error(f"LLM error for {self.agent_id}: {e}")
            self._add_to_memory(f"LLM call failed: {str(e)}")
            return "WAIT"  # Default fallback action

    def send_message(self, content: str) -> Message:
        """Create a message from this agent."""
        # Add to memory when sending messages
        self._add_to_memory(f"Sent: {content}")
        return Message(sender=self.agent_id, content=content)

    def update_status(self, new_status: str):
        """Update agent status and add to memory."""
        self.status = new_status
        self._add_to_memory(f"Status: {new_status}")

    def get_status(self) -> Dict:
        return {
            "id": self.agent_id,
            "role": self.role,
            "status": self.status,
            "memory": self.memory.copy(),  # Return a copy to prevent external modification
            "position": self.grid.get_agent_position(self.agent_id)
        }
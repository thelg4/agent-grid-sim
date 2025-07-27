# from abc import ABC, abstractmethod
# from typing import List, Dict, Optional

# from app.env.grid import Grid


# class BaseAgent(ABC):
#     def __init__(self, agent_id: str, role: str, grid: Grid):
#         self.agent_id = agent_id
#         self.role = role
#         self.grid = grid
#         self.status = "Idle"
#         self.memory: List[str] = []

#     @abstractmethod
#     def step(self):
#         """Perform a single step in the simulation."""
#         pass

#     def observe(self) -> Dict:
#         """Get local view of the grid (stub for now)."""
#         return {
#             "location": self.grid.get_agent_position(self.agent_id),
#             "surroundings": [],  # could be expanded later
#         }

#     def send_message(self, message: str):
#         self.memory.append(message)

#     def get_status(self) -> Dict:
#         return {
#             "id": self.agent_id,
#             "role": self.role,
#             "status": self.status,
#             "memory": self.memory[-5:],  # return last 5 messages
#         }

# app/agents/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import openai
import os
from app.env.grid import Grid
from app.tools.message import Message


class BaseAgent(ABC):
    def __init__(self, agent_id: str, role: str, grid: Grid):
        self.agent_id = agent_id
        self.role = role
        self.grid = grid
        self.status = "Idle"
        self.memory: List[str] = []
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
            Always respond with a single action in the format above.""",
        }

    @abstractmethod
    def step(self, messages: List[Message]) -> Optional[Message]:
        """Perform a single step in the simulation."""
        pass

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
                    surroundings.append(
                        {
                            "position": (nx, ny),
                            "occupied_by": cell.occupied_by,
                            "structure": cell.structure,
                        }
                    )

        return {
            "location": position,
            "surroundings": surroundings,
            "grid_size": (self.grid.width, self.grid.height),
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
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompts.get(
                            self.role, "You are a helpful agent."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=100,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"LLM error for {self.agent_id}: {e}")
            return "WAIT"  # Default fallback action

    def send_message(self, content: str) -> Message:
        """Create a message from this agent."""
        self.memory.append(f"[{self.agent_id}] {content}")
        return Message(sender=self.agent_id, content=content)

    def get_status(self) -> Dict:
        return {
            "id": self.agent_id,
            "role": self.role,
            "status": self.status,
            "memory": self.memory[-5:],  # return last 5 messages
            "position": self.grid.get_agent_position(self.agent_id),
        }

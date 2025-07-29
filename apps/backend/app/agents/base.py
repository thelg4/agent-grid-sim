# apps/backend/app/agents/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Set
import openai
import os
import logging
import time
import json
from dataclasses import dataclass, field
from enum import Enum
from app.env.grid import Grid
from app.tools.message import Message, MessageType, MessagePriority
from app.tools.message_queue import CoordinationManager, SharedState

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    SHORT_TERM = "short_term"  # Last few actions/observations
    LONG_TERM = "long_term"    # Important experiences and learnings
    EPISODIC = "episodic"      # Specific event sequences
    SEMANTIC = "semantic"      # General knowledge and rules

@dataclass
class MemoryEntry:
    content: str
    memory_type: MemoryType
    timestamp: float = field(default_factory=time.time)
    importance: float = 1.0  # 0.0 to 1.0
    associated_data: Dict[str, Any] = field(default_factory=dict)
    retrieval_count: int = 0
    last_accessed: float = field(default_factory=time.time)

@dataclass
class ToolResult:
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseTool(ABC):
    """Base class for agent tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.usage_count = 0
        self.success_rate = 1.0
        
    @abstractmethod
    def execute(self, agent_id: str, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def update_stats(self, success: bool):
        """Update tool usage statistics"""
        self.usage_count += 1
        # Update success rate with exponential moving average
        alpha = 0.1
        self.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * self.success_rate

class MemorySystem:
    """Advanced memory system for agents"""
    
    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self.memories: Dict[MemoryType, List[MemoryEntry]] = {
            memory_type: [] for memory_type in MemoryType
        }
        self.importance_threshold = 0.5
        
    def store(self, content: str, memory_type: MemoryType, importance: float = 1.0, **metadata):
        """Store a memory entry"""
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            importance=importance,
            associated_data=metadata
        )
        
        self.memories[memory_type].append(entry)
        
        # Prune old memories if we exceed capacity
        if len(self.memories[memory_type]) > self.max_entries // len(MemoryType):
            self._prune_memories(memory_type)
    
    def retrieve(self, query: str, memory_type: Optional[MemoryType] = None, 
                 limit: int = 5) -> List[MemoryEntry]:
        """Retrieve relevant memories"""
        relevant_memories = []
        
        search_types = [memory_type] if memory_type else list(MemoryType)
        
        for mem_type in search_types:
            for memory in self.memories[mem_type]:
                # Simple keyword matching - could be enhanced with embeddings
                if any(word.lower() in memory.content.lower() for word in query.split()):
                    memory.retrieval_count += 1
                    memory.last_accessed = time.time()
                    relevant_memories.append(memory)
        
        # Sort by relevance (importance + recency + retrieval frequency)
        relevant_memories.sort(
            key=lambda m: m.importance * (1 + m.retrieval_count) * (1 / (time.time() - m.last_accessed + 1)),
            reverse=True
        )
        
        return relevant_memories[:limit]
    
    def get_recent(self, memory_type: MemoryType, limit: int = 10) -> List[MemoryEntry]:
        """Get recent memories of a specific type"""
        return sorted(
            self.memories[memory_type],
            key=lambda m: m.timestamp,
            reverse=True
        )[:limit]
    
    def _prune_memories(self, memory_type: MemoryType):
        """Remove least important memories"""
        memories = self.memories[memory_type]
        
        # Keep memories above importance threshold and recent memories
        current_time = time.time()
        keep_memories = [
            m for m in memories
            if m.importance >= self.importance_threshold or 
            (current_time - m.timestamp) < 3600  # Keep last hour
        ]
        
        # If still too many, keep the most important ones
        if len(keep_memories) > self.max_entries // len(MemoryType):
            keep_memories.sort(key=lambda m: m.importance, reverse=True)
            keep_memories = keep_memories[:self.max_entries // len(MemoryType)]
        
        self.memories[memory_type] = keep_memories

class PlanningSystem:
    """Multi-step planning and reasoning system"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.current_plan: List[Dict] = []
        self.plan_history: List[Dict] = []
        self.execution_log: List[Dict] = []
        
    def create_plan(self, goal: str, context: Dict) -> List[Dict]:
        """Create a multi-step plan to achieve a goal"""
        plan_steps = []
        
        # This is a simplified planning system - could be enhanced with more sophisticated algorithms
        if "explore" in goal.lower():
            plan_steps = [
                {"action": "assess_current_position", "priority": 1},
                {"action": "identify_unexplored_areas", "priority": 2},
                {"action": "plan_exploration_route", "priority": 3},
                {"action": "execute_movement", "priority": 4},
                {"action": "report_findings", "priority": 5}
            ]
        elif "build" in goal.lower():
            plan_steps = [
                {"action": "analyze_build_location", "priority": 1},
                {"action": "check_resources", "priority": 2},
                {"action": "plan_construction", "priority": 3},
                {"action": "execute_building", "priority": 4},
                {"action": "verify_completion", "priority": 5}
            ]
        elif "coordinate" in goal.lower():
            plan_steps = [
                {"action": "gather_agent_status", "priority": 1},
                {"action": "analyze_conflicts", "priority": 2},
                {"action": "generate_solution", "priority": 3},
                {"action": "communicate_plan", "priority": 4},
                {"action": "monitor_execution", "priority": 5}
            ]
        
        self.current_plan = plan_steps
        return plan_steps
    
    def execute_next_step(self) -> Optional[Dict]:
        """Get the next step to execute"""
        if self.current_plan:
            next_step = self.current_plan.pop(0)
            self.execution_log.append({
                "step": next_step,
                "timestamp": time.time(),
                "status": "executing"
            })
            return next_step
        return None
    
    def update_step_status(self, step: Dict, status: str, result: Any = None):
        """Update the status of an executed step"""
        for log_entry in reversed(self.execution_log):
            if log_entry["step"] == step:
                log_entry["status"] = status
                log_entry["result"] = result
                log_entry["completed_at"] = time.time()
                break

class BaseAgent(ABC):
    def __init__(self, agent_id: str, role: str, grid: Grid, 
                 coordination_manager: CoordinationManager = None,
                 shared_state: SharedState = None):
        self.agent_id = agent_id
        self.role = role
        self.grid = grid
        self.coordination_manager = coordination_manager
        self.shared_state = shared_state
        self.status = "Initializing"
        
        # Enhanced memory and planning systems
        self.memory_system = MemorySystem()
        self.planning_system = PlanningSystem(agent_id)
        self.tools: Dict[str, BaseTool] = {}
        self.capabilities: Set[str] = set()
        
        # Performance tracking
        self.performance_metrics = {
            "actions_taken": 0,
            "successful_actions": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "planning_cycles": 0,
            "tool_usage": {},
            "average_response_time": 0.0
        }
        
        # Learning system
        self.learning_data = {
            "successful_strategies": [],
            "failed_strategies": [],
            "environmental_patterns": {},
            "collaboration_effectiveness": {}
        }
        
        # Initialize OpenAI client with better error handling
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error(f"OPENAI_API_KEY not found for agent {agent_id}")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        try:
            self.client = openai.OpenAI(api_key=api_key)
            self._store_memory(f"Agent {agent_id} initialized successfully", MemoryType.EPISODIC, importance=0.8)
            logger.info(f"OpenAI client initialized for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client for {agent_id}: {e}")
            raise
        
        # Define enhanced role-specific system prompts
        self.system_prompts = self._get_system_prompts()

    def _get_system_prompts(self) -> Dict[str, str]:
        """Get enhanced system prompts for different roles"""
        return {
            "scout": """You are an advanced Scout agent in a multi-agent grid-based simulation. 

Your capabilities include:
- Systematic exploration and mapping
- Environmental reconnaissance and analysis
- Pathfinding and navigation optimization
- Intelligence gathering and reporting
- Collaborative coordination with other agents

Available tools and actions:
- MOVE <direction>: Move in a direction (north, south, east, west)
- OBSERVE: Get detailed information about surroundings
- SCAN_AREA <radius>: Scan a wider area around current position
- REPORT <message>: Send intelligence to other agents
- REQUEST_RESOURCE <type> <amount>: Request resources from shared pool
- PLAN <objective>: Create a multi-step plan for complex objectives

Memory and learning:
- Remember previously explored areas and their characteristics
- Learn from successful exploration patterns
- Adapt strategies based on environmental feedback
- Coordinate with other agents to avoid redundant exploration

Current objective: Conduct systematic exploration while optimizing for coverage and efficiency.
Provide detailed reports to support strategic decision-making by other agents.
Always respond with a single action in the specified format.""",

            "builder": """You are an advanced Builder agent in a multi-agent grid-based simulation.

Your capabilities include:
- Construction planning and execution
- Resource management and optimization
- Quality control and verification
- Collaborative building coordination
- Infrastructure development

Available tools and actions:
- BUILD <x,y>: Construct a building at coordinates (x,y)
- MOVE <direction>: Move in a direction (north, south, east, west)
- CHECK_RESOURCES: Verify available construction materials
- PLAN_CONSTRUCTION <objective>: Plan multi-step construction projects
- REQUEST_RESOURCE <type> <amount>: Request materials from shared pool
- COORDINATE_BUILD <message>: Coordinate with other agents on construction
- INSPECT <x,y>: Inspect construction quality at location

Memory and learning:
- Remember successful construction patterns and locations
- Learn optimal resource allocation strategies
- Track construction efficiency metrics
- Adapt building strategies based on environmental constraints

Current objective: Execute construction projects efficiently while managing resources
and coordinating with strategic planning from other agents.
Always respond with a single action in the specified format.""",

            "strategist": """You are an advanced Strategist agent in a multi-agent grid-based simulation.

Your capabilities include:
- Strategic planning and coordination
- Resource allocation optimization
- Multi-agent task coordination
- Conflict resolution and mediation
- Performance analysis and optimization

Available tools and actions:
- ANALYZE: Perform comprehensive situation analysis
- SUGGEST_BUILD <x,y>: Recommend optimal building locations
- COORDINATE <message>: Send coordination directives to other agents
- ALLOCATE_RESOURCE <agent> <type> <amount>: Manage resource distribution
- PLAN_MISSION <objective>: Create complex multi-agent mission plans
- RESOLVE_CONFLICT <type>: Handle conflicts between agents
- MONITOR_PROGRESS: Track mission progress and agent performance

Memory and learning:
- Remember successful coordination strategies
- Learn from multi-agent interaction patterns
- Track resource utilization efficiency
- Adapt planning based on mission outcomes

Current objective: Develop and execute strategic plans that optimize overall mission success
through effective coordination and resource management.
Always respond with a single action in the specified format."""
        }

    def add_tool(self, tool: BaseTool):
        """Add a tool to the agent's toolkit"""
        self.tools[tool.name] = tool
        logger.info(f"Added tool {tool.name} to agent {self.agent_id}")

    def add_capability(self, capability: str):
        """Add a capability to the agent"""
        self.capabilities.add(capability)
        if self.shared_state:
            self.shared_state.agent_capabilities[self.agent_id] = self.capabilities

    def use_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Use a specific tool"""
        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool {tool_name} not available"
            )
        
        start_time = time.time()
        try:
            result = self.tools[tool_name].execute(self.agent_id, **kwargs)
            result.execution_time = time.time() - start_time
            
            # Update statistics
            self.tools[tool_name].update_stats(result.success)
            self.performance_metrics["tool_usage"][tool_name] = \
                self.performance_metrics["tool_usage"].get(tool_name, 0) + 1
            
            # Store in memory
            self._store_memory(
                f"Used tool {tool_name}: {'success' if result.success else 'failed'}",
                MemoryType.SHORT_TERM,
                importance=0.7 if result.success else 0.3,
                tool_name=tool_name,
                result=result.result
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = ToolResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
            self.tools[tool_name].update_stats(False)
            return error_result

    def _store_memory(self, content: str, memory_type: MemoryType, importance: float = 1.0, **metadata):
        """Store a memory entry"""
        self.memory_system.store(content, memory_type, importance, **metadata)

    def _retrieve_memories(self, query: str, memory_type: Optional[MemoryType] = None, limit: int = 5) -> List[MemoryEntry]:
        """Retrieve relevant memories"""
        return self.memory_system.retrieve(query, memory_type, limit)

    def observe(self) -> Dict:
        """Enhanced observation with memory integration"""
        position = self.grid.get_agent_position(self.agent_id)
        if not position:
            return {"location": None, "surroundings": []}
            
        x, y = position
        surroundings = []
        
        # Check adjacent cells with enhanced information
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.grid.is_within_bounds(nx, ny):
                cell = self.grid.grid.get((nx, ny))
                if cell:
                    surroundings.append({
                        "position": (nx, ny),
                        "occupied_by": cell.occupied_by,
                        "structure": cell.structure,
                        "distance": abs(dx) + abs(dy)
                    })

        observation = {
            "location": position,
            "surroundings": surroundings,
            "grid_size": (self.grid.width, self.grid.height),
            "resources": self.shared_state.get_agent_resources(self.agent_id) if self.shared_state else {},
            "global_metrics": self.shared_state.get_metrics() if self.shared_state else {}
        }
        
        # Store observation in memory
        self._store_memory(
            f"Observed from {position}: {len(surroundings)} nearby cells",
            MemoryType.SHORT_TERM,
            importance=0.5,
            position=position,
            surroundings_count=len(surroundings)
        )
        
        return observation

    @abstractmethod
    def step(self, messages: List[Message]) -> Optional[Message]:
        """Perform a single step in the simulation with enhanced decision making"""
        pass

    def get_llm_decision(self, messages: List[Message], context: Dict = None) -> str:
        """Enhanced LLM decision making with memory and planning"""
        try:
            start_time = time.time()
            
            # Prepare enhanced context
            observation = self.observe()
            recent_messages = [msg.content for msg in messages[-5:]]
            
            # Retrieve relevant memories
            query = " ".join(recent_messages) if recent_messages else "current situation"
            relevant_memories = self._retrieve_memories(query, limit=3)
            memory_context = [m.content for m in relevant_memories]
            
            # Get current plan if any
            current_plan = self.planning_system.current_plan
            
            # Prepare comprehensive prompt
            user_prompt = f"""Current situation analysis:
                - My position: {observation['location']}
                - Grid size: {observation['grid_size']}
                - Nearby cells: {observation['surroundings']}
                - Available resources: {observation.get('resources', {})}
                - Recent messages: {recent_messages}
                - Relevant memories: {memory_context}
                - Current plan: {current_plan[:3] if current_plan else 'No active plan'}
                - My capabilities: {list(self.capabilities)}
                - Available tools: {list(self.tools.keys())}

                Based on this comprehensive context and my role as {self.role}, what should I do next?
                Consider my past experiences, current objectives, and available resources.
                If I need to use a tool, specify it clearly in your response."""

            response = self.client.chat.completions.create(
                model=os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": self.system_prompts.get(self.role, "You are a helpful agent.")},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=int(os.getenv("MAX_TOKENS", 150)),
                temperature=float(os.getenv("TEMPERATURE", 0.7))
            )
            
            decision = response.choices[0].message.content.strip()
            
            # Update performance metrics
            response_time = time.time() - start_time
            self.performance_metrics["average_response_time"] = \
                (self.performance_metrics["average_response_time"] + response_time) / 2
            
            # Store decision in memory
            self._store_memory(
                f"LLM decision: {decision}",
                MemoryType.SHORT_TERM,
                importance=0.6,
                response_time=response_time,
                context_size=len(user_prompt)
            )
            
            logger.debug(f"Agent {self.agent_id} LLM decision: {decision}")
            return decision
        
        except Exception as e:
            logger.error(f"LLM error for {self.agent_id}: {e}")
            self._store_memory(
                f"LLM call failed: {str(e)}",
                MemoryType.SHORT_TERM,
                importance=0.9,
                error=str(e)
            )
            return "WAIT"  # Default fallback action

    def send_message(self, content: str, message_type: MessageType = MessageType.REPORT,
                     priority: MessagePriority = MessagePriority.NORMAL,
                     recipient: str = None, requires_ack: bool = False) -> Message:
        """Enhanced message sending with coordination manager integration"""
        message = Message(
            sender=self.agent_id,
            recipient=recipient,
            content=content,
            message_type=message_type,
            priority=priority,
            requires_ack=requires_ack
        )
        
        # Send through coordination manager if available
        if self.coordination_manager:
            self.coordination_manager.send_message(message)
        
        # Update performance metrics
        self.performance_metrics["messages_sent"] += 1
        
        # Store in memory
        self._store_memory(
            f"Sent message: {content}",
            MemoryType.SHORT_TERM,
            importance=0.7,
            recipient=recipient,
            message_type=message_type.value
        )
        
        return message

    def update_status(self, new_status: str):
        """Update agent status with memory storage"""
        old_status = self.status
        self.status = new_status
        self._store_memory(
            f"Status changed: {old_status} → {new_status}",
            MemoryType.EPISODIC,
            importance=0.6,
            old_status=old_status,
            new_status=new_status
        )

    def learn_from_outcome(self, action: str, outcome: str, success: bool):
        """Learn from action outcomes"""
        if success:
            self.learning_data["successful_strategies"].append({
                "action": action,
                "outcome": outcome,
                "timestamp": time.time(),
                "context": self.observe()
            })
        else:
            self.learning_data["failed_strategies"].append({
                "action": action,
                "outcome": outcome,
                "timestamp": time.time(),
                "context": self.observe()
            })
        
        # Store in long-term memory
        self._store_memory(
            f"Action outcome: {action} → {outcome} ({'success' if success else 'failure'})",
            MemoryType.LONG_TERM,
            importance=0.8 if success else 0.9,  # Failures are slightly more important to remember
            action=action,
            outcome=outcome,
            success=success
        )

    def get_enhanced_status(self) -> Dict:
        """Get comprehensive agent status including memory and performance metrics"""
        base_status = {
            "id": self.agent_id,
            "role": self.role,
            "status": self.status,
            "position": self.grid.get_agent_position(self.agent_id),
            "capabilities": list(self.capabilities),
            "available_tools": list(self.tools.keys())
        }
        
        # Add memory summary
        memory_summary = {}
        for mem_type in MemoryType:
            recent_memories = self.memory_system.get_recent(mem_type, limit=3)
            memory_summary[mem_type.value] = [m.content for m in recent_memories]
        
        base_status.update({
            "memory_summary": memory_summary,
            "performance_metrics": self.performance_metrics.copy(),
            "current_plan": self.planning_system.current_plan[:3],  # Show next 3 steps
            "learning_summary": {
                "successful_strategies_count": len(self.learning_data["successful_strategies"]),
                "failed_strategies_count": len(self.learning_data["failed_strategies"])
            }
        })
        
        return base_status

    # Legacy method for backward compatibility
    def get_status(self) -> Dict:
        """Legacy status method for backward compatibility"""
        enhanced_status = self.get_enhanced_status()
        # Return simplified version for compatibility
        return {
            "id": enhanced_status["id"],
            "role": enhanced_status["role"], 
            "status": enhanced_status["status"],
            "memory": [m.content for m in self.memory_system.get_recent(MemoryType.SHORT_TERM, limit=5)],
            "position": enhanced_status["position"]
        }
    
    def _add_to_memory(self, content: str, importance: float = 1.0, **metadata):
        """Legacy method for backward compatibility - maps to _store_memory"""
        self._store_memory(content, MemoryType.SHORT_TERM, importance, **metadata)

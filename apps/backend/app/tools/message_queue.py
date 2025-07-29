# apps/backend/app/tools/message_queue.py

from typing import Dict, List, Optional, Set
import heapq
import threading
import time
from collections import defaultdict, deque
from .message import Message, MessageType, MessagePriority, ResourceRequest, TaskDependency
import logging

logger = logging.getLogger(__name__)

class MessageQueue:
    """Thread-safe message queue with priority handling and delivery guarantees"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue = []  # Priority queue: (priority, timestamp, message)
        self._pending_acks = {}  # message_id -> Message
        self._message_history = deque(maxlen=500)  # Keep recent message history
        self._lock = threading.RLock()
        self._counter = 0  # For stable sorting
        
    def enqueue(self, message: Message) -> bool:
        """Add message to queue. Returns False if queue is full."""
        with self._lock:
            if len(self._queue) >= self.max_size:
                logger.warning(f"Message queue full, dropping message: {message.message_id}")
                return False
            
            # Priority queue entry: (priority_value, timestamp, counter, message)
            priority_value = -message.priority.value  # Negative for max-heap behavior
            entry = (priority_value, message.timestamp, self._counter, message)
            heapq.heappush(self._queue, entry)
            self._counter += 1
            
            if message.requires_ack:
                self._pending_acks[message.message_id] = message
                
            self._message_history.append(message)
            logger.debug(f"Enqueued message {message.message_id} from {message.sender}")
            return True
    
    def dequeue(self, agent_id: str) -> Optional[Message]:
        """Get next message for specific agent"""
        with self._lock:
            # Look for messages addressed to this agent or broadcast messages
            temp_queue = []
            result = None
            
            while self._queue:
                entry = heapq.heappop(self._queue)
                _, _, _, message = entry
                
                # Check if message is expired
                if message.is_expired():
                    logger.debug(f"Message {message.message_id} expired, dropping")
                    continue
                
                # Check if this message is for this agent
                if message.recipient == agent_id or message.is_broadcast():
                    result = message
                    break
                else:
                    temp_queue.append(entry)
            
            # Put back messages that weren't for this agent
            for entry in temp_queue:
                heapq.heappush(self._queue, entry)
            
            return result
    
    def acknowledge(self, message_id: str, agent_id: str) -> bool:
        """Acknowledge receipt of a message"""
        with self._lock:
            if message_id in self._pending_acks:
                message = self._pending_acks.pop(message_id)
                logger.debug(f"Message {message_id} acknowledged by {agent_id}")
                return True
            return False
    
    def get_pending_acks(self) -> List[Message]:
        """Get messages awaiting acknowledgment"""
        with self._lock:
            return list(self._pending_acks.values())
    
    def size(self) -> int:
        with self._lock:
            return len(self._queue)
    
    def get_message_history(self, limit: int = 50) -> List[Message]:
        """Get recent message history"""
        with self._lock:
            return list(self._message_history)[-limit:]

class SharedState:
    """Manages shared state beyond the grid"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.resources = defaultdict(int)  # resource_type -> available_amount
        self.resource_allocations = {}  # agent_id -> {resource_type: allocated_amount}
        self.task_dependencies = {}  # task_id -> TaskDependency
        self.agent_capabilities = {}  # agent_id -> Set[capability]
        self.global_objectives = []
        self.metrics = defaultdict(float)
        
    def allocate_resource(self, agent_id: str, resource_type: str, amount: int) -> bool:
        """Allocate resources to an agent"""
        with self._lock:
            if self.resources[resource_type] >= amount:
                self.resources[resource_type] -= amount
                if agent_id not in self.resource_allocations:
                    self.resource_allocations[agent_id] = defaultdict(int)
                self.resource_allocations[agent_id][resource_type] += amount
                logger.info(f"Allocated {amount} {resource_type} to {agent_id}")
                return True
            return False
    
    def release_resource(self, agent_id: str, resource_type: str, amount: int):
        """Release resources back to the shared pool"""
        with self._lock:
            if agent_id in self.resource_allocations:
                allocated = self.resource_allocations[agent_id][resource_type]
                release_amount = min(allocated, amount)
                self.resource_allocations[agent_id][resource_type] -= release_amount
                self.resources[resource_type] += release_amount
                logger.info(f"Released {release_amount} {resource_type} from {agent_id}")
    
    def add_task_dependency(self, task: TaskDependency):
        """Add a task dependency"""
        with self._lock:
            self.task_dependencies[task.task_id] = task
    
    def complete_task(self, task_id: str) -> List[str]:
        """Mark task as complete and return newly available tasks"""
        with self._lock:
            if task_id in self.task_dependencies:
                self.task_dependencies[task_id].status = "completed"
                
                # Find tasks that can now be started
                available_tasks = []
                for tid, task in self.task_dependencies.items():
                    if (task.status == "pending" and 
                        all(self.task_dependencies.get(dep_id, {}).status == "completed" 
                            for dep_id in task.depends_on)):
                        available_tasks.append(tid)
                
                return available_tasks
            return []
    
    def get_agent_resources(self, agent_id: str) -> Dict[str, int]:
        """Get resources allocated to an agent"""
        with self._lock:
            return dict(self.resource_allocations.get(agent_id, {}))
    
    def update_metric(self, metric_name: str, value: float):
        """Update a global metric"""
        with self._lock:
            self.metrics[metric_name] = value
    
    def get_metrics(self) -> Dict[str, float]:
        """Get all current metrics"""
        with self._lock:
            return dict(self.metrics)

class CoordinationManager:
    """Manages agent coordination and conflict resolution"""
    
    def __init__(self, shared_state: SharedState):
        self.shared_state = shared_state
        self.message_queue = MessageQueue()
        self._lock = threading.RLock()
        self.conflict_resolution_strategies = {
            "resource_conflict": self._resolve_resource_conflict,
            "spatial_conflict": self._resolve_spatial_conflict,
            "task_conflict": self._resolve_task_conflict
        }
    
    def send_message(self, message: Message) -> bool:
        """Send a message through the coordination system"""
        return self.message_queue.enqueue(message)
    
    def get_messages_for_agent(self, agent_id: str) -> List[Message]:
        """Get all pending messages for an agent"""
        messages = []
        while True:
            msg = self.message_queue.dequeue(agent_id)
            if msg is None:
                break
            messages.append(msg)
        return messages
    
    def handle_resource_request(self, request: ResourceRequest) -> Message:
        """Handle a resource allocation request"""
        with self._lock:
            success = self.shared_state.allocate_resource(
                request.requester, 
                request.resource_type, 
                request.amount
            )
            
            if success:
                return Message(
                    sender="coordination_manager",
                    recipient=request.requester,
                    content=f"Resource allocated: {request.amount} {request.resource_type}",
                    message_type=MessageType.RESOURCE_ALLOCATION,
                    metadata={"resource_type": request.resource_type, "amount": request.amount}
                )
            else:
                return Message(
                    sender="coordination_manager",
                    recipient=request.requester,
                    content=f"Resource allocation failed: insufficient {request.resource_type}",
                    message_type=MessageType.ERROR,
                    metadata={"resource_type": request.resource_type, "requested": request.amount}
                )
    
    def detect_conflicts(self) -> List[Dict]:
        """Detect potential conflicts between agents"""
        conflicts = []
        # This is a simplified conflict detection - can be enhanced
        
        # Resource conflicts
        pending_requests = [msg for msg in self.message_queue.get_message_history() 
                          if msg.message_type == MessageType.RESOURCE_REQUEST]
        resource_demands = defaultdict(int)
        
        for req_msg in pending_requests:
            if "resource_type" in req_msg.metadata:
                resource_demands[req_msg.metadata["resource_type"]] += req_msg.metadata.get("amount", 0)
        
        for resource_type, demand in resource_demands.items():
            available = self.shared_state.resources[resource_type]
            if demand > available:
                conflicts.append({
                    "type": "resource_conflict",
                    "resource": resource_type,
                    "demand": demand,
                    "available": available
                })
        
        return conflicts
    
    def _resolve_resource_conflict(self, conflict: Dict) -> List[Message]:
        """Resolve resource allocation conflicts"""
        # Simple priority-based resolution
        messages = []
        # Implementation would go here
        return messages
    
    def _resolve_spatial_conflict(self, conflict: Dict) -> List[Message]:
        """Resolve spatial conflicts between agents"""
        messages = []
        # Implementation would go here
        return messages
    
    def _resolve_task_conflict(self, conflict: Dict) -> List[Message]:
        """Resolve task assignment conflicts"""
        messages = []
        # Implementation would go here
        return messages
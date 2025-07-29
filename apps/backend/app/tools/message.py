from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid
import time

class MessageType(Enum):
    COMMAND = "command"
    QUERY = "query"
    REPORT = "report"
    ACKNOWLEDGMENT = "ack"
    ERROR = "error"
    COORDINATION = "coordination"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_ALLOCATION = "resource_allocation"

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Message:
    sender: str
    content: str
    message_type: MessageType = MessageType.REPORT
    priority: MessagePriority = MessagePriority.NORMAL
    recipient: Optional[str] = None  # If None, message is broadcast
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    requires_ack: bool = False
    parent_message_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    ttl: Optional[float] = None  # Time to live in seconds
    retry_count: int = 0
    max_retries: int = 3

    def is_broadcast(self) -> bool:
        return self.recipient is None

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def should_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def increment_retry(self):
        self.retry_count += 1

    def create_ack(self, sender: str) -> 'Message':
        return Message(
            sender=sender,
            recipient=self.sender,
            content=f"ACK: {self.message_id}",
            message_type=MessageType.ACKNOWLEDGMENT,
            parent_message_id=self.message_id,
            metadata={"original_message_id": self.message_id}
        )

    def create_error_response(self, sender: str, error_msg: str) -> 'Message':
        return Message(
            sender=sender,
            recipient=self.sender,
            content=f"ERROR: {error_msg}",
            message_type=MessageType.ERROR,
            parent_message_id=self.message_id,
            metadata={"original_message_id": self.message_id, "error": error_msg}
        )

    def __repr__(self):
        target = "All" if self.is_broadcast() else self.recipient
        return f"[{self.message_type.value.upper()}] {self.sender} → {target}: {self.content[:50]}..."

@dataclass
class ResourceRequest:
    resource_type: str
    amount: int
    requester: str
    location: Optional[tuple] = None
    urgency: MessagePriority = MessagePriority.NORMAL
    justification: str = ""

@dataclass 
class TaskDependency:
    task_id: str
    depends_on: List[str]
    assigned_agent: str
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: float = field(default_factory=time.time)
    estimated_duration: Optional[float] = None
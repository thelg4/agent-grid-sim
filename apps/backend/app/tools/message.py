from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    sender: str
    recipient: Optional[str] = None  # If None, message is broadcast
    content: str = ""

    def is_broadcast(self) -> bool:
        return self.recipient is None

    def __repr__(self):
        target = "All" if self.is_broadcast() else self.recipient
        return f"[{self.sender} → {target}] {self.content}"

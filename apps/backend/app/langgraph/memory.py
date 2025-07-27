from collections import defaultdict
from app.tools.message import Message

class Memory:
    def __init__(self):
        self.logs = defaultdict(list)  # agent_id -> List[Message]

    def append(self, agent_id: str, message: Message):
        self.logs[agent_id].append(message)

    def get(self, agent_id: str) -> list[Message]:
        return self.logs[agent_id][-5:]  # last 5 messages only, for brevity

    def get_all(self) -> dict[str, list[Message]]:
        return self.logs

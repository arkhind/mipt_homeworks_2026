from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str


class MessageHistory:
    def __init__(
        self,
        limit_message: int | None = None,
        limit_chars: int | None = None,
    ) -> None:
        self._messages: list[Message] = []
        self.limit_message = limit_message
        self.limit_chars = limit_chars

    def add(self, message: Message) -> None:
        self._messages.append(message)
        self._trim()

    def _trim(self) -> None:
        if self.limit_message is not None:
            while len(self._messages) > self.limit_message:
                self._messages.pop(0)

        if self.limit_chars is not None:
            while len(self._messages) > 1:
                total = sum(len(m.content) for m in self._messages)
                if total <= self.limit_chars:
                    break
                self._messages.pop(0)

            if self._messages:
                total = sum(len(m.content) for m in self._messages)
                if total > self.limit_chars:
                    excess = total - self.limit_chars
                    self._messages[0].content = self._messages[0].content[excess:]

    def clear(self) -> None:
        self._messages.clear()

    def to_list(self) -> list[dict[str, str]]:
        return [{'role': m.role, 'content': m.content} for m in self._messages]

    def __len__(self) -> int:
        return len(self._messages)

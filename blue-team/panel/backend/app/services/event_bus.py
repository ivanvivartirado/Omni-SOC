import asyncio
import contextlib
from typing import Any


class EventBus:
    """Pub/sub en memoria para enviar eventos en vivo a los WebSockets."""

    def __init__(self, maxsize: int = 500) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._maxsize = maxsize

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self._maxsize)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(q)

    def publish(self, message: dict[str, Any]) -> None:
        for q in list(self._subscribers):
            with contextlib.suppress(asyncio.QueueFull):
                q.put_nowait(message)

    @property
    def subscribers(self) -> int:
        return len(self._subscribers)


bus = EventBus()

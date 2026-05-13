"""
ORION EventBus — Async pub/sub for loose-coupled module communication.

Modules subscribe to event names (e.g. ``soulprint.decision_analyzed``).
Publishing is fire-and-forget by default, with optional ``await`` semantics
when a module needs to wait for downstream processing.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger("orion.spine.event_bus")

Subscriber = Callable[["Event"], Coroutine[Any, Any, None]]


@dataclass
class Event:
    """A single event on the bus."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class EventBus:
    """In-memory async event bus (replaceable with Redis/MQTT backend)."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = {}
        self._history: list[Event] = []
        self._max_history = 1000

    def subscribe(self, event_name: str, handler: Subscriber) -> None:
        """Register *handler* for events matching *event_name*."""
        self._subscribers.setdefault(event_name, []).append(handler)
        logger.debug("Subscribed %s to '%s'", handler.__qualname__, event_name)

    def unsubscribe(self, event_name: str, handler: Subscriber) -> None:
        handlers = self._subscribers.get(event_name, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish *event* to all matching subscribers concurrently."""
        logger.info("Event published: %s (from %s)", event.name, event.source)
        self._record(event)

        handlers = self._subscribers.get(event.name, [])
        wildcard_handlers = self._subscribers.get("*", [])
        all_handlers = handlers + wildcard_handlers

        if not all_handlers:
            logger.debug("No subscribers for '%s'", event.name)
            return

        tasks = [asyncio.create_task(h(event)) for h in all_handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Handler %s failed on '%s': %s",
                    all_handlers[i].__qualname__,
                    event.name,
                    result,
                )

    def _record(self, event: Event) -> None:
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

    @property
    def history(self) -> list[Event]:
        return list(self._history)

    @property
    def subscriber_count(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._subscribers.items()}

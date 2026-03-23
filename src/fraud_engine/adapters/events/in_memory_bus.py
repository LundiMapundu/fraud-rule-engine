from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


class InMemoryEventBus:
    """Simple in-memory event bus for testing."""

    def __init__(self) -> None:
        self.published_events: list[tuple[str, dict[str, Any]]] = []

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        self.published_events.append((event_type, payload))
        logger.debug("in_memory_event_published", event_type=event_type)

    async def start_consuming(self) -> None:
        pass

    async def stop_consuming(self) -> None:
        pass

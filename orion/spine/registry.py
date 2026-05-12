"""
ORION ModuleRegistry — Module discovery, registration, and lifecycle.

Every ORION module implements ``BaseModule`` and registers itself here.
The registry validates contracts, manages startup/shutdown ordering, and
provides introspection for the Eternal Architect.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from orion.spine.event_bus import Event, EventBus

logger = logging.getLogger("orion.spine.registry")


@dataclass
class ModuleRecord:
    """Metadata about a registered module."""

    name: str
    version: str
    description: str
    event_subscriptions: list[str] = field(default_factory=list)
    event_publications: list[str] = field(default_factory=list)
    mcp_tools: list[str] = field(default_factory=list)
    api_routes: list[str] = field(default_factory=list)
    revenue_surfaces: list[str] = field(default_factory=list)
    status: str = "registered"  # registered | active | error | stopped
    instance: Any = None


class ModuleRegistry:
    """Central registry for all ORION modules."""

    def __init__(self, event_bus: EventBus) -> None:
        self._modules: dict[str, ModuleRecord] = {}
        self._event_bus = event_bus

    def register(self, record: ModuleRecord) -> None:
        """Register (or re-register) a module."""
        if record.name in self._modules:
            logger.warning("Re-registering module '%s'", record.name)
        self._modules[record.name] = record
        logger.info(
            "Module registered: %s v%s (%s)",
            record.name,
            record.version,
            record.description,
        )

    def unregister(self, name: str) -> None:
        if name in self._modules:
            del self._modules[name]
            logger.info("Module unregistered: %s", name)

    def get(self, name: str) -> ModuleRecord | None:
        return self._modules.get(name)

    @property
    def modules(self) -> dict[str, ModuleRecord]:
        return dict(self._modules)

    async def activate(self, name: str) -> None:
        """Activate a module: run its startup hook and publish event."""
        record = self._modules.get(name)
        if record is None:
            raise KeyError(f"Module '{name}' not found in registry")

        instance = record.instance
        if instance is not None and hasattr(instance, "startup"):
            await instance.startup()

        record.status = "active"
        await self._event_bus.publish(
            Event(
                name="orion.module.activated",
                source="registry",
                payload={"module": name, "version": record.version},
            )
        )
        logger.info("Module activated: %s", name)

    async def deactivate(self, name: str) -> None:
        record = self._modules.get(name)
        if record is None:
            return

        instance = record.instance
        if instance is not None and hasattr(instance, "shutdown"):
            await instance.shutdown()

        record.status = "stopped"
        await self._event_bus.publish(
            Event(
                name="orion.module.deactivated",
                source="registry",
                payload={"module": name},
            )
        )
        logger.info("Module deactivated: %s", name)

    def validate_contract(self, name: str) -> list[str]:
        """Return a list of contract-validation warnings (empty = valid)."""
        record = self._modules.get(name)
        if record is None:
            return [f"Module '{name}' not registered"]

        warnings: list[str] = []
        if not record.version:
            warnings.append("Missing version")
        if not record.description:
            warnings.append("Missing description")
        if not record.event_subscriptions and not record.event_publications:
            warnings.append("Module does not subscribe to or publish any events")
        return warnings

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "name": r.name,
                "version": r.version,
                "status": r.status,
                "events_in": r.event_subscriptions,
                "events_out": r.event_publications,
                "mcp_tools": r.mcp_tools,
                "revenue_surfaces": r.revenue_surfaces,
            }
            for r in self._modules.values()
        ]

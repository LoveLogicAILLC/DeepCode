"""
ORION BaseModule — Abstract contract that every module must implement.

A module is a self-contained organ of the ORION platform.  It:
  - Declares the events it subscribes to and publishes.
  - Exposes MCP tool names.
  - Declares its revenue surfaces.
  - Provides startup / shutdown lifecycle hooks.
  - Optionally serves FastAPI sub-routes.
"""

from __future__ import annotations

import logging
from abc import ABC
from pathlib import Path
from typing import Any

from orion.spine.event_bus import Event, EventBus
from orion.spine.registry import ModuleRecord, ModuleRegistry

logger = logging.getLogger("orion.modules.base")


class BaseModule(ABC):
    """Abstract base that every ORION module must subclass."""

    # --- Identity (override in subclass) ------------------------------------
    NAME: str = ""
    VERSION: str = "0.1.0"
    DESCRIPTION: str = ""

    # --- Contract declarations (override in subclass) -----------------------
    EVENT_SUBSCRIPTIONS: list[str] = []
    EVENT_PUBLICATIONS: list[str] = []
    MCP_TOOLS: list[str] = []
    API_ROUTES: list[str] = []
    REVENUE_SURFACES: list[str] = []

    def __init__(self, event_bus: EventBus, registry: ModuleRegistry) -> None:
        self._event_bus = event_bus
        self._registry = registry

    # --- Registration -------------------------------------------------------

    def register(self) -> None:
        """Self-register with the module registry."""
        record = ModuleRecord(
            name=self.NAME,
            version=self.VERSION,
            description=self.DESCRIPTION,
            event_subscriptions=list(self.EVENT_SUBSCRIPTIONS),
            event_publications=list(self.EVENT_PUBLICATIONS),
            mcp_tools=list(self.MCP_TOOLS),
            api_routes=list(self.API_ROUTES),
            revenue_surfaces=list(self.REVENUE_SURFACES),
            instance=self,
        )
        self._registry.register(record)
        self._bind_event_handlers()

    def _bind_event_handlers(self) -> None:
        """Subscribe to declared events by looking for ``on_<event_suffix>`` methods."""
        for event_name in self.EVENT_SUBSCRIPTIONS:
            suffix = event_name.rsplit(".", 1)[-1]
            handler_name = f"on_{suffix}"
            handler = getattr(self, handler_name, None)
            if handler and callable(handler):
                self._event_bus.subscribe(event_name, handler)
                logger.debug("[%s] Bound %s -> %s", self.NAME, event_name, handler_name)
            else:
                logger.warning(
                    "[%s] No handler '%s' for event '%s'",
                    self.NAME,
                    handler_name,
                    event_name,
                )

    # --- Lifecycle ----------------------------------------------------------

    async def startup(self) -> None:
        """Called when the module is activated. Override for custom init."""

    async def shutdown(self) -> None:
        """Called when the module is deactivated. Override for custom cleanup."""

    # --- MCP ----------------------------------------------------------------

    async def handle_mcp(
        self, method: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Dispatch an MCP tool call to the appropriate method."""
        fn = getattr(self, f"mcp_{method}", None)
        if fn is None:
            raise ValueError(f"[{self.NAME}] Unknown MCP method: {method}")
        return await fn(arguments)

    # --- Helpers ------------------------------------------------------------

    async def emit(
        self, event_name: str, payload: dict[str, Any] | None = None
    ) -> None:
        """Convenience wrapper to publish an event from this module."""
        await self._event_bus.publish(
            Event(name=event_name, payload=payload or {}, source=self.NAME)
        )

    def contract_path(self) -> Path:
        """Return the expected CONTRACT.md path for this module."""
        return Path(__file__).parent / self.NAME / "CONTRACT.md"

    def validate_contract_file(self) -> list[str]:
        """Check that CONTRACT.md exists and has required sections."""
        warnings: list[str] = []
        path = self.contract_path()
        if not path.exists():
            warnings.append(f"CONTRACT.md missing at {path}")
            return warnings

        content = path.read_text(encoding="utf-8")
        required_sections = ["## Events", "## MCP Tools", "## Revenue Surfaces"]
        for section in required_sections:
            if section not in content:
                warnings.append(f"CONTRACT.md missing section: {section}")
        return warnings

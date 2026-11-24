"""
ORION Platform — Bootstrap and lifecycle orchestration.

Wires together the spine, loads modules, and provides a single entry point
for starting the entire platform (API gateway + event bus + modules).
"""

from __future__ import annotations

import logging
from typing import Any

from orion.spine.config import OrionConfig
from orion.spine.event_bus import Event, EventBus
from orion.spine.mcp_server import MCPServer
from orion.spine.provider_manager import ProviderManager
from orion.spine.registry import ModuleRegistry

logger = logging.getLogger("orion.platform")


class OrionPlatform:
    """Top-level object that owns all spine components and modules."""

    def __init__(self, config: OrionConfig | None = None) -> None:
        self.config = config or OrionConfig.from_yaml()
        self.event_bus = EventBus()
        self.registry = ModuleRegistry(self.event_bus)
        self.provider_manager = ProviderManager(config=self.config)
        self.mcp = MCPServer(self.registry, self.event_bus, self.provider_manager)

    async def boot(self) -> None:
        """Bootstrap the platform: load and activate all configured modules."""
        logger.info("ORION platform booting ...")

        # Health-check providers (non-blocking — we don't require external LLMs)
        try:
            health = await self.provider_manager.health_check_all()
            logger.info("Provider health: %s", health)
        except Exception as exc:
            logger.warning("Provider health-check failed (continuing): %s", exc)

        # Load core modules
        self._load_core_modules()

        # Activate all registered modules
        for name in list(self.registry.modules):
            try:
                await self.registry.activate(name)
            except Exception as exc:
                logger.error("Failed to activate module '%s': %s", name, exc)

        await self.event_bus.publish(
            Event(
                name="orion.platform.booted", source="platform", payload=self.status()
            )
        )
        logger.info(
            "ORION platform booted — %d modules active", len(self.registry.modules)
        )

    def _load_core_modules(self) -> None:
        """Instantiate and register the core organ modules."""
        from orion.modules.architect import ArchitectModule
        from orion.modules.echomerce import EchomerceModule
        from orion.modules.griefdao import GriefDAOModule
        from orion.modules.soulprint import SoulprintModule

        modules_map: dict[str, type] = {
            "griefdao": GriefDAOModule,
            "echomerce": EchomerceModule,
            "soulprint": SoulprintModule,
        }

        for mod_name in self.config.auto_load_modules:
            cls = modules_map.get(mod_name)
            if cls is None:
                logger.warning(
                    "Unknown module '%s' in auto_load_modules — skipping", mod_name
                )
                continue
            instance = cls(self.event_bus, self.registry)
            instance.register()

        # Architect is always loaded
        architect = ArchitectModule(
            self.event_bus,
            self.registry,
            provider_manager=self.provider_manager,
        )
        architect.register()

    async def shutdown(self) -> None:
        """Gracefully deactivate all modules."""
        for name in list(self.registry.modules):
            await self.registry.deactivate(name)
        logger.info("ORION platform shut down")

    def status(self) -> dict[str, Any]:
        return {
            "modules": self.registry.summary(),
            "providers": self.provider_manager.summary(),
            "events": self.event_bus.subscriber_count,
            "event_history_size": len(self.event_bus.history),
        }

    # --- Convenience wrappers -----------------------------------------------

    async def run_architect_cycle(
        self, vision_seed: str | None = None
    ) -> dict[str, Any]:
        """Run one Eternal Architect self-improvement cycle."""
        record = self.registry.get("architect")
        if record is None or record.instance is None:
            raise RuntimeError("Architect module not loaded")
        result = await record.instance.run_cycle(vision_seed=vision_seed)
        return {
            "cycle_id": result.cycle_id,
            "status": result.status,
            "phase": result.phase,
            "discovery": result.discovery,
            "spec": result.spec,
            "implementation": result.implementation,
            "monetization": result.monetization,
        }

    def create_fastapi_app(self):
        """Create the FastAPI application (import deferred to avoid hard dep)."""
        from orion.spine.api_gateway import create_app

        return create_app(
            self.config, self.registry, self.event_bus, self.provider_manager
        )

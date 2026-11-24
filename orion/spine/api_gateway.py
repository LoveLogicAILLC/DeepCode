"""
ORION API Gateway — FastAPI-based REST surface for the platform.

Exposes platform health, module introspection, event history, and per-module
OpenAPI routes.  Modules register their own routers at activation time.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from orion.spine.config import OrionConfig
from orion.spine.event_bus import EventBus
from orion.spine.provider_manager import ProviderManager
from orion.spine.registry import ModuleRegistry

logger = logging.getLogger("orion.spine.api_gateway")


def create_app(
    config: OrionConfig,
    registry: ModuleRegistry,
    event_bus: EventBus,
    provider_manager: ProviderManager,
) -> FastAPI:
    """Build and return the FastAPI application."""

    app = FastAPI(
        title="ORION Eternal Architect",
        version="1.0.0",
        description="Self-architecting AI-native platform — REST surface",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Platform-level endpoints -------------------------------------------

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": "1.0.0",
            "providers": provider_manager.summary(),
            "modules": registry.summary(),
        }

    @app.get("/modules")
    async def list_modules() -> list[dict[str, Any]]:
        return registry.summary()

    @app.get("/modules/{name}")
    async def get_module(name: str) -> dict[str, Any]:
        record = registry.get(name)
        if record is None:
            raise HTTPException(404, detail=f"Module '{name}' not found")
        return {
            "name": record.name,
            "version": record.version,
            "description": record.description,
            "status": record.status,
            "events_in": record.event_subscriptions,
            "events_out": record.event_publications,
            "mcp_tools": record.mcp_tools,
            "api_routes": record.api_routes,
            "revenue_surfaces": record.revenue_surfaces,
        }

    @app.post("/modules/{name}/activate")
    async def activate_module(name: str) -> dict[str, str]:
        try:
            await registry.activate(name)
        except KeyError as exc:
            raise HTTPException(404, detail=str(exc))
        return {"status": "activated", "module": name}

    @app.post("/modules/{name}/deactivate")
    async def deactivate_module(name: str) -> dict[str, str]:
        await registry.deactivate(name)
        return {"status": "deactivated", "module": name}

    @app.get("/events/history")
    async def event_history(limit: int = 50) -> list[dict[str, Any]]:
        return [e.to_dict() for e in event_bus.history[-limit:]]

    @app.get("/events/subscribers")
    async def event_subscribers() -> dict[str, int]:
        return event_bus.subscriber_count

    @app.get("/providers")
    async def list_providers() -> list[dict[str, Any]]:
        return provider_manager.summary()

    @app.post("/providers/health")
    async def check_providers() -> dict[str, bool]:
        return await provider_manager.health_check_all()

    @app.get("/config")
    async def get_config() -> dict[str, Any]:
        return config.to_dict()

    return app

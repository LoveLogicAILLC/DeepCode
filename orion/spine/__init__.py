"""
ORION Spine — Core nervous system of the platform.

Components:
    - Config: Centralised configuration management
    - ProviderManager: LLM provider chain with health checks
    - Registry: Module discovery and lifecycle management
    - EventBus: Async pub/sub for loose-coupled communication
    - APIGateway: FastAPI-based gateway for REST endpoints
    - MCPServer: Model Context Protocol tool surface
"""

from orion.spine.config import OrionConfig
from orion.spine.provider_manager import ProviderManager
from orion.spine.registry import ModuleRegistry
from orion.spine.event_bus import EventBus

__all__ = [
    "OrionConfig",
    "ProviderManager",
    "ModuleRegistry",
    "EventBus",
]

"""
ORION MCP Server — Model Context Protocol tool surface.

Exposes every registered module's capabilities as MCP-discoverable tools
so that external agents (and ORION's own Eternal Architect) can call them
via stdio or streamable HTTP.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from orion.spine.event_bus import Event, EventBus
from orion.spine.provider_manager import ProviderManager
from orion.spine.registry import ModuleRegistry

logger = logging.getLogger("orion.spine.mcp_server")


class MCPServer:
    """Lightweight MCP tool server backed by the module registry."""

    def __init__(
        self,
        registry: ModuleRegistry,
        event_bus: EventBus,
        provider_manager: ProviderManager,
    ) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._provider_manager = provider_manager

    def list_tools(self) -> list[dict[str, Any]]:
        """Return a catalogue of all available MCP tools."""
        tools: list[dict[str, Any]] = []

        # Platform-level tools
        tools.append(
            {
                "name": "orion.health",
                "description": "Return platform health and module status",
                "parameters": {},
            }
        )
        tools.append(
            {
                "name": "orion.list_modules",
                "description": "List all registered modules and their status",
                "parameters": {},
            }
        )
        tools.append(
            {
                "name": "orion.publish_event",
                "description": "Publish an event on the ORION event bus",
                "parameters": {
                    "event_name": {"type": "string", "required": True},
                    "payload": {"type": "object", "required": False},
                    "source": {"type": "string", "required": False},
                },
            }
        )
        tools.append(
            {
                "name": "orion.generate",
                "description": "Send a prompt to the LLM provider chain",
                "parameters": {
                    "prompt": {"type": "string", "required": True},
                    "model": {"type": "string", "required": False},
                    "temperature": {"type": "number", "required": False},
                },
            }
        )

        # Module-level tools
        for record in self._registry.modules.values():
            for tool_name in record.mcp_tools:
                tools.append(
                    {
                        "name": f"{record.name}.{tool_name}",
                        "description": f"[{record.name}] {tool_name}",
                        "parameters": {},
                    }
                )

        return tools

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Dispatch a tool call and return the result."""
        arguments = arguments or {}

        if tool_name == "orion.health":
            return {
                "providers": self._provider_manager.summary(),
                "modules": self._registry.summary(),
            }

        if tool_name == "orion.list_modules":
            return {"modules": self._registry.summary()}

        if tool_name == "orion.publish_event":
            event = Event(
                name=arguments["event_name"],
                payload=arguments.get("payload", {}),
                source=arguments.get("source", "mcp"),
            )
            await self._event_bus.publish(event)
            return {"status": "published", "event_id": event.event_id}

        if tool_name == "orion.generate":
            text = await self._provider_manager.generate(
                prompt=arguments["prompt"],
                model_override=arguments.get("model"),
                temperature=arguments.get("temperature", 0.7),
            )
            return {"response": text}

        # Delegate to module instance
        parts = tool_name.split(".", 1)
        if len(parts) == 2:
            module_name, method = parts
            record = self._registry.get(module_name)
            if record and record.instance and hasattr(record.instance, "handle_mcp"):
                return await record.instance.handle_mcp(method, arguments)

        raise ValueError(f"Unknown MCP tool: {tool_name}")

    def tools_json(self) -> str:
        """Serialise the tool catalogue to JSON (for stdio transport)."""
        return json.dumps({"tools": self.list_tools()}, indent=2)

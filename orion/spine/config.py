"""
ORION Config — Centralised configuration management.

Loads platform configuration from YAML files, environment variables, and
sensible defaults.  Every spine component and module reads from a single
``OrionConfig`` instance so the platform stays coherent.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG_PATH = Path("orion.yaml")


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""

    name: str
    base_url: str = "http://localhost:11434"
    model: str = "hermes3:70b"
    timeout: int = 120
    enabled: bool = True
    priority: int = 0  # lower = higher priority


@dataclass
class OrionConfig:
    """Root configuration object for the ORION platform."""

    project_root: Path = field(default_factory=lambda: Path.cwd())
    data_dir: Path = field(default_factory=lambda: Path.cwd() / ".orion")
    log_level: str = "INFO"

    # Provider chain (ordered by priority)
    providers: list[ProviderConfig] = field(default_factory=list)

    # Event bus
    event_bus_backend: str = "memory"  # memory | redis | mqtt

    # API gateway
    api_host: str = "0.0.0.0"
    api_port: int = 8420

    # MCP
    mcp_transport: str = "stdio"  # stdio | http

    # Modules to auto-load on boot
    auto_load_modules: list[str] = field(
        default_factory=lambda: ["griefdao", "echomerce", "soulprint"]
    )

    # Treasury / revenue
    treasury_wallet: str = ""

    # Arbitrary extra keys from the YAML
    extra: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: Path | str | None = None) -> OrionConfig:
        """Load configuration from a YAML file with env-var overrides."""
        path = Path(path) if path else _DEFAULT_CONFIG_PATH
        raw: dict[str, Any] = {}
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}

        providers_raw = raw.pop("providers", [])
        providers = [ProviderConfig(**p) for p in providers_raw]
        if not providers:
            providers = _default_providers()

        known_keys = {f.name for f in cls.__dataclass_fields__.values()}
        known = {k: v for k, v in raw.items() if k in known_keys}
        extra = {k: v for k, v in raw.items() if k not in known_keys}

        cfg = cls(providers=providers, extra=extra, **known)
        cfg._apply_env_overrides()
        cfg.data_dir.mkdir(parents=True, exist_ok=True)
        return cfg

    def _apply_env_overrides(self) -> None:
        if val := os.getenv("ORION_LOG_LEVEL"):
            self.log_level = val
        if val := os.getenv("ORION_API_PORT"):
            self.api_port = int(val)
        if val := os.getenv("ORION_EVENT_BUS"):
            self.event_bus_backend = val
        if val := os.getenv("ORION_MCP_TRANSPORT"):
            self.mcp_transport = val

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "log_level": self.log_level,
            "providers": [
                {
                    "name": p.name,
                    "base_url": p.base_url,
                    "model": p.model,
                    "priority": p.priority,
                    "enabled": p.enabled,
                }
                for p in self.providers
            ],
            "event_bus_backend": self.event_bus_backend,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "mcp_transport": self.mcp_transport,
            "auto_load_modules": self.auto_load_modules,
        }


def _default_providers() -> list[ProviderConfig]:
    """Sensible default provider chain: Ollama local first."""
    return [
        ProviderConfig(
            name="ollama-local",
            base_url="http://localhost:11434",
            model="hermes3:70b",
            priority=0,
        ),
        ProviderConfig(
            name="ollama-qwen",
            base_url="http://localhost:11434",
            model="qwen2.5:32b",
            priority=1,
        ),
    ]

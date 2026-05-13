"""
ORION ProviderManager — LLM provider chain with automatic health-checking.

Maintains an ordered list of providers (Ollama local -> external fallbacks)
and routes generation requests to the first healthy provider.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import aiohttp

from orion.spine.config import OrionConfig, ProviderConfig

logger = logging.getLogger("orion.spine.provider_manager")


@dataclass
class ProviderStatus:
    """Runtime health status for a single provider."""

    config: ProviderConfig
    healthy: bool = True
    last_check: float = 0.0
    consecutive_failures: int = 0


@dataclass
class ProviderManager:
    """Manages the ordered LLM provider chain with health checks."""

    config: OrionConfig
    _providers: list[ProviderStatus] = field(default_factory=list, init=False)
    _health_interval: float = 30.0  # seconds between health probes

    def __post_init__(self) -> None:
        sorted_cfgs = sorted(self.config.providers, key=lambda p: p.priority)
        self._providers = [ProviderStatus(config=p) for p in sorted_cfgs if p.enabled]

    @property
    def providers(self) -> list[ProviderStatus]:
        return list(self._providers)

    async def health_check_all(self) -> dict[str, bool]:
        """Probe every provider and return a name -> healthy mapping."""
        results: dict[str, bool] = {}
        for ps in self._providers:
            healthy = await self._probe(ps)
            ps.healthy = healthy
            ps.last_check = time.time()
            if healthy:
                ps.consecutive_failures = 0
            else:
                ps.consecutive_failures += 1
            results[ps.config.name] = healthy
        return results

    async def generate(
        self,
        prompt: str,
        *,
        model_override: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Send a generation request to the first healthy provider."""
        for ps in self._providers:
            if not ps.healthy and (time.time() - ps.last_check) < self._health_interval:
                continue
            try:
                result = await self._call_provider(
                    ps,
                    prompt,
                    model_override=model_override,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                ps.healthy = True
                ps.consecutive_failures = 0
                return result
            except Exception as exc:
                logger.warning(
                    "Provider %s failed: %s — falling back", ps.config.name, exc
                )
                ps.healthy = False
                ps.consecutive_failures += 1
                continue

        raise RuntimeError("All LLM providers exhausted; no healthy provider available")

    async def _call_provider(
        self,
        ps: ProviderStatus,
        prompt: str,
        *,
        model_override: str | None,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call Ollama-compatible /api/generate endpoint."""
        url = f"{ps.config.base_url}/api/generate"
        payload: dict[str, Any] = {
            "model": model_override or ps.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        timeout = aiohttp.ClientTimeout(total=ps.config.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("response", "")

    async def _probe(self, ps: ProviderStatus) -> bool:
        """Lightweight health probe against the provider's tag endpoint."""
        try:
            url = f"{ps.config.base_url}/api/tags"
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "name": ps.config.name,
                "model": ps.config.model,
                "healthy": ps.healthy,
                "failures": ps.consecutive_failures,
            }
            for ps in self._providers
        ]

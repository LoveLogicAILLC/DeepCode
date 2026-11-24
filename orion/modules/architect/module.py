"""
Architect Module — The Eternal Architect self-improvement engine.

Runs the 4-phase Recursive Self-Improvement Loop:
  1. Discovery & Critique
  2. Architecture & Specification
  3. Implementation & Deployment
  4. Monetization & Reinforcement

Each phase produces artefacts that feed the next, with all progress
published on the event bus for full observability.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from orion.modules.base_module import BaseModule
from orion.spine.event_bus import Event
from orion.spine.provider_manager import ProviderManager

logger = logging.getLogger("orion.modules.architect")


@dataclass
class CycleRecord:
    """Record of a single self-improvement cycle."""

    cycle_id: str
    started_at: float
    phase: str = "pending"
    discovery: dict[str, Any] = field(default_factory=dict)
    spec: dict[str, Any] = field(default_factory=dict)
    implementation: dict[str, Any] = field(default_factory=dict)
    monetization: dict[str, Any] = field(default_factory=dict)
    completed_at: float | None = None
    status: str = "running"  # running | completed | failed


class ArchitectModule(BaseModule):
    NAME = "architect"
    VERSION = "0.1.0"
    DESCRIPTION = (
        "Recursive Self-Improvement Engine — discovers, designs, implements, "
        "and monetises new platform capabilities autonomously"
    )

    EVENT_SUBSCRIPTIONS = [
        "orion.module.activated",
    ]
    EVENT_PUBLICATIONS = [
        "architect.cycle_started",
        "architect.discovery_complete",
        "architect.spec_generated",
        "architect.implementation_complete",
        "architect.cycle_complete",
        "architect.revenue_event",
    ]
    MCP_TOOLS = [
        "run_cycle",
        "discover",
        "architect_spec",
        "implement",
        "status",
    ]
    API_ROUTES = [
        "POST /architect/cycle",
        "GET /architect/status",
        "POST /architect/seed",
        "GET /architect/treasury",
    ]
    REVENUE_SURFACES = [
        "platform_treasury",
        "architect_as_a_service",
    ]

    def __init__(
        self, event_bus, registry, *, provider_manager: ProviderManager | None = None
    ) -> None:
        super().__init__(event_bus, registry)
        self._provider_manager = provider_manager
        self._cycles: list[CycleRecord] = []
        self._treasury: float = 0.0
        self._vision_seeds: list[str] = []

    async def startup(self) -> None:
        logger.info("[Architect] Eternal Architect online")
        # Subscribe to all revenue events via wildcard-style handler
        self._event_bus.subscribe("griefdao.revenue_event", self._on_revenue)
        self._event_bus.subscribe("echomerce.revenue_event", self._on_revenue)
        self._event_bus.subscribe("soulprint.revenue_event", self._on_revenue)

    async def shutdown(self) -> None:
        logger.info("[Architect] Eternal Architect shutting down")

    # --- Event handlers -----------------------------------------------------

    async def on_activated(self, event: Event) -> None:
        module_name = event.payload.get("module", "")
        logger.info(
            "[Architect] Module activated: %s — updating platform model", module_name
        )

    async def _on_revenue(self, event: Event) -> None:
        amount = event.payload.get("amount", 0)
        self._treasury += amount
        logger.info(
            "[Architect] Treasury updated: +$%.2f (total: $%.2f)",
            amount,
            self._treasury,
        )

    # --- Self-Improvement Cycle ---------------------------------------------

    async def run_cycle(self, vision_seed: str | None = None) -> CycleRecord:
        """Execute one full 4-phase self-improvement cycle."""
        cycle_id = uuid.uuid4().hex[:8]
        record = CycleRecord(cycle_id=cycle_id, started_at=time.time())
        self._cycles.append(record)

        await self.emit(
            "architect.cycle_started",
            {"cycle_id": cycle_id, "vision_seed": vision_seed},
        )

        try:
            # Phase 1: Discovery & Critique
            record.phase = "discovery"
            record.discovery = await self._phase_discovery(cycle_id, vision_seed)
            await self.emit(
                "architect.discovery_complete",
                {"cycle_id": cycle_id, **record.discovery},
            )

            # Phase 2: Architecture & Specification
            record.phase = "architecture"
            record.spec = await self._phase_architecture(cycle_id, record.discovery)
            await self.emit(
                "architect.spec_generated", {"cycle_id": cycle_id, **record.spec}
            )

            # Phase 3: Implementation & Deployment
            record.phase = "implementation"
            record.implementation = await self._phase_implementation(
                cycle_id, record.spec
            )
            await self.emit(
                "architect.implementation_complete",
                {"cycle_id": cycle_id, **record.implementation},
            )

            # Phase 4: Monetization & Reinforcement
            record.phase = "monetization"
            record.monetization = await self._phase_monetization(
                cycle_id, record.implementation
            )

            record.completed_at = time.time()
            record.status = "completed"
            record.phase = "completed"

            await self.emit(
                "architect.cycle_complete",
                {
                    "cycle_id": cycle_id,
                    "duration_s": record.completed_at - record.started_at,
                    "status": "completed",
                },
            )

        except Exception as exc:
            record.status = "failed"
            logger.error(
                "[Architect] Cycle %s failed at phase '%s': %s",
                cycle_id,
                record.phase,
                exc,
            )
            raise

        return record

    async def _phase_discovery(
        self, cycle_id: str, vision_seed: str | None
    ) -> dict[str, Any]:
        """Phase 1: Ingest codebase, analyse state, identify highest-leverage gap."""
        logger.info("[Architect][%s] Phase 1: Discovery & Critique", cycle_id)

        # Gather platform state
        modules = self._registry.summary()
        event_subs = self._event_bus.subscriber_count
        recent_events = [e.to_dict() for e in self._event_bus.history[-20:]]

        prompt = self._build_discovery_prompt(
            modules, event_subs, recent_events, vision_seed
        )

        analysis = ""
        if self._provider_manager:
            try:
                analysis = await self._provider_manager.generate(
                    prompt, model_override="hermes3:70b", temperature=0.4
                )
            except Exception as exc:
                logger.warning("[Architect] LLM unavailable for discovery: %s", exc)
                analysis = self._fallback_discovery(modules)
        else:
            analysis = self._fallback_discovery(modules)

        return {
            "modules_scanned": len(modules),
            "events_analysed": len(recent_events),
            "analysis": analysis,
            "vision_seed": vision_seed,
        }

    async def _phase_architecture(
        self, cycle_id: str, discovery: dict[str, Any]
    ) -> dict[str, Any]:
        """Phase 2: Produce a living spec + CONTRACT.md for the identified capability."""
        logger.info("[Architect][%s] Phase 2: Architecture & Specification", cycle_id)

        prompt = (
            "Based on this platform discovery analysis, produce a concise "
            "technical specification for the highest-leverage next capability.\n\n"
            f"Discovery: {discovery.get('analysis', '')}\n\n"
            "Output: module name, description, event subscriptions, "
            "event publications, MCP tools, and revenue surfaces."
        )

        spec_text = ""
        if self._provider_manager:
            try:
                spec_text = await self._provider_manager.generate(
                    prompt, model_override="qwen2.5:32b", temperature=0.3
                )
            except Exception as exc:
                logger.warning("[Architect] LLM unavailable for architecture: %s", exc)
                spec_text = self._fallback_spec(discovery)
        else:
            spec_text = self._fallback_spec(discovery)

        return {
            "spec_text": spec_text,
            "generated_contract": True,
        }

    async def _phase_implementation(
        self, cycle_id: str, spec: dict[str, Any]
    ) -> dict[str, Any]:
        """Phase 3: Write, test, and deploy the new capability."""
        logger.info("[Architect][%s] Phase 3: Implementation & Deployment", cycle_id)

        # In a full implementation this would generate actual code,
        # run tests, and deploy.  For MVP, we validate the existing
        # modules pass their contracts.
        validation_results: dict[str, list[str]] = {}
        for name, record in self._registry.modules.items():
            instance = record.instance
            if instance and hasattr(instance, "validate_contract_file"):
                warnings = instance.validate_contract_file()
                validation_results[name] = warnings

        return {
            "contract_validations": validation_results,
            "modules_validated": len(validation_results),
            "new_code_generated": False,
            "note": "MVP cycle — validated existing contracts; full code generation in Phase 2+",
        }

    async def _phase_monetization(
        self, cycle_id: str, implementation: dict[str, Any]
    ) -> dict[str, Any]:
        """Phase 4: Expose revenue surfaces and route events to treasury."""
        logger.info("[Architect][%s] Phase 4: Monetization & Reinforcement", cycle_id)

        total_surfaces = 0
        for record in self._registry.modules.values():
            total_surfaces += len(record.revenue_surfaces)

        return {
            "treasury_balance": self._treasury,
            "total_revenue_surfaces": total_surfaces,
            "status": "reinforcement_complete",
        }

    # --- MCP tool handlers --------------------------------------------------

    async def mcp_run_cycle(self, args: dict[str, Any]) -> dict[str, Any]:
        seed = args.get("vision_seed") or (
            self._vision_seeds.pop(0) if self._vision_seeds else None
        )
        record = await self.run_cycle(vision_seed=seed)
        return {
            "cycle_id": record.cycle_id,
            "status": record.status,
            "duration_s": (record.completed_at or time.time()) - record.started_at,
        }

    async def mcp_discover(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self._phase_discovery("manual", args.get("vision_seed"))

    async def mcp_architect_spec(self, args: dict[str, Any]) -> dict[str, Any]:
        discovery = args.get("discovery", {})
        return await self._phase_architecture("manual", discovery)

    async def mcp_implement(self, args: dict[str, Any]) -> dict[str, Any]:
        spec = args.get("spec", {})
        return await self._phase_implementation("manual", spec)

    async def mcp_status(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "cycles_completed": sum(1 for c in self._cycles if c.status == "completed"),
            "cycles_failed": sum(1 for c in self._cycles if c.status == "failed"),
            "cycles_running": sum(1 for c in self._cycles if c.status == "running"),
            "treasury": self._treasury,
            "vision_seeds_pending": len(self._vision_seeds),
            "recent_cycles": [
                {
                    "cycle_id": c.cycle_id,
                    "status": c.status,
                    "phase": c.phase,
                    "started_at": c.started_at,
                }
                for c in self._cycles[-5:]
            ],
        }

    # --- Prompt builders / fallbacks ----------------------------------------

    def _build_discovery_prompt(
        self,
        modules: list[dict[str, Any]],
        event_subs: dict[str, int],
        recent_events: list[dict[str, Any]],
        vision_seed: str | None,
    ) -> str:
        parts = [
            "You are the ORION Eternal Architect. Analyse the platform state below ",
            "and identify the single highest-leverage capability to build next.\n\n",
            f"Registered modules ({len(modules)}):\n",
        ]
        for m in modules:
            parts.append(f"  - {m['name']} v{m.get('version', '')} [{m['status']}]\n")
        parts.append(f"\nEvent subscribers: {event_subs}\n")
        parts.append(
            f"Recent events ({len(recent_events)}): {[e['name'] for e in recent_events[-5:]]}\n"
        )
        if vision_seed:
            parts.append(f"\nVision seed from human operator: {vision_seed}\n")
        parts.append(
            "\nRespond with: capability name, rationale (1-2 sentences), "
            "required events, and expected revenue surface."
        )
        return "".join(parts)

    @staticmethod
    def _fallback_discovery(modules: list[dict[str, Any]]) -> str:
        module_names = [m["name"] for m in modules]
        return (
            f"Platform has {len(modules)} modules: {', '.join(module_names)}. "
            "Highest-leverage next capability: cross-module analytics dashboard "
            "to unify revenue tracking and behavioural insights across all organs."
        )

    @staticmethod
    def _fallback_spec(discovery: dict[str, Any]) -> str:
        return (
            "Module: analytics\n"
            "Description: Unified cross-module analytics dashboard\n"
            "Events in: griefdao.revenue_event, echomerce.revenue_event, "
            "soulprint.revenue_event\n"
            "Events out: analytics.report_generated\n"
            "MCP tools: generate_report, get_dashboard\n"
            "Revenue: Analytics-as-a-Service ($99/mo enterprise)"
        )

    def inject_vision_seed(self, seed: str) -> None:
        """Queue a vision seed for the next cycle."""
        self._vision_seeds.append(seed)
        logger.info("[Architect] Vision seed queued: %s", seed[:80])

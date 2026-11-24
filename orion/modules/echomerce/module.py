"""
Echomerce Module — Pre-demand commerce engine.

Detects demand before it materialises, autonomously generates
products/services, and routes revenue back to the platform treasury.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from orion.modules.base_module import BaseModule
from orion.spine.event_bus import Event

logger = logging.getLogger("orion.modules.echomerce")


class EchomerceModule(BaseModule):
    NAME = "echomerce"
    VERSION = "0.1.0"
    DESCRIPTION = (
        "Pre-demand commerce engine — predictive market creation, "
        "demand anticipation, and autonomous product/service generation"
    )

    EVENT_SUBSCRIPTIONS = [
        "soulprint.decision_analyzed",
        "griefdao.estate_updated",
    ]
    EVENT_PUBLICATIONS = [
        "echomerce.demand_detected",
        "echomerce.product_generated",
        "echomerce.order_fulfilled",
        "echomerce.revenue_event",
    ]
    MCP_TOOLS = [
        "detect_demand",
        "generate_product",
        "list_opportunities",
        "fulfill_order",
    ]
    API_ROUTES = [
        "GET /echomerce/opportunities",
        "POST /echomerce/detect",
        "POST /echomerce/products",
        "POST /echomerce/fulfill",
    ]
    REVENUE_SURFACES = [
        "pre_demand_marketplace",
        "demand_intelligence_api",
        "autonomous_product_creation",
    ]

    def __init__(self, event_bus, registry) -> None:
        super().__init__(event_bus, registry)
        self._opportunities: dict[str, dict[str, Any]] = {}

    async def startup(self) -> None:
        logger.info("[Echomerce] Module started")

    async def shutdown(self) -> None:
        logger.info("[Echomerce] Module stopped")

    # --- Event handlers -----------------------------------------------------

    async def on_decision_analyzed(self, event: Event) -> None:
        """Extract commerce signals from Soulprint decision analyses."""
        decision_type = event.payload.get("decision_type", "")
        if decision_type:
            opp = await self._create_opportunity(
                signal_source="soulprint",
                category=decision_type,
                confidence=0.6,
            )
            logger.info("[Echomerce] Demand signal from Soulprint: %s", opp["id"])

    async def on_estate_updated(self, event: Event) -> None:
        """Detect legacy-commerce crossovers from GriefDAO estate changes."""
        estate_id = event.payload.get("estate_id", "")
        if estate_id:
            opp = await self._create_opportunity(
                signal_source="griefdao",
                category="legacy_commerce",
                confidence=0.5,
            )
            logger.info("[Echomerce] Legacy-commerce signal: %s", opp["id"])

    # --- MCP tool handlers --------------------------------------------------

    async def mcp_detect_demand(self, args: dict[str, Any]) -> dict[str, Any]:
        opp = await self._create_opportunity(
            signal_source=args.get("source", "manual"),
            category=args.get("category", "general"),
            confidence=args.get("confidence", 0.5),
        )
        return {"opportunity_id": opp["id"], "status": "detected"}

    async def mcp_generate_product(self, args: dict[str, Any]) -> dict[str, Any]:
        opp_id = args.get("opportunity_id", "")
        opp = self._opportunities.get(opp_id)
        if opp is None:
            return {"error": f"Opportunity '{opp_id}' not found"}

        product_id = uuid.uuid4().hex[:12]
        opp["status"] = "product_generated"
        await self.emit(
            "echomerce.product_generated",
            {"product_id": product_id, "opportunity_id": opp_id},
        )
        await self.emit(
            "echomerce.revenue_event",
            {"surface": "autonomous_product_creation", "amount": 29.99},
        )
        return {"product_id": product_id, "status": "generated"}

    async def mcp_list_opportunities(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"opportunities": list(self._opportunities.values())}

    async def mcp_fulfill_order(self, args: dict[str, Any]) -> dict[str, Any]:
        opp_id = args.get("opportunity_id", "")
        opp = self._opportunities.get(opp_id)
        if opp is None:
            return {"error": f"Opportunity '{opp_id}' not found"}
        opp["status"] = "fulfilled"
        await self.emit(
            "echomerce.order_fulfilled",
            {"opportunity_id": opp_id},
        )
        return {"opportunity_id": opp_id, "status": "fulfilled"}

    # --- Internals ----------------------------------------------------------

    async def _create_opportunity(
        self,
        signal_source: str,
        category: str,
        confidence: float,
    ) -> dict[str, Any]:
        opp_id = uuid.uuid4().hex[:12]
        opp = {
            "id": opp_id,
            "signal_source": signal_source,
            "category": category,
            "confidence": confidence,
            "detected_at": time.time(),
            "status": "detected",
        }
        self._opportunities[opp_id] = opp
        await self.emit(
            "echomerce.demand_detected",
            {"opportunity_id": opp_id, "category": category},
        )
        return opp

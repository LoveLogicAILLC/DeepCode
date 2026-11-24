# Echomerce — CONTRACT.md

> Machine-parseable + human-readable contract for the Echomerce module.

## Module Identity

| Field | Value |
|---|---|
| **Name** | `echomerce` |
| **Version** | `0.1.0` |
| **Description** | Pre-demand commerce engine — predictive market creation, demand anticipation, and autonomous product/service generation |

## Events

### Subscriptions

| Event | Handler | Description |
|---|---|---|
| `soulprint.decision_analyzed` | `on_decision_analyzed` | Extract commerce signals from life-decision analyses |
| `griefdao.estate_updated` | `on_estate_updated` | Detect legacy-commerce crossover opportunities |

### Publications

| Event | Description |
|---|---|
| `echomerce.demand_detected` | Fired when a new pre-demand signal is identified |
| `echomerce.product_generated` | Fired when an autonomous product/service is created |
| `echomerce.order_fulfilled` | Fired when a pre-demand order is fulfilled |
| `echomerce.revenue_event` | Revenue generated from commerce transactions |

## MCP Tools

| Tool | Description |
|---|---|
| `detect_demand` | Analyse signals and identify pre-demand opportunities |
| `generate_product` | Autonomously generate a product/service to meet detected demand |
| `list_opportunities` | List current pre-demand opportunities in the pipeline |
| `fulfill_order` | Execute fulfilment for a pre-demand order |

## API Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/echomerce/opportunities` | List demand opportunities |
| `POST` | `/echomerce/detect` | Trigger demand detection |
| `POST` | `/echomerce/products` | Generate a new product |
| `POST` | `/echomerce/fulfill` | Fulfil a pre-demand order |

## Revenue Surfaces

| Surface | Model | Description |
|---|---|---|
| Pre-demand Marketplace | Transaction fee (15%) | Commission on pre-demand commerce |
| Demand Intelligence API | Usage-based ($0.01/call) | External access to demand signals |
| Autonomous Product Creation | Per-product ($29.99) | AI-generated product/service packaging |

## Data Schema

```json
{
  "opportunity": {
    "id": "string",
    "signal_source": "string",
    "category": "string",
    "confidence": "float",
    "detected_at": "datetime",
    "status": "detected | product_generated | fulfilled"
  }
}
```

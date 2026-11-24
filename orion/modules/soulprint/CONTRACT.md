# Soulprint — CONTRACT.md

> Machine-parseable + human-readable contract for the Soulprint module.

## Module Identity

| Field | Value |
|---|---|
| **Name** | `soulprint` |
| **Version** | `0.1.0` |
| **Description** | Longitudinal life intelligence — decision analysis, behavioural pattern recognition, and predictive life-modelling |

## Events

### Subscriptions

| Event | Handler | Description |
|---|---|---|
| `griefdao.estate_updated` | `on_estate_updated` | Incorporate estate data into life model |
| `echomerce.demand_detected` | `on_demand_detected` | Use demand signals to refine behavioural predictions |

### Publications

| Event | Description |
|---|---|
| `soulprint.decision_analyzed` | Fired when a life-decision is analysed and classified |
| `soulprint.pattern_detected` | Fired when a new behavioural pattern is identified |
| `soulprint.prediction_generated` | Fired when a life-trajectory prediction is created |
| `soulprint.revenue_event` | Revenue generated from intelligence services |

## MCP Tools

| Tool | Description |
|---|---|
| `analyze_decision` | Analyse and classify a life-decision |
| `detect_patterns` | Run pattern detection on a user's decision history |
| `predict_trajectory` | Generate a predictive life-trajectory model |
| `get_profile` | Retrieve a user's Soulprint profile |

## API Routes

| Method | Path | Description |
|---|---|---|
| `POST` | `/soulprint/decisions` | Submit a decision for analysis |
| `GET` | `/soulprint/patterns/{user}` | Get detected patterns for a user |
| `POST` | `/soulprint/predict` | Generate a trajectory prediction |
| `GET` | `/soulprint/profile/{user}` | Get a user's Soulprint profile |

## Revenue Surfaces

| Surface | Model | Description |
|---|---|---|
| Life Intelligence Dashboard | Subscription ($14.99/mo) | Personal decision analytics |
| Trajectory Prediction API | Per-prediction ($4.99) | External access to life modelling |
| Pattern Intelligence | Enterprise license | Bulk behavioural pattern access |

## Data Schema

```json
{
  "decision": {
    "id": "string",
    "user": "string",
    "description": "string",
    "category": "string",
    "impact_score": "float",
    "analyzed_at": "datetime"
  },
  "pattern": {
    "id": "string",
    "user": "string",
    "pattern_type": "string",
    "confidence": "float",
    "decisions": ["string"]
  }
}
```

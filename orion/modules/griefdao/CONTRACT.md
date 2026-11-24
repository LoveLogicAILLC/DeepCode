# GriefDAO — CONTRACT.md

> Machine-parseable + human-readable contract for the GriefDAO module.

## Module Identity

| Field | Value |
|---|---|
| **Name** | `griefdao` |
| **Version** | `0.1.0` |
| **Description** | Perpetual digital legacy management — estate preservation, memorial AI personas, and cross-generational knowledge transfer |

## Events

### Subscriptions

| Event | Handler | Description |
|---|---|---|
| `soulprint.decision_analyzed` | `on_decision_analyzed` | Update estate profile when a new life-decision is analysed |
| `echomerce.demand_detected` | `on_demand_detected` | Evaluate demand signals for legacy-related commerce opportunities |

### Publications

| Event | Description |
|---|---|
| `griefdao.estate_updated` | Fired when an estate record is created or modified |
| `griefdao.memorial_created` | Fired when a new memorial persona is instantiated |
| `griefdao.legacy_transfer` | Fired when cross-generational knowledge transfer occurs |
| `griefdao.revenue_event` | Revenue generated from premium legacy services |

## MCP Tools

| Tool | Description |
|---|---|
| `create_estate` | Create a new digital estate record |
| `get_estate` | Retrieve an existing estate |
| `create_memorial` | Instantiate an AI memorial persona from estate data |
| `transfer_knowledge` | Initiate cross-generational knowledge transfer |

## API Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/griefdao/estates` | List all estates |
| `POST` | `/griefdao/estates` | Create a new estate |
| `GET` | `/griefdao/estates/{id}` | Get estate details |
| `POST` | `/griefdao/memorials` | Create a memorial persona |

## Revenue Surfaces

| Surface | Model | Description |
|---|---|---|
| Premium Legacy Vault | Subscription ($9.99/mo) | Encrypted perpetual estate storage |
| Memorial Persona | Per-creation ($49.99) | AI persona trained on estate data |
| Legacy Transfer | Per-transfer ($19.99) | Cross-generational knowledge packaging |

## Data Schema

```json
{
  "estate": {
    "id": "string",
    "owner": "string",
    "created_at": "datetime",
    "artifacts": ["string"],
    "persona_corpus": "string",
    "status": "active | archived | transferred"
  }
}
```

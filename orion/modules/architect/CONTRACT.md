# Architect — CONTRACT.md

> Machine-parseable + human-readable contract for the Eternal Architect module.

## Module Identity

| Field | Value |
|---|---|
| **Name** | `architect` |
| **Version** | `0.1.0` |
| **Description** | Recursive Self-Improvement Engine — discovers, designs, implements, and monetises new platform capabilities autonomously |

## Events

### Subscriptions

| Event | Handler | Description |
|---|---|---|
| `orion.module.activated` | `on_module_activated` | Track new module activations for self-awareness |
| `*.revenue_event` | `on_revenue_event` | Track all revenue events for treasury management |

### Publications

| Event | Description |
|---|---|
| `architect.cycle_started` | Fired when a new self-improvement cycle begins |
| `architect.discovery_complete` | Fired when the discovery phase finishes |
| `architect.spec_generated` | Fired when a new architecture spec is produced |
| `architect.implementation_complete` | Fired when new code is deployed |
| `architect.cycle_complete` | Fired when a full cycle finishes |
| `architect.revenue_event` | Revenue generated from architect services |

## MCP Tools

| Tool | Description |
|---|---|
| `run_cycle` | Execute one full self-improvement cycle |
| `discover` | Run the discovery & critique phase only |
| `architect_spec` | Run the architecture & specification phase |
| `implement` | Run the implementation & deployment phase |
| `status` | Get current architect state and cycle history |

## API Routes

| Method | Path | Description |
|---|---|---|
| `POST` | `/architect/cycle` | Trigger a full self-improvement cycle |
| `GET` | `/architect/status` | Get architect status and history |
| `POST` | `/architect/seed` | Inject a vision seed into the next cycle |
| `GET` | `/architect/treasury` | Get treasury balance and revenue breakdown |

## Revenue Surfaces

| Surface | Model | Description |
|---|---|---|
| Platform Treasury | Internal routing | All module revenue flows here |
| Architect-as-a-Service | Enterprise license | External orgs can use the self-improvement loop |

## Orchestration

The Architect runs a continuous **4-Phase Cycle**:

```
1. Discovery & Critique  (hermes3:70b)
2. Architecture & Spec    (qwen2.5:32b)
3. Implementation & Deploy (qwen2.5:32b + LangGraph)
4. Monetization & Reinforce
```

Each cycle is event-driven and publishes progress events at every phase boundary.

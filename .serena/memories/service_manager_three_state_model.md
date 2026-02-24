# Service Manager Three-State Model

## Purpose
Guides editing of the Docker container lifecycle manager in `service-manager/`.

## Key Files
- `service-manager/service_manager.py` — main FastAPI app, sleep/wake logic
- `service-manager/tests/test_sleep_wake.py` — unit tests (mock Docker client)
- `service-manager/tests/test_integration_sleep_wake.py` — integration tests (real Docker)
- `config/sleep-policies/default.yaml` — global sleep policy configuration
- `config/services.yml` — service definitions with resource constraints

## Architecture
Three-state FSM for container lifecycle:
```
STOPPED → STARTING → RUNNING → SLEEPING → RUNNING
```
- **Running**: full operation, normal resources
- **Sleeping**: Docker `pause` — ~50-80% memory reduction
- **Stopped**: container not running — zero resources

Docker SDK calls (NEVER confuse these):
- Sleep: `container.pause()`
- Wake: `container.unpause()`
- Stop: `container.stop()`

Service classification:
| Priority | Services | Sleep Policy |
|----------|----------|-------------|
| High (never sleep) | gateway, service-manager, tool-router | N/A |
| Normal (auto-sleep) | filesystem, git, fetch, memory | 5 min idle |
| Low (extended sleep) | chrome-devtools, playwright, puppeteer | 2 min idle |

API endpoints: GET /health, GET /metrics/*, POST /services/{name}/sleep, POST /services/{name}/wake

## Critical Constraints
- Wake time: **<200ms** normal, **<50ms** critical
- Memory reduction: **>60%** for sleeping services
- CPU reduction: **>80%** for sleeping services
- Health check: respond **<5s** (BR-004)
- Docker errors → HTTP 503, never expose raw SDK exceptions
- Unit tests must mock Docker client

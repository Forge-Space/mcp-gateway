# Monitoring & Observability

Comprehensive monitoring and observability guide for the MCP Gateway tool router.

## Overview

The tool router includes built-in observability features:
- **Health Checks** - Service health and readiness endpoints
- **Structured Logging** - Contextual logging with multiple levels
- **Metrics Collection** - Performance metrics and counters
- **Timing Instrumentation** - Operation duration tracking

## Health Checks

### Health Check Endpoints

The tool router provides health check functionality for monitoring service status.

**Components Monitored:**
- Gateway connectivity and response time
- Configuration validation
- Tool availability

**Health Statuses:**
- `healthy` - All systems operational
- `degraded` - Service running but with issues
- `unhealthy` - Critical failures detected

### Using Health Checks

```python
from tool_router.observability import HealthCheck

health = HealthCheck()

# Full health check
result = health.check_all()
print(f"Status: {result.status}")
print(f"Components: {len(result.components)}")

# Quick readiness check
if health.check_readiness():
    print("Service ready to handle requests")

# Quick liveness check
if health.check_liveness():
    print("Service is alive")
```

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "version": "1.0.0",
  "components": [
    {
      "name": "configuration",
      "status": "healthy",
      "message": "Configuration valid",
      "latency_ms": null,
      "metadata": {
        "base_url": "http://localhost:4444",
        "timeout_ms": 120000,
        "max_retries": 3
      }
    },
    {
      "name": "gateway",
      "status": "healthy",
      "message": "Gateway connection successful",
      "latency_ms": 45.2,
      "metadata": {
        "tool_count": 25
      }
    }
  ]
}
```

## Structured Logging

### Setup Logging

```python
from tool_router.observability import setup_logging, get_logger

# Configure logging
setup_logging(level="INFO", structured=True)

# Get logger instance
logger = get_logger(__name__)

# Log messages
logger.info("Processing task")
logger.warning("High latency detected")
logger.error("Failed to connect to gateway")
```

### Log Levels

- **DEBUG** - Detailed diagnostic information
- **INFO** - General informational messages
- **WARNING** - Warning messages for potential issues
- **ERROR** - Error messages for failures
- **CRITICAL** - Critical failures requiring immediate attention

### Structured Log Format

```
timestamp=2024-02-14T16:30:00 level=INFO logger=tool_router.core.server message=Executing task
timestamp=2024-02-14T16:30:01 level=INFO logger=tool_router.core.server message=Selected tool: tavily_search
timestamp=2024-02-14T16:30:02 level=INFO logger=tool_router.core.server message=Task completed successfully
```

### Log Context

Add contextual information to logs:

```python
from tool_router.observability.logger import LogContext

logger = get_logger(__name__)

with LogContext(logger, request_id="abc123", user="admin"):
    logger.info("Processing request")
    # Logs will include request_id and user fields
```

## Metrics Collection

### Recording Metrics

```python
from tool_router.observability import get_metrics
from tool_router.observability.metrics import TimingContext

metrics = get_metrics()

# Record timing
with TimingContext("operation_name"):
    # Your code here
    pass

# Increment counter
metrics.increment_counter("requests_total")
metrics.increment_counter("errors_total", 1)

# Get statistics
stats = metrics.get_stats("operation_name")
print(f"Average: {stats.avg_ms}ms")
print(f"Min: {stats.min_ms}ms")
print(f"Max: {stats.max_ms}ms")
```

### Available Metrics

**Timing Metrics:**
- `execute_task.total_duration` - Total task execution time
- `execute_task.get_tools` - Time to fetch tools
- `execute_task.pick_best_tools` - Tool selection time
- `execute_task.build_arguments` - Argument building time
- `execute_task.call_tool` - Tool execution time
- `search_tools.total_duration` - Total search time
- `search_tools.get_tools` - Time to fetch tools
- `search_tools.pick_best_tools` - Tool matching time

**Counter Metrics:**
- `execute_task.calls` - Total execute_task calls
- `execute_task.success` - Successful executions
- `execute_task.errors.*` - Error counts by type
- `execute_task.tool_selected.*` - Tool usage counts
- `search_tools.calls` - Total search calls
- `search_tools.success` - Successful searches
- `search_tools.no_matches` - Searches with no results

### Viewing All Metrics

```python
metrics = get_metrics()
all_metrics = metrics.get_all_metrics()

print("Timings:")
for name, stats in all_metrics["timings"].items():
    print(f"  {name}: {stats['avg_ms']}ms avg ({stats['count']} samples)")

print("\nCounters:")
for name, count in all_metrics["counters"].items():
    print(f"  {name}: {count}")
```

## Integration Examples

### FastAPI Health Endpoint

```python
from fastapi import FastAPI
from tool_router.observability import HealthCheck

app = FastAPI()
health_check = HealthCheck()

@app.get("/health")
async def health():
    result = health_check.check_all()
    return result.to_dict()

@app.get("/health/ready")
async def readiness():
    return {"ready": health_check.check_readiness()}

@app.get("/health/live")
async def liveness():
    return {"alive": health_check.check_liveness()}
```

### Prometheus Metrics Export

```python
from tool_router.observability import get_metrics

def export_prometheus_metrics():
    metrics = get_metrics()
    all_metrics = metrics.get_all_metrics()

    lines = []

    # Export timing metrics
    for name, stats in all_metrics["timings"].items():
        metric_name = name.replace(".", "_")
        lines.append(f"# TYPE {metric_name}_seconds summary")
        lines.append(f"{metric_name}_seconds_sum {stats['total_ms'] / 1000}")
        lines.append(f"{metric_name}_seconds_count {stats['count']}")

    # Export counters
    for name, count in all_metrics["counters"].items():
        metric_name = name.replace(".", "_")
        lines.append(f"# TYPE {metric_name}_total counter")
        lines.append(f"{metric_name}_total {count}")

    return "\n".join(lines)
```

### Docker Health Check

```dockerfile
FROM python:3.11-slim

# ... your Dockerfile content ...

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "from tool_router.observability import HealthCheck; \
                 import sys; \
                 sys.exit(0 if HealthCheck().check_readiness() else 1)"
```

## Monitoring Best Practices

### 1. Set Appropriate Log Levels

**Development:**

```python
setup_logging(level="DEBUG", structured=False)
```

**Production:**

```python
setup_logging(level="INFO", structured=True)
```

### 2. Monitor Key Metrics

**Critical Metrics:**
- Gateway connection latency
- Tool execution success rate
- Error rates by type
- Tool selection accuracy

**Alert Thresholds:**
- Gateway latency > 1000ms
- Error rate > 5%
- No tools available
- Configuration invalid

### 3. Use Health Checks

**Kubernetes Probes:**

```yaml
livenessProbe:
  exec:
    command:
    - python
    - -c
    - "from tool_router.observability import HealthCheck; exit(0 if HealthCheck().check_liveness() else 1)"
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  exec:
    command:
    - python
    - -c
    - "from tool_router.observability import HealthCheck; exit(0 if HealthCheck().check_readiness() else 1)"
  initialDelaySeconds: 5
  periodSeconds: 10
```

### 4. Aggregate and Visualize

**Recommended Tools:**
- **Prometheus** - Metrics collection
- **Grafana** - Visualization dashboards
- **ELK Stack** - Log aggregation
- **Datadog** - All-in-one monitoring

## Troubleshooting

### High Latency

**Check metrics:**

```python
metrics = get_metrics()
stats = metrics.get_stats("execute_task.total_duration")
print(f"Average latency: {stats.avg_ms}ms")
```

**Common causes:**
- Slow gateway response
- Network issues
- Too many retries
- Large tool sets

### Frequent Errors

**Check error counters:**

```python
metrics = get_metrics()
errors = {
    k: v for k, v in metrics.get_all_metrics()["counters"].items()
    if "error" in k
}
print(errors)
```

**Common errors:**
- Gateway connection failures
- JWT authentication issues
- Tool selection failures
- Argument building errors

### Service Degradation

**Run health check:**

```python
health = HealthCheck()
result = health.check_all()

for component in result.components:
    if component.status != "healthy":
        print(f"{component.name}: {component.message}")
```

## Next Steps

- **[AI Usage Guide](AI_USAGE.md)** - Effective tool usage patterns
- **[Architecture Overview](../architecture/OVERVIEW.md)** - System design
- **[Development Guide](../development/DEVELOPMENT.md)** - Contributing

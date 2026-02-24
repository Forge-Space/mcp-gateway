# Routing and Performance Patterns

## Purpose
Guide Serena when editing routing logic, load balancing, circuit breaker patterns, caching strategies, and performance optimization code.

## Key Files
- `tool_router/core/server.py` — Main routing and tool execution
- `tool_router/gateway/client.py` — Gateway API client
- `tool_router/scoring/matcher.py` — Tool scoring and selection
- `tool_router/ai/enhanced_selector.py` — AI-powered routing
- `service-manager/service_manager.py` — Service lifecycle and resource management
- `config/services.yml` — Service configurations and sleep policies
- `config/resource-limits.yml` — Resource constraints and efficiency targets

## Architecture / Rules / Patterns

**Tool Routing Flow**:
1. IDE calls `execute_task("task description")`
2. Tool router queries gateway API for all available tools
3. Hybrid AI + keyword scoring (70% AI weight + 30% keyword matching)
4. Best tool selected based on relevance score
5. Arguments auto-built from task description
6. Gateway API executes tool on upstream server
7. Results returned to IDE

**AI-Powered Routing (Ollama Integration)**:
- Local LLM: llama3.2:3b (privacy-focused, zero-cost)
- Hybrid scoring: 70% AI relevance + 30% keyword matching
- Graceful fallback to keyword-only if AI fails
- Model selection based on hardware constraints (Celeron N100: 16GB RAM, 4 cores, no GPU)
- Enterprise BYOK support: Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro, Grok Beta

**Load Balancing Strategy**:
- Least-connections algorithm for service distribution
- Health-based routing (unhealthy services excluded)
- Geographic routing for multi-region deployments
- Weighted routing based on service capacity
- DNS-based routing with failover (Route53, Azure DNS, Cloud DNS)

**Circuit Breaker Pattern**:
- **States**: CLOSED → OPEN → HALF_OPEN → CLOSED
- **Thresholds**: 5 consecutive failures → OPEN state
- **Timeout**: 30 seconds before attempting HALF_OPEN
- **Recovery**: 1 successful request → CLOSED state
- **Failure Types**: Timeout, connection error, 5xx responses

**Caching Strategy (Multi-Level)**:
1. **TTLCache** (in-memory): Fast access, 5-minute TTL
2. **Redis** (distributed): Shared cache, 15-minute TTL
3. **Database** (SQLite/PostgreSQL): Persistent storage
- Cache hit rate target: > 80%
- Cache invalidation on configuration changes
- Performance metrics collection for cache effectiveness

**Connection Pooling**:
- HTTP connection pool: 10 max connections per host
- Database connection pool: 20 max connections
- Connection timeout: 30 seconds
- Idle timeout: 5 minutes
- Connection recycling after 1 hour

**Resource Monitoring**:
- Real-time CPU, memory, disk, network metrics
- Container-level resource tracking (Docker stats API)
- Performance baselines and anomaly detection
- Resource pressure detection for auto-sleep/wake
- Metrics collection every 30 seconds

## Critical Constraints
- Tool router response time MUST be < 500ms (actual: 50-100ms)
- Cache hit rate MUST be > 80% for optimal performance
- Circuit breaker MUST open after 5 consecutive failures
- Connection pool MUST limit max connections to prevent resource exhaustion
- AI routing fallback to keyword-only MUST be seamless (no errors to user)
- Service wake time MUST be < 200ms (95th percentile)
- Memory reduction for sleeping services MUST be > 60%
- Health checks MUST complete within 5 seconds

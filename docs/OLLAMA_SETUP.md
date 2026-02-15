# Ollama Setup Guide

Ollama provides local LLM inference for the AI Router feature in MCP Gateway.

---

## Quick Setup

### 1. Start Gateway (Ollama starts automatically)

```bash
./scripts/mcp start
```

### 2. Pull Required Model

The AI Router uses `llama3.2:3b` by default (2GB download):

```bash
# Pull the model
docker exec ollama ollama pull llama3.2:3b

# Verify installation
docker exec ollama ollama list
```

**Expected output:**
```
NAME              ID              SIZE      MODIFIED
llama3.2:3b       dde5aa3fc5ff    2.0 GB    2 minutes ago
```

---

## Configuration

### Environment Variables

Edit `.env` to configure Ollama:

```bash
# Ollama Configuration
OLLAMA_PORT=11434                           # Ollama API port
ROUTER_AI_ENABLED=true                      # Enable AI routing
ROUTER_AI_PROVIDER=ollama                   # Use Ollama
ROUTER_AI_MODEL=llama3.2:3b                 # Model to use
ROUTER_AI_ENDPOINT=http://ollama:11434      # Ollama endpoint
ROUTER_AI_TIMEOUT_MS=5000                   # Request timeout
ROUTER_AI_WEIGHT=0.7                        # AI routing weight
```

---

## Available Models

### Recommended Models

| Model | Size | Use Case | Command |
|-------|------|----------|---------|
| **llama3.2:3b** | 2GB | Default, fast, good quality | `ollama pull llama3.2:3b` |
| llama3.2:1b | 1.3GB | Fastest, lower quality | `ollama pull llama3.2:1b` |
| llama3.1:8b | 4.7GB | Better quality, slower | `ollama pull llama3.1:8b` |
| qwen2.5:3b | 2.0GB | Alternative, multilingual | `ollama pull qwen2.5:3b` |

### Pull Additional Models

```bash
# List available models
docker exec ollama ollama list

# Pull a different model
docker exec ollama ollama pull llama3.1:8b

# Update .env to use new model
echo "ROUTER_AI_MODEL=llama3.1:8b" >> .env

# Restart to apply changes
./scripts/mcp restart
```

---

## Testing Ollama

### 1. Check Ollama Status

```bash
# Check if Ollama is running
curl http://localhost:11434/

# List installed models
curl http://localhost:11434/api/tags
```

### 2. Test Model Inference

```bash
# Simple test
docker exec ollama ollama run llama3.2:3b "Hello, how are you?"

# Interactive chat
docker exec -it ollama ollama run llama3.2:3b
```

### 3. Test AI Router

```bash
# Check tool_router logs for AI routing
./scripts/mcp logs tool-router | grep -i "ai router"

# Test via API (requires gateway running)
curl -X POST http://localhost:8030/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "search for MCP documentation"}'
```

---

## Troubleshooting

### Ollama Container Unhealthy

**Symptom:** `dependency failed to start: container ollama is unhealthy`

**Cause:** Health check failing during startup or model download.

**Fix:**
```bash
# Check Ollama logs
./scripts/mcp logs ollama

# Restart Ollama
docker compose restart ollama

# Wait for health check (30s)
docker compose ps ollama
```

### Model Not Found

**Symptom:** `Error: model 'llama3.2:3b' not found`

**Fix:**
```bash
# Pull the model
docker exec ollama ollama pull llama3.2:3b

# Verify
docker exec ollama ollama list
```

### Slow Model Download

**Symptom:** Model download taking too long or timing out.

**Fix:**
```bash
# Use smaller model
docker exec ollama ollama pull llama3.2:1b
echo "ROUTER_AI_MODEL=llama3.2:1b" >> .env
./scripts/mcp restart

# Or disable AI routing temporarily
echo "ROUTER_AI_ENABLED=false" >> .env
./scripts/mcp restart
```

### Out of Memory

**Symptom:** Ollama crashes or containers get killed (exit code 137).

**Fix:**
```bash
# Use smaller model
docker exec ollama ollama pull llama3.2:1b

# Or increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory → 8GB+

# Or disable Ollama
docker compose stop ollama
echo "ROUTER_AI_ENABLED=false" >> .env
./scripts/mcp restart
```

---

## Performance Optimization

### 1. Use Smaller Models

Smaller models = faster inference + less memory:

```bash
# 1B model (fastest)
docker exec ollama ollama pull llama3.2:1b
echo "ROUTER_AI_MODEL=llama3.2:1b" >> .env
```

### 2. Adjust Keep-Alive

Control how long models stay in memory:

```bash
# Keep loaded for 24h (default)
echo "OLLAMA_KEEP_ALIVE=24h" >> .env

# Unload immediately after use (saves memory)
echo "OLLAMA_KEEP_ALIVE=0" >> .env

# Keep loaded for 1 hour
echo "OLLAMA_KEEP_ALIVE=1h" >> .env
```

### 3. GPU Acceleration (if available)

Ollama automatically uses GPU if available:

```bash
# Check GPU detection
docker exec ollama ollama run llama3.2:3b --verbose

# For NVIDIA GPUs, ensure nvidia-docker is installed
# For Apple Silicon, Metal acceleration is automatic
```

---

## Disabling Ollama

If you don't need AI routing:

```bash
# Disable AI Router
echo "ROUTER_AI_ENABLED=false" >> .env

# Stop Ollama container
docker compose stop ollama

# Restart gateway
./scripts/mcp restart
```

---

## Advanced Configuration

### Custom Ollama Endpoint

Use external Ollama instance:

```bash
# Point to external Ollama
echo "ROUTER_AI_ENDPOINT=http://192.168.1.100:11434" >> .env

# Disable local Ollama container
docker compose stop ollama
```

### Multiple Models

Run multiple models for different use cases:

```bash
# Pull multiple models
docker exec ollama ollama pull llama3.2:3b
docker exec ollama ollama pull qwen2.5:3b

# Switch models by updating .env
echo "ROUTER_AI_MODEL=qwen2.5:3b" >> .env
./scripts/mcp restart
```

---

## Resources

- **Ollama Documentation**: https://ollama.com/docs
- **Model Library**: https://ollama.com/library
- **AI Router Documentation**: `docs/ai-router/README.md`
- **Performance Tuning**: `docs/PERFORMANCE.md`

---

## Quick Reference

```bash
# Start with Ollama
./scripts/mcp start

# Pull model
docker exec ollama ollama pull llama3.2:3b

# Check status
docker compose ps ollama
curl http://localhost:11434/api/tags

# View logs
./scripts/mcp logs ollama

# Test inference
docker exec ollama ollama run llama3.2:3b "test"

# Disable Ollama
echo "ROUTER_AI_ENABLED=false" >> .env
./scripts/mcp restart
```

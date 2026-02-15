# AI-Powered Tool Router Guide

## Overview

The MCP Gateway tool router now includes AI-powered tool selection using **Ollama**, a free, local LLM service. This enhancement provides intelligent tool routing with natural language understanding, combined with traditional keyword matching for reliability.

## Architecture

### Hybrid Scoring System

The router uses a **hybrid approach** that combines:

1. **AI Selection (70% weight)**: LLM analyzes task and tool descriptions using natural language understanding
2. **Keyword Matching (30% weight)**: Traditional token-based scoring for reliability

This hybrid approach provides:
- **Intelligent routing** for complex, ambiguous tasks
- **Fallback reliability** when AI times out or fails
- **Tunable balance** between AI and keyword scoring

### Automatic Fallback

The system automatically falls back to keyword-only matching when:
- AI selection times out (default: 2 seconds)
- Ollama service is unavailable
- AI confidence is too low (<0.3)
- Any AI-related error occurs

## Setup

### 1. Start the Stack

The Ollama service is included in `docker-compose.yml`:

```bash
make start
```

On first start, Docker will pull the Ollama image (~1GB) and the system will automatically pull the `llama3.2:3b` model (~2GB).

### 2. Configuration

AI router settings are configured via environment variables in `.env`:

```bash
# Enable/disable AI selection (default: true)
ROUTER_AI_ENABLED=true

# Model to use (default: llama3.2:3b)
ROUTER_AI_MODEL=llama3.2:3b

# Ollama endpoint (default: http://ollama:11434)
ROUTER_AI_ENDPOINT=http://ollama:11434

# Timeout for AI selection in ms (default: 2000)
ROUTER_AI_TIMEOUT_MS=2000

# Weight for AI score in hybrid scoring (default: 0.7)
# Range: 0.0 (pure keyword) to 1.0 (pure AI)
ROUTER_AI_WEIGHT=0.7
```

### 3. Verify Setup

Check that Ollama is running:

```bash
docker ps | grep ollama
```

Test AI router:

```bash
# Via tool-router MCP tool
# The execute_task tool will automatically use AI selection
```

## Supported Models

### Recommended Models

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `llama3.2:3b` | ~2GB | Fast | Good | **Default - balanced performance** |
| `llama3.2:1b` | ~1GB | Very Fast | Fair | Resource-constrained environments |
| `mistral:7b` | ~4GB | Medium | Better | Higher accuracy requirements |
| `llama3.1:8b` | ~5GB | Slower | Best | Maximum accuracy |

### Changing Models

Update `.env`:

```bash
ROUTER_AI_MODEL=mistral:7b
```

Restart services:

```bash
make stop
make start
```

The new model will be pulled automatically on first use.

## Performance Tuning

### Timeout Adjustment

Increase timeout for larger models:

```bash
# For mistral:7b or larger models
ROUTER_AI_TIMEOUT_MS=3000
```

### AI Weight Tuning

Adjust hybrid scoring balance:

```bash
# More AI influence (90% AI, 10% keyword)
ROUTER_AI_WEIGHT=0.9

# More keyword influence (50% AI, 50% keyword)
ROUTER_AI_WEIGHT=0.5

# Pure keyword (disable AI influence)
ROUTER_AI_WEIGHT=0.0
```

### Disable AI Selection

```bash
ROUTER_AI_ENABLED=false
```

This reverts to pure keyword matching (fastest, but less intelligent).

## Monitoring

### Metrics

The tool router exposes metrics for AI selection:

- `execute_task.ai_selection.success` - Successful AI selections
- `execute_task.ai_selection.low_confidence` - AI confidence too low
- `execute_task.ai_selection.error` - AI selection errors
- `execute_task.keyword_selection` - Fallback to keyword matching
- `execute_task.ai_confidence` - AI confidence scores (gauge)
- `execute_task.selection_method.hybrid_ai` - Hybrid AI+keyword selections
- `execute_task.selection_method.keyword` - Pure keyword selections

### Logs

AI selection logs include:

```text
INFO: AI selected: brave_web_search (confidence: 0.95) - Task requires web search
INFO: Selected tool: brave_web_search (method: hybrid_ai)
```

Fallback logs:

```text
WARNING: AI selection timeout (2.0s) for task: search...
INFO: Selected tool: brave_web_search (method: keyword)
```

## Troubleshooting

### Ollama Service Not Available

**Symptom**: Logs show "Ollama service not available"

**Solution**:
1. Check if Ollama container is running: `docker ps | grep ollama`
2. Check logs: `docker logs ollama`
3. Restart: `docker restart ollama`

### Model Not Found (404)

**Symptom**: Logs show "Model llama3.2:3b not found"

**Solution**:

```bash
# Pull model manually
docker exec -it ollama ollama pull llama3.2:3b

# Or restart to trigger automatic pull
docker restart tool-router
```

### Slow Performance

**Symptom**: Tool routing takes >5 seconds

**Solutions**:
1. Reduce timeout: `ROUTER_AI_TIMEOUT_MS=1500`
2. Use smaller model: `ROUTER_AI_MODEL=llama3.2:1b`
3. Reduce AI weight: `ROUTER_AI_WEIGHT=0.5`
4. Disable AI: `ROUTER_AI_ENABLED=false`

### Low Accuracy

**Symptom**: Wrong tools being selected

**Solutions**:
1. Increase AI weight: `ROUTER_AI_WEIGHT=0.9`
2. Use larger model: `ROUTER_AI_MODEL=mistral:7b`
3. Increase timeout: `ROUTER_AI_TIMEOUT_MS=3000`

## Best Practices

1. **Use default settings** for balanced performance (llama3.2:3b, 70% AI weight, 2s timeout)
2. **Monitor metrics** to understand AI vs keyword selection rates
3. **Tune gradually** - adjust one parameter at a time
4. **Test with realistic tasks** to validate routing accuracy
5. **Keep Ollama updated** for model improvements

## Advanced: Custom Models

To use custom or quantized models:

1. Pull model in Ollama container:

   ```bash
   docker exec -it ollama ollama pull your-model:tag
   ```

2. Update `.env`:

   ```bash
   ROUTER_AI_MODEL=your-model:tag
   ```

3. Restart tool-router:

   ```bash
   docker restart tool-router
   ```

## See Also

- [Tool Router Architecture](../architecture/TOOL_ROUTER_GUIDE.md)
- [Environment Configuration](../ENVIRONMENT_CONFIGURATION.md)
- [Ollama Documentation](https://ollama.ai/docs)

# Tool Router AI Architecture

## Purpose
Guides editing of the hybrid AI + keyword tool selection system in `tool_router/ai/`.

## Key Files
- `tool_router/ai/selector.py` — `OllamaSelector` class; calls Ollama API, returns scored tools
- `tool_router/ai/prompts.py` — prompt templates for tool selection queries
- `tool_router/core/server.py` — main FastMCP server, integrates AI selector
- `tool_router/ai/enhanced_selector.py` — `EnhancedAISelector` with cost optimization
- `tool_router/ai/prompt_architect.py` — `PromptArchitect` for prompt optimization

## Architecture
Hybrid scoring model combines local LLM inference with keyword matching:
```
final_score = (0.70 × ai_score) + (0.30 × keyword_score)
```
- AI score (70%): Ollama LLM relevance score via `OllamaSelector`
- Keyword score (30%): existing keyword-based relevance
- Fallback: if Ollama unavailable → keyword-only (100%)

Ollama config: model `llama3.2:3b`, endpoint `localhost:11434`, all inference local (privacy).

Fallback chain (must never crash the router):
1. Connection refused → keyword-only
2. Timeout → keyword-only
3. Malformed response → keyword-only
4. Unhandled exception → log WARNING, keyword-only

## Critical Constraints
- **IMMUTABLE weights**: 70% AI + 30% keyword — never change without explicit instruction
- Response target: **<500ms**
- Tool limit: **≤2 tools** exposed to IDE (BR-001)
- Must query gateway API for available tools before scoring
- Mock Ollama in unit tests — never require live instance
- Coverage: maintain **≥85%** (current 88.29%, 22 tests)

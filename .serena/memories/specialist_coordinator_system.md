# Specialist Coordinator System

## Purpose
Guides editing of the domain-specific AI specialist architecture.

## Key Files
- `tool_router/specialist_coordinator.py` — `SpecialistCoordinator` orchestrator
- `tool_router/ai/enhanced_selector.py` — `EnhancedAISelector` with cost optimization
- `tool_router/ai/prompt_architect.py` — `PromptArchitect` for prompt analysis/optimization
- `tool_router/ai/ui_specialist.py` — `UISpecialist` for component generation

## Architecture
Three specialist agents coordinated by `SpecialistCoordinator`:

1. **Router** (`SpecialistType.ROUTER`): Tool selection via `EnhancedAISelector`
   - Hardware-aware, cost-optimized, token estimation
2. **Prompt Architect** (`SpecialistType.PROMPT_ARCHITECT`): Prompt optimization
   - Task analysis, token reduction, quality scoring, iterative refinement
3. **UI Specialist** (`SpecialistType.UI_SPECIALIST`): Component generation
   - Multi-framework (React, Vue, Angular, Svelte, Next.js)
   - Multi-design-system (Tailwind, Material, Bootstrap, Ant, Chakra)
   - Accessibility levels (minimal, AA, AAA)

Task routing by `TaskCategory`:
- `TOOL_SELECTION` → Router only
- `PROMPT_OPTIMIZATION` → Prompt Architect only
- `UI_GENERATION` → UI Specialist only
- `CODE_GENERATION` → Prompt Architect → Router (chained)
- `MULTI_STEP` → keyword-based multi-specialist dispatch

Data flow: `TaskRequest` → `SpecialistCoordinator.process_task()` → `List[SpecialistResult]`
Each result has: specialist_type, result, confidence, processing_time_ms, cost_estimate, metadata.

Performance tracking: `_routing_stats` dict with request counts, avg time, cost savings.

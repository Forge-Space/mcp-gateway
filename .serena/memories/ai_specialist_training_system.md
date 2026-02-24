# AI Specialist Training System

## Purpose
Guide Serena when editing AI specialist agents, training infrastructure, model selection, feedback loops, and knowledge base management.

## Key Files
- `SPECIALIST_ARCHITECTURE_IMPLEMENTATION.md` — Complete specialist architecture
- `SPECIALIST_TRAINING_SUMMARY.md` — Training infrastructure documentation
- `tool_router/ai/enhanced_selector.py` — Router Agent (hardware-aware model selection)
- `tool_router/ai/prompt_architect.py` — Prompt Architect (token optimization)
- `tool_router/ai/ui_specialist.py` — UI Specialist (component generation)
- `tool_router/specialist_coordinator.py` — Multi-agent orchestration
- `tool_router/training/training_pipeline.py` — Training orchestration
- `tool_router/training/knowledge_base.py` — SQLite knowledge base
- `config/specialist-agents.yaml` — Specialist configuration

## Architecture / Rules / Patterns

**Three Specialist Agents**:

1. **Router Agent** (enhanced_selector.py):
   - Hardware-aware model selection (Intel Celeron N100: 16GB RAM, 4 cores, no GPU)
   - Model tiering: ultra_fast → fast → balanced → premium → enterprise
   - Cost optimization with token estimation
   - Local model priority: llama3.2:3b, tinyllama, phi3:mini (zero-cost)
   - Enterprise BYOK: Claude 3.5 Sonnet ($3.00/1M), GPT-4o ($2.50/1M), Gemini 1.5 Pro ($2.00/1M), Grok Beta ($3.50/1M)

2. **Prompt Architect** (prompt_architect.py):
   - Task type identification (UI generation, API design, database schema)
   - Token minimization algorithms (up to 40% reduction)
   - Quality scoring: clarity, completeness, specificity, efficiency (baseline 0.6+)
   - Iterative refinement with feedback loops
   - Multi-language support and context-aware optimization

3. **UI Specialist** (ui_specialist.py):
   - Multi-framework support: React, Vue, Angular, Svelte, Next.js (10+ frameworks)
   - Design systems: Material Design, Tailwind UI, Bootstrap, Carbon Design (8+ systems)
   - WCAG accessibility compliance (AA/AAA levels)
   - React 2024 best practices: functional components, hooks, TypeScript
   - Atomic Design and Feature-Sliced Design patterns

**Specialist Coordinator** (specialist_coordinator.py):
- Intelligent task categorization and routing
- Multi-specialist coordination for complex tasks
- Performance monitoring and analytics
- Cost tracking and optimization per specialist
- Cache management for efficiency

**Training Infrastructure**:

1. **Data Extraction** (data_extraction.py):
   - Web documentation: React 2024 docs, design systems, WCAG guidelines
   - GitHub repositories: shadcn/ui, Material-UI, Ant Design
   - Pattern detection: React patterns, UI components, accessibility features
   - Confidence scoring for extracted patterns

2. **Knowledge Base** (knowledge_base.py):
   - SQLite storage with full-text search
   - Pattern categories: React, UI components, accessibility, prompt engineering, architecture
   - Metadata tracking: usage statistics, effectiveness scores, timestamps
   - Search and indexing for fast retrieval

3. **Training Pipeline** (training_pipeline.py):
   - Multi-stage: Extraction → Validation → Population → Training → Evaluation
   - Continuous learning with feedback loops
   - Quality assurance and validation at each stage
   - Pattern versioning and change tracking

4. **Evaluation Framework** (evaluation.py):
   - Comprehensive metrics: accuracy, precision, recall, F1-score, response time
   - Benchmark suites for each specialist type
   - Performance analysis and recommendations
   - Comparative analysis across specialists

**MCP Gateway Integration**:
- `execute_specialist_task`: Main entry point for specialist processing
- `get_specialist_stats`: Performance and capability reporting
- `optimize_prompt`: Dedicated prompt optimization tool

## Critical Constraints
- Hardware constraints MUST be enforced: 8GB max per model, 16GB total RAM, 4 cores CPU, no GPU
- Local models MUST be prioritized for zero-cost operations (llama3.2:3b first)
- Token optimization MUST achieve minimum 20% reduction (target: 40%)
- Quality scores MUST be ≥ 0.6 for production use
- UI components MUST be WCAG AA compliant (AAA preferred)
- Response times: Router < 100ms, Prompt Architect < 500ms, UI Specialist < 3s
- Cost tracking MUST be enabled for all enterprise models
- Pattern confidence scores MUST be > 0.7 for knowledge base insertion
- Feedback loops MUST update pattern effectiveness scores continuously

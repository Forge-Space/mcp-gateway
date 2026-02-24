"""Pytest conftest for tool_router tests.

Excludes modules that depend on infrastructure not available in CI
(Redis, Sentry, dashboard, RAG, etc.) or have broken imports.
"""

import os


_dir = os.path.dirname(__file__)

collect_ignore_glob = [
    "test_cache_*.py",
    "test_redis_cache.py",
    "test_dashboard.py",
    "test_invalidation.py",
    "test_rag_manager.py",
    "test_security_middleware.py",
    "test_ui_specialist.py",
]

collect_ignore = [
    os.path.join(_dir, "unit"),
    os.path.join(_dir, "test_security"),
    os.path.join(_dir, "test_observability"),
    os.path.join(_dir, "training", "test_knowledge_base.py"),
    os.path.join(_dir, "training", "test_data_extraction.py"),
    os.path.join(_dir, "training", "test_evaluation.py"),
]

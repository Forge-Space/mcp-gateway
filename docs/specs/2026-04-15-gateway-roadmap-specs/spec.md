---
status: proposed
created: 2026-04-15
owner: lucassantana
pr:
tags: roadmap,specs,gateway
---

# gateway-roadmap-specs

## Goal
Represent MCP Gateway phases with durable specs that survive handoffs and support RAG retrieval.

## Context
Gateway work already uses phase language in docs and commits. Committed specs give those phases tasks, status, and PR links.

## Approach
Seed a proposed spec, regenerate docs/roadmap.md, and use spec status as the source of truth for future phase planning.

## Verification
docs/roadmap.md is generated from this spec and RAG can return it for gateway roadmap queries.

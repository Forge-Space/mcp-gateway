# Forge Space Strategic Positioning (2026-02-24)

## Identity
- **What**: "The Open Full-Stack AI Workspace"
- **Tagline**: "Generate. Integrate. Ship."
- **mcp-gateway role**: The central AI tool routing hub — connects any MCP server, routes intelligently, manages via admin UI. The "USB-C of AI dev tools".

## How mcp-gateway fits
- Core infrastructure enabling MCP-native architecture (key differentiator #1)
- Supports multi-LLM (Gemini, Claude, GPT) without code changes
- Users can add custom MCP servers for their domain
- Tool chaining (brand → UI → code → deploy) in one session

## Monetization relevance
- Free tier: self-hosted gateway (Docker)
- Paid: "Managed MCP Gateway" — hosted gateway-as-a-service ($25/user/month) — planned for month 4-8
- Enterprise: custom MCP server development, integration services

## Ecosystem context
| Repo | Purpose |
|------|---------|
| siza | AI workspace frontend (Next.js 16, Cloudflare Workers) |
| siza-mcp | 12 MCP tools for UI generation |
| **mcp-gateway** | **AI-powered tool routing hub (this repo)** |
| forge-patterns | Shared standards, MCP context server |
| branding-mcp | Brand identity generation (7 tools) |

## Pricing tiers (siza webapp)
Free ($0), Pro ($19/mo), Team ($49/mo, 5 seats), Enterprise (custom)

## Community
- CONTRIBUTING.md added (2026-02-24)
- GitHub labels: good first issue, help wanted, community, enhancement, documentation, mcp
- Public roadmap via GitHub Projects (pending token scope)

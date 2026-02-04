---
name: mcp-docs-search
description: Use MCP tools for docs lookup and web search. Use when needing up-to-date docs, APIs, or best practices.
---

# MCP Docs & Search

## When to use

- Needing current docs for libraries (e.g. React, Vite, Tailwind, Express, Prisma, TypeScript)
- Searching for APIs, errors, or best practices
- Multi-step reasoning or architecture decisions

## Preferred MCPs

| Task                 | MCP                                                                 | Use                                      |
| -------------------- | ------------------------------------------------------------------- | ---------------------------------------- |
| Library docs         | **user-Context7**                                                   | Node, React, Tailwind, Prisma, etc.      |
| Web search           | **user-tavily**                                                     | APIs, errors, best practices, tutorials  |
| Multi-step reasoning | **user-sequential-thinking**                                        | Architecture, refactors, migration steps |
| GitHub               | **user-GitHub**                                                     | Issues, PRs, repo metadata               |
| Browser/E2E          | **user-playwright**, **cursor-ide-browser**, **user-browser-tools** | E2E tests, UI verification               |
| UI ideas             | **user-v0**, **user-@magicuidesign/mcp**                            | Reference only; adapt to repo            |
| Cloudflare           | **user-cloudflare-observability**, **user-cloudflare-bindings**     | When project uses Cloudflare Workers     |

## Use when needed (not default)

- **radar_search**, **mcp-gateway**, **user-desktop-commander**, **user-apify-dribbble**, **MCP_DOCKER**, **curl**: Only when the task clearly requires them (e.g. Docker API, desktop automation, scraping).
- **user-minecraft**, **composio**: Use when explicitly required by the task.

## Conventions

- Prefer Context7 for official library docs before assuming API behavior.
- Use Tavily for errors, version-specific notes, or when Context7 doesn’t cover the topic.
- Don’t force MCPs; use the one that fits the task.

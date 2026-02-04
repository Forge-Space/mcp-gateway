---
name: backend-express
description: Work with Express API backends. Use when editing backend routes, middleware, or services.
---

# Backend (Express)

## When to use

- Editing backend — routes, middleware, services
- Adding or changing API endpoints, auth, or session handling
- Backend tests or integration with shared services

## Structure (adapt to project)

- **Entry**: e.g. `src/server.ts` or `packages/backend/src/server.ts`
- **Routes**: under `src/routes/` or equivalent
- **Middleware**: under `src/middleware/`
- **Services**: under `src/services/`

## Conventions

- Use project config and env (e.g. `.env`); no hardcoded secrets.
- Auth and session: per project (OAuth, JWT, etc.).
- Responses: consistent JSON; appropriate HTTP status codes; no stack traces or secrets in responses.
- Tests: unit and integration under project test dirs.

## Commands (adapt to project)

- Dev: `npm run dev` or `npm run dev:backend`
- Build: `npm run build`
- Tests: `npm run test`

## MCP

- **user-Context7**: Express, Node, TypeScript docs
- **user-sequential-thinking**: Multi-step API or auth design

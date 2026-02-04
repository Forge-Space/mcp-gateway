---
name: frontend-react-vite
description: Work with React + Vite + Tailwind frontends. Use when editing UI components, pages, or frontend tests.
---

# Frontend (React, Vite, Tailwind)

## When to use

- Editing frontend — components, pages, hooks, stores, services
- Adding or changing UI, routing, or API calls from the webapp
- Frontend styling (Tailwind), tests, or E2E flows

## Structure (adapt to project)

- **Entry**: e.g. `src/main.tsx` → `App.tsx`
- **Pages**: under `src/pages/` or `src/app/` (App Router)
- **Components**: under `src/components/` — layout, feature, ui
- **State**: stores or context; API client (e.g. `src/services/api.ts`)
- **Types**: under `src/types/`

## Conventions

- React + TypeScript; API via backend base URL from env.
- Functional components and hooks; keep components small and focused.
- Styling: Tailwind; follow existing patterns in the project.
- Tests: unit and E2E (e.g. Playwright) when changing user flows.

## Commands (adapt to project)

- Dev: `npm run dev` or `npm run dev:frontend`
- Build: `npm run build:frontend` or `npm run build`
- Lint/typecheck: `npm run lint`, `npm run type:check`

## MCP

- **user-Context7**: React, Vite, Tailwind, TypeScript docs
- **user-browser-tools** / **cursor-ide-browser**: E2E and browser checks
- **user-v0** / **user-@magicuidesign/mcp**: UI ideas; adapt to repo patterns

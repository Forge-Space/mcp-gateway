# NPM Publish Guide (`@forge-mcp-gateway/client`)

This guide is the canonical runbook for restoring and operating npm publication for the MCP client
package.

## Scope

- Package: `@forge-mcp-gateway/client`
- Workflow: `.github/workflows/npm-release-core.yml`
- npm page: https://www.npmjs.com/package/@forge-mcp-gateway/client

## Preconditions

1. `package.json` has the intended `name` and `version`.
2. Repository secret `NPM_TOKEN` exists and belongs to an account with write access to
   `@forge-mcp-gateway`.
3. Local validation passes:
   - `npm ci --legacy-peer-deps --ignore-scripts`
   - `npm run lint:check`
   - `npm run lint:types`
   - `npm run build`

## Workflow behavior

The workflow has three execution modes:

1. PR validation mode (`pull_request`):
   - Runs lint/type/build and `npm publish --dry-run`.
   - Does not publish.
2. Manual publish mode (`workflow_dispatch` with `publish=true`):
   - Runs validation, verifies npm token, performs advisory scope preflight, publishes, then verifies resolvability.
3. Tag publish mode (`push` on `core-v*` tags):
   - Runs publish automatically.
   - Uses `next` for prerelease versions and `latest` for stable versions.

## Manual publish (recommended)

```bash
gh workflow run npm-release-core.yml \
  -f publish=true \
  -f npm_tag=latest
```

Use `npm_tag=next` when intentionally publishing prerelease tracks.

## Manual dry run

```bash
gh workflow run npm-release-core.yml \
  -f publish=false \
  -f npm_tag=latest
```

## What the workflow verifies

Before publish:

- Token exists (`NPM_TOKEN`)
- Auth works (`npm whoami`)
- Scope access preflight warns if unavailable (`npm access list packages @forge-mcp-gateway --json`)
- Target version is not already published

After publish:

- `npm view @forge-mcp-gateway/client@<version> version` resolves
- `npx -y @forge-mcp-gateway/client@<version> --help` executes

If any step fails, the workflow fails with explicit error messages.

## Operational checks

After successful publish, verify locally:

```bash
npm view @forge-mcp-gateway/client version
npx -y @forge-mcp-gateway/client --help
```

Then update setup docs/UI copy if they still show the temporary "npm unavailable" warning.

## Common failure modes

1. `npm access list packages @forge-mcp-gateway --json` returns `E403`:
   - Preflight warning only; workflow continues to publish step.
   - If publish then fails with `E403`, token user lacks org/package scope permission.
   - Fix org membership/permissions and rotate `NPM_TOKEN`.
2. `Version already exists on npm`:
   - Bump package version and retry.
3. Post-publish verification timeout:
   - Retry once after registry propagation delay.
   - If still failing, inspect package metadata and binary entrypoint.

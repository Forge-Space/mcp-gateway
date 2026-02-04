# Development

## Local dev loop

1. Edit `scripts/gateways.txt`, `scripts/prompts.txt`, or `.env`.
2. `make start` (or `make gateway-only` for gateway only).
3. `make register`; optionally `make list-prompts` to verify prompts.
4. Test in Cursor with the URL from `make register` or Admin UI. Use the [Automatic JWT wrapper](../README.md#connect-cursor) for context-forge.

## Adding a gateway

- **No auth:** Add `Name|URL` or `Name|URL|Transport` to `scripts/gateways.txt`, or `EXTRA_GATEWAYS` in `.env`. Run `make register`.
- **Auth (API key, OAuth):** Add in Admin UI → edit gateway → Passthrough Headers or OAuth. See [ADMIN_UI_MANUAL_REGISTRATION.md](ADMIN_UI_MANUAL_REGISTRATION.md).

~60 tools per Cursor connection: use `scripts/virtual-servers.txt` (one server per line: `ServerName|gateway1,gateway2,...`), then `make register`. See [AI_USAGE.md – Tool limit](AI_USAGE.md#tool-limit-and-virtual-servers). Duplicate servers: `make cleanup-duplicates` (`CLEANUP_DRY_RUN=1` to report only).

## Prompts / resources

Format: prompts `name|description|template` ({{arg}}, `\n`); resources `name|uri|description|mime_type`. Set `REGISTER_PROMPTS=true` or `REGISTER_RESOURCES=true`, edit `scripts/prompts.txt` or `scripts/resources.txt`, run `make register`. See [scripts/README.md](../scripts/README.md) and `.env.example`.

## Troubleshooting

[README – Troubleshooting](../README.md#troubleshooting). SQLite corruption: [data/README.md](../data/README.md#recovery-from-sqlite-corruption).

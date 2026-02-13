# Data directory

Used at runtime by the gateway container. SQLite database: `mcp.db` (created on first start). Ignored by git: `*.db`, `*.db-shm`, `*.db-wal`.

## Recovery from SQLite corruption

If the gateway logs `database disk image is malformed` or `FileLock health check failed` (sqlite3.DatabaseError), the DB file is corrupted. Fix:

1. Stop the stack: `./start.sh stop`
2. Remove the DB (and WAL/SHM if present):
   `rm -f ./data/mcp.db ./data/mcp.db-shm ./data/mcp.db-wal`
3. Start again: `./start.sh`

The gateway will create a new empty database. Re-register gateways via Admin UI or `./scripts/register-gateways.sh`. Any previously configured gateways and virtual servers are lost; backup `./data` before deleting if you need to attempt recovery elsewhere.

## Local Docker translate services

These run with `./start.sh` and are registered via `./scripts/register-gateways.sh` (see `scripts/gateways.txt`).

| Service             | Port | Internal URL                        |
| ------------------- | ---- | ----------------------------------- |
| sequential-thinking | 8013 | http://sequential-thinking:8013/sse |
| chrome-devtools     | 8014 | http://chrome-devtools:8014/sse     |
| playwright          | 8015 | http://playwright:8015/sse          |
| magicuidesign-mcp   | 8016 | http://magicuidesign-mcp:8016/sse   |
| desktop-commander   | 8017 | http://desktop-commander:8017/sse   |
| puppeteer           | 8018 | http://puppeteer:8018/sse           |
| browser-tools       | 8019 | http://browser-tools:8019/sse       |
| tavily              | 8020 | http://tavily:8020/sse              |
| filesystem          | 8021 | http://filesystem:8021/sse          |
| reactbits           | 8022 | http://reactbits:8022/sse           |
| snyk                | 8023 | http://snyk:8023/sse                |
| sqlite              | 8024 | http://sqlite:8024/sse              |
| github              | 8025 | http://github:8025/sse              |

Optional env: `TAVILY_API_KEY` (tavily), `FILESYSTEM_VOLUME`, `FILESYSTEM_PATH` (filesystem), `SNYK_TOKEN` (snyk), `SQLITE_DB_PATH`, `SQLITE_VOLUME` (sqlite), `GITHUB_PERSONAL_ACCESS_TOKEN` (github). See `.env.example`.

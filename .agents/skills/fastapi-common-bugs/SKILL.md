---
name: fastapi-common-bugs
description: Identifies and fixes common FastAPI bugs specific to this repo: routers not registered in http_server.py, function names shadowing imports, hardcoded timestamps in probes, unclosed SQLite connections, and deprecated Query(regex=). Use when adding new API endpoints, auditing existing routers, or investigating 404/500 errors on known endpoints.
---

# FastAPI Common Bugs in MCP Gateway

## Bug Pattern 1: Router Defined But Never Mounted

**Symptom**: Endpoint defined with `APIRouter`, tests pass, but hitting the URL returns 404 in production.

**Root cause**: `http_server.py` never calls `app.include_router(my_router)`.

**Check**:
```bash
grep -n "include_router" tool_router/http_server.py
# Compare against:
ls tool_router/api/*.py | xargs grep -l "router = APIRouter"
```

**Fix**: Add to `http_server.py`:
```python
from tool_router.api.my_module import router as my_router
# ...
app.include_router(my_router)
```

**Also add to openapi_tags** in the `FastAPI()` constructor.

## Bug Pattern 2: Import Shadowed by Endpoint Function

**Symptom**: Endpoint calls itself recursively → uncaught exception → 500 error.

**Root cause**: Import name and endpoint function name are the same.

```python
# Bug: get_cache_metrics imported then shadowed by async def get_cache_metrics()
from ..cache import get_cache_metrics   # import
async def get_cache_metrics():          # shadows the import!
    metrics = get_cache_metrics()       # calls ITSELF recursively!
```

**Fix**: Alias the import:
```python
from ..cache import get_cache_metrics as _get_cache_metrics_data
async def get_cache_metrics():
    metrics = _get_cache_metrics_data()   # correct
```

**Detection**: Any endpoint function whose name matches an imported symbol.

## Bug Pattern 3: Hardcoded Timestamp in Probe Endpoints

**Symptom**: `/health/liveness` returns a static date from years ago.

**Fix**:
```python
# Wrong:
return {"alive": True, "timestamp": "2025-01-20T00:00:00Z"}

# Right:
from datetime import UTC, datetime
return {"alive": True, "timestamp": datetime.now(UTC).isoformat()}
```

## Bug Pattern 4: Duplicate Pydantic Model Names Across Routers

**Symptom**: `test_schema_models_present` fails because FastAPI renames one model (e.g., `CacheMetricsResponse` → `CacheMetricsResponse1`).

**Root cause**: Two `APIRouter`s both define a `class CacheMetricsResponse(BaseModel)`. FastAPI deduplicates by appending a suffix.

**Fix**: Use distinct model names per router module:
```python
# performance.py — specifically about hit rates
class CacheHitRateResponse(BaseModel): ...

# cache_dashboard.py — full cache telemetry  
class CacheMetricsResponse(BaseModel): ...
```

**Detection**:
```bash
grep -rn "^class.*BaseModel" tool_router/api/ | awk -F: '{print $3}' | sort | uniq -d
```

## Bug Pattern 5: Deprecated `Query(regex=)` → `Query(pattern=)`

**Symptom**: FastAPI emits `FastAPIDeprecationWarning: 'regex' has been deprecated, please use 'pattern' instead` during tests and at runtime. Treated as error in strict warning mode.

**Root cause**: FastAPI `>=0.109` renamed the `regex` parameter of `Query()`, `Path()`, `Header()`, `Cookie()` to `pattern`.

**Detection**:
```bash
grep -rn "Query(.*regex=\|Path(.*regex=\|Header(.*regex=\|Cookie(.*regex=" tool_router/
```

**Fix**:
```python
# Wrong (FastAPI < 0.109 style):
format: str = Query(default="json", regex="^(json|csv)$")

# Right:
format: str = Query(default="json", pattern="^(json|csv)$")
```

## Bug Pattern 6: Unclosed SQLite Connections in Long-Lived Objects

**Symptom**: `ResourceWarning: unclosed database in <sqlite3.Connection object>` in pytest output. Connections accumulate per test run; production server leaks file handles.

**Root cause**: Class stores `self.conn = sqlite3.connect(...)` but has no `close()`, `__del__`, or context manager support.

**Fix**: Add lifecycle methods to any class holding a persistent `sqlite3.Connection`:
```python
class MyTool:
    def __init__(self) -> None:
        self.conn: sqlite3.Connection | None = None
        self._init_database()

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "MyTool":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
```

**Detection**:
```bash
# Find classes with self.conn = sqlite3.connect(...) but no close()
grep -rn "self\.conn = sqlite3\.connect" tool_router/ --include="*.py" -l | \
  xargs grep -L "def close"
```

## How to Audit for All Six Bugs

```bash
# 1. Unregistered routers
diff \
  <(grep "include_router" tool_router/http_server.py | grep -oP "(?<=router\().*?(?=\))" | sort) \
  <(ls tool_router/api/*.py | xargs grep -l "router = APIRouter" | sed 's|.*/||;s|\.py||' | sort)

# 2. Shadowed imports (same name as endpoint function)
grep -n "from.*import\|^async def\|^def " tool_router/api/performance.py | \
  awk '/import/{gsub(/.*import /,""); n=$0} /^async def|^def/{if($2 in used) print "SHADOW: "$2}'

# 3. Hardcoded timestamps
grep -rn "2025-01-\|2024-" tool_router/api/

# 4. Duplicate model names
grep -rn "^class.*BaseModel" tool_router/api/ | sed 's/.*class \([A-Z][^(]*\).*/\1/' | sort | uniq -d

# 5. Deprecated Query(regex=)
grep -rn "Query(.*regex=\|Path(.*regex=\|Header(.*regex=" tool_router/

# 6. Unclosed SQLite connections
grep -rn "self\.conn = sqlite3\.connect" tool_router/ --include="*.py" -l | \
  xargs grep -L "def close"
```

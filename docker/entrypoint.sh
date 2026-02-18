#!/bin/bash

# Custom entrypoint that handles Alembic migration issues
echo "🚀 Starting MCP Gateway with custom entrypoint..."

# Check if we should skip migrations
if [ "$SKIP_MIGRATIONS" = "true" ]; then
    echo "⏭️  Skipping Alembic migrations due to SKIP_MIGRATIONS=true"
    echo "� Starting minimal gateway to bypass migration issues..."

    # Start the minimal gateway instead
    exec python3 /app/docker/minimal_gateway.py
else
    echo "🔄 Running Alembic migrations..."
    python3 -c "
import asyncio
from mcpgateway.bootstrap_db import main
try:
    asyncio.run(main())
    print('✅ Migrations completed successfully')
except Exception as e:
    print(f'❌ Migration failed: {e}')
    print('⚠️  Continuing with limited functionality...')
"

    echo "🌟 Starting Gateway server..."
    # Start the original application
    exec gunicorn -c gunicorn.config.py --worker-class uvicorn.workers.UvicornWorker --workers 16 --timeout 600 --max-requests 100000 --max-requests-jitter 100 --access-logfile /dev/null --error-logfile - --forwarded-allow-ips=* --pid /tmp/mcpgateway-gunicorn.lock --preload mcpgateway.main:app
fi

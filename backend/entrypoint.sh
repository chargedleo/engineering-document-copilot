#!/bin/sh
set -e

# ==============================================================================
# Engineering Copilot Backend Container Entrypoint
# Handles database connectivity verification and Alembic schema migrations
# ==============================================================================

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "=========================================================="
    echo "Verifying database connectivity and applying migrations..."
    echo "=========================================================="

    python - <<'EOF'
import asyncio
import os
import sys
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def wait_for_db():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL not set; skipping connectivity check.")
        return

    max_retries = int(os.getenv("DB_CONNECT_RETRIES", "30"))
    retry_delay = int(os.getenv("DB_CONNECT_DELAY_SECONDS", "2"))

    print(f"Checking database connectivity (retries={max_retries}, delay={retry_delay}s)...")
    for attempt in range(1, max_retries + 1):
        try:
            engine = create_async_engine(url, pool_pre_ping=True)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            print("Database is reachable and ready.")
            return
        except Exception as exc:
            print(f"Waiting for database (attempt {attempt}/{max_retries}): {exc}")
            time.sleep(retry_delay)

    print("ERROR: Database connection timed out.", file=sys.stderr)
    sys.exit(1)

asyncio.run(wait_for_db())
EOF

    echo "Running Alembic migrations (alembic upgrade head)..."
    alembic upgrade head
    echo "Alembic migrations completed successfully."
else
    echo "RUN_MIGRATIONS is set to false; skipping startup migrations."
fi

echo "Starting backend process: $@"
exec "$@"

#!/usr/bin/env bash
set -e

if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Applying database migrations..."
  alembic upgrade head
else
  echo "⏭Skipping database migrations (RUN_MIGRATIONS=$RUN_MIGRATIONS)"
fi

echo "Starting backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
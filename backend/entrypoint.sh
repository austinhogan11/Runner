#!/usr/bin/env sh
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "🔧 Applying database migrations..."
  alembic upgrade head
fi

echo "🚀 Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
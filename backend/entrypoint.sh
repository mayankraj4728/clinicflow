#!/usr/bin/env sh
# Wait for PostgreSQL, apply migrations, then start the API server.
set -e

echo "Applying database migrations..."
for i in $(seq 1 30); do
  if alembic upgrade head; then
    echo "Migrations applied."
    break
  fi
  echo "Database not ready yet (attempt $i/30) - retrying in 2s..."
  sleep 2
done

echo "Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

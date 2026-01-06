#!/bin/bash
# Production startup script
# Reads PORT from environment (Render sets this automatically)
# Falls back to 8000 if not set

PORT=${PORT:-8000}

echo "Starting server on port $PORT"

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1 \
    --access-log \
    --log-level info


#!/bin/bash
# Production startup script
# Reads PORT from environment (Render sets this automatically)
# Falls back to 8000 if not set

set -e  # Exit on error

PORT=${PORT:-8000}

echo "=========================================="
echo "Starting FairPath API Server"
echo "Port: $PORT"
echo "Host: 0.0.0.0"
echo "=========================================="

# Ensure we're binding to all interfaces and the correct port
# Use --timeout-keep-alive to ensure connections stay open
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1 \
    --access-log \
    --log-level info \
    --timeout-keep-alive 5


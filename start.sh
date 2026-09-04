#!/bin/sh
set -e

PORT="${PORT:-10000}"
HOST="${HOST:-0.0.0.0}"

echo "Starting BioForge FastAPI Backend on ${HOST}:${PORT}..."
exec uvicorn backend.app.main:app --host "$HOST" --port "$PORT"

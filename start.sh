#!/bin/bash

# Startup script for Render deployment
# Forces uvicorn to ensure FastAPI compatibility

echo "🚀 Starting Job Alert Bot with uvicorn..."

# Set environment variables if not already set
export PYTHONPATH="${PYTHONPATH}:/opt/render/project/src"

# Start uvicorn with proper configuration
exec uvicorn asgi:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info
#!/bin/bash
# Launch script for Nexus_3 API using uv

# Set up environment
export PYTHONUNBUFFERED=1
export PYTHONPATH="/Users/bard/Code/nexus_3/src"

# Change to project directory
cd /Users/bard/Code/nexus_3

# Ensure logs directory exists
mkdir -p logs

# Log startup
echo "$(date): Starting Nexus_3 API on port 8100" >> logs/nexus.log

# Start the API server using uv
exec uv run uvicorn nexus.app:app \
    --host 0.0.0.0 \
    --port 8100 \
    --no-access-log \
    --log-level info

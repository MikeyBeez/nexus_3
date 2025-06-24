#!/bin/bash
# Nexus MCP Server launcher script (debug version)

# Enable debug output
set -x

# Log startup
echo "Starting Nexus MCP server..." >&2
echo "NEXUS_API_URL: ${NEXUS_API_URL:-http://localhost:8100}" >&2

# Set up environment
export NEXUS_API_URL="${NEXUS_API_URL:-http://localhost:8100}"

# Change to MCP server directory
cd /Users/bard/Code/nexus_3/mcp_server

# Check if the built file exists
if [ ! -f "dist/index.js" ]; then
    echo "Error: dist/index.js not found. Run 'npm run build' first." >&2
    exit 1
fi

# Check if node is available
if ! command -v node &> /dev/null; then
    echo "Error: node not found in PATH" >&2
    exit 1
fi

# Run the MCP server with debug output
exec node dist/index.js

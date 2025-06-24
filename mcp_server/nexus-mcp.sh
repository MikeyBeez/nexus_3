#!/bin/bash

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set up environment
export NEXUS_API_URL="${NEXUS_API_URL:-http://localhost:8100}"

# Run the MCP server with node
exec node "$DIR/dist/index.js"

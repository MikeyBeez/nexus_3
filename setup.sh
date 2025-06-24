#!/bin/bash
# Setup script for Nexus_3

echo "🚀 Setting up Nexus_3..."
echo "======================="

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p tmp

# Install Python dependencies
echo -e "\nInstalling Python dependencies..."
if command -v uv &> /dev/null; then
    uv venv
    uv sync
else
    echo "Warning: uv not found, using pip"
    python -m venv .venv
    source .venv/bin/activate
    pip install -e .
fi

# Set up MCP server
echo -e "\nSetting up MCP server..."
cd mcp_server
npm install
npm run build
cd ..

# Make scripts executable
echo -e "\nMaking scripts executable..."
chmod +x launch_api.sh
chmod +x manage_service.sh

echo -e "\n✅ Setup complete!"
echo ""
echo "To start Nexus_3:"
echo "  As a service: ./manage_service.sh install"
echo "  For development: make dev"
echo ""
echo "API will be available at: http://localhost:8100"

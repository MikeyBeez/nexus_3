# Nexus_3 Dual Service Architecture

## Overview

Nexus_3 runs as BOTH:
1. **REST API** on port 8100 (for direct HTTP access)
2. **MCP Server** (for Claude integration)

Both services work together to provide orchestration capabilities.

## Service Architecture

```
Nexus_3 Service
├── API Component (Port 8100)
│   ├── FastAPI server
│   ├── Task management
│   ├── Orchestration endpoints
│   └── Service health checks
│
└── MCP Component (stdio)
    ├── Claude integration
    ├── Tool definitions
    ├── Calls API internally
    └── Natural language interface
```

## How They Work Together

1. **MCP Server** receives commands from Claude
2. **MCP Server** makes HTTP calls to the **API Server**
3. **API Server** executes the actual orchestration
4. Results flow back through MCP to Claude

## Starting Both Services

### Option 1: As a System Service (Recommended)
```bash
cd /Users/bard/Code/nexus_3
make service-install  # Installs launchctl service
make service-start    # Starts API server

# Install MCP server in Claude
make install-mcp
# Then add to Claude Desktop
```

### Option 2: Development Mode
```bash
# Terminal 1: Start API
cd /Users/bard/Code/nexus_3
make dev

# Terminal 2: Test MCP server
cd /Users/bard/Code/nexus_3/mcp_server
npm run dev
```

## Service Management

### Check All Services
```bash
# Run the check script
chmod +x check_services.sh
./check_services.sh

# Or manually check
launchctl list | grep -E "(nexus|cortex)"
```

### Stop Old Nexus Services
```bash
# DO NOT stop com.apple.nexusd - it's an Apple system service!

# Stop old Nexus_2 if running
launchctl stop com.mikeybee.nexus2
launchctl unload ~/Library/LaunchAgents/com.mikeybee.nexus2.plist
```

### Ensure Both Components Running
```bash
# Check API
curl http://localhost:8100/health

# Check MCP (through Claude)
# Use nexus tools in Claude
```

## Port Configuration

- **8000**: Cortex_2 API (Knowledge/Memory)
- **8100**: Nexus_3 API (Orchestration)
- **stdio**: MCP servers (both Cortex and Nexus)

## Important Notes

1. The API server MUST be running for MCP to work
2. MCP server is stateless - it just forwards to API
3. Both use the same task/orchestration system
4. Logs are in `/Users/bard/Code/nexus_3/logs/`

## Troubleshooting

If MCP tools don't work in Claude:
1. Check API is running: `curl http://localhost:8100/health`
2. Check logs: `tail -f /Users/bard/Code/nexus_3/logs/nexus-error.log`
3. Reinstall MCP: `make install-mcp`
4. Check environment: `echo $NEXUS_API_URL` (should be http://localhost:8100)

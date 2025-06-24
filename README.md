# Nexus_3: AI Orchestration System

A streamlined orchestration system that coordinates between AI services, combining REST API and MCP (Model Context Protocol) server capabilities.

## 🎯 Core Purpose

Nexus_3 is a minimal, working implementation that:
- Provides REST API endpoints for orchestration
- Serves as an MCP server for Claude integration
- Manages task execution and coordination
- Integrates with Cortex_2 for memory/knowledge services

## 🚀 Quick Start

```bash
# Install dependencies
./setup.sh

# Start as a service
make service-install
make service-start

# Or run directly for development
make dev
```

## 📡 Access Points

- **REST API**: http://localhost:8100
- **API Docs**: http://localhost:8100/docs
- **MCP Server**: Available to Claude via MCP protocol

## 🏗️ Architecture

```
Nexus_3 (Orchestrator)
    ├── REST API (FastAPI)
    ├── MCP Server (TypeScript)
    └── Integrations
        └── Cortex_2 API (Knowledge/Memory)
```

## 🔧 Key Features

- **Task Management**: Create, execute, and monitor tasks
- **Service Coordination**: Route requests to appropriate services
- **Memory Integration**: Uses Cortex_2 for knowledge storage
- **Dual Protocol**: Both HTTP REST and MCP interfaces

## 📚 Documentation

See `/docs` for detailed documentation.

---
*Nexus_3: Simplified orchestration that actually works.*

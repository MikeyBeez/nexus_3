# CLAUDE_PLEASE_READ_ME.txt - Nexus_3 Project

CRITICAL: READ THIS FIRST WHEN CONTINUING NEXUS_3 DEVELOPMENT

## PROJECT STATUS (as of chat ending)

Nexus_3 is a ground-up rewrite of Nexus_2, designed to be:
1. **Modular** like Cortex_2 - hot-swappable orchestration modules
2. **Working** - fixes the broken graph operations from Nexus_2
3. **Dual Protocol** - BOTH REST API (port 8100) AND MCP server (stdio) running together
4. **Service-based** - launchctl integration from the start

## CURRENT STATE

✅ **Completed**:
- Basic project structure created
- FastAPI server with core endpoints
- MCP server for Claude integration
- Service management (launchctl)
- Cortex_2 integration client
- Task management system
- Basic orchestration framework

❌ **TODO - CRITICAL FOR NEXT CHAT**:
1. **Module System** (like Cortex_2):
   - Create `modules/` directory structure
   - Module manifest format (YAML)
   - Dynamic module loading/unloading
   - Module types: orchestrators, analyzers, executors, integrations
   
2. **Orchestration Modules**:
   - Base orchestrator class
   - Goal decomposition module
   - Service routing module
   - Result aggregation module
   
3. **Fix from Nexus_2**:
   - The graph operations were broken
   - Complex chains would fail
   - Needed better error handling
   - State management was problematic

## ARCHITECTURE VISION

```
Nexus_3 (Orchestration OS)
├── Core Engine
│   ├── Module Loader (like Cortex_2)
│   ├── Task Manager
│   ├── Service Router
│   └── State Manager
├── Modules/
│   ├── orchestrators/
│   │   ├── linear_orchestrator/
│   │   ├── parallel_orchestrator/
│   │   └── adaptive_orchestrator/
│   ├── analyzers/
│   │   ├── goal_analyzer/
│   │   └── context_analyzer/
│   ├── executors/
│   │   ├── code_executor/
│   │   └── command_executor/
│   └── integrations/
│       ├── cortex_integration/
│       └── external_apis/
├── REST API (FastAPI)
├── MCP Server (TypeScript)
└── Storage/
    ├── task_store/
    └── module_cache/
```

## MODULE SYSTEM DESIGN (TO IMPLEMENT)

Each module should have:

```yaml
# modules/orchestrators/linear_orchestrator/manifest.yaml
id: linear_orchestrator
version: 1.0.0
type: orchestrator
name: Linear Task Orchestrator
description: Executes tasks in sequential order

metadata:
  author: MikeyBee
  tags: [orchestration, sequential, basic]
  
capabilities:
  - sequential_execution
  - error_handling
  - result_chaining

dependencies:
  - task_manager
  - service_router

config:
  max_retries: 3
  timeout_seconds: 300
  
entry_point: orchestrator.py
```

## KEY DIFFERENCES FROM NEXUS_2

1. **Modular Architecture**: Everything is a loadable module
2. **Simpler State**: No complex graph, just task chains
3. **Better Error Handling**: Each module handles its own errors
4. **Service Patterns**: Clear patterns for service integration
5. **Dual Protocol**: Both REST and MCP from the start

## FILE LOCATIONS

- **Main code**: `/Users/bard/Code/nexus_3/src/nexus/`
- **Modules**: `/Users/bard/Code/nexus_3/modules/` (TO CREATE)
- **MCP Server**: `/Users/bard/Code/nexus_3/mcp_server/`
- **Tests**: `/Users/bard/Code/nexus_3/tests/` (TO CREATE)
- **Temp files**: `/Users/bard/Code/nexus_3/tmp/`

## INTEGRATION POINTS

1. **Cortex_2** (port 8000):
   - Knowledge graph queries
   - Context analysis
   - Memory management
   
2. **Future Services**:
   - Code execution service
   - External API gateway
   - Monitoring service

## COMMANDS TO REMEMBER

```bash
# IMPORTANT: Disable old nexus services first!
cd /Users/bard/Code/nexus_3
./check_services.sh  # This will show what needs to be stopped

# Start Nexus_3 (runs BOTH API and enables MCP)
cd /Users/bard/Code/nexus_3
make service-start    # Starts API as service
make install-mcp     # Build MCP server
# Then add MCP to Claude Desktop

# For development
make dev             # Starts API only

# Check both services
make check-services  # Shows Cortex_2 and Nexus_3 status

# Install MCP
make install-mcp
# Then add to Claude

# Test API
python test_api.py
```

## NEXT CHAT PRIORITIES

1. **Implement Module System**:
   ```python
   # src/nexus/modules/base.py
   class BaseModule(ABC):
       def __init__(self, manifest: dict):
           self.id = manifest['id']
           self.version = manifest['version']
           
       @abstractmethod
       async def execute(self, context: dict) -> dict:
           pass
   ```

2. **Create Module Loader**:
   ```python
   # src/nexus/modules/loader.py
   class ModuleLoader:
       def load_module(self, module_id: str) -> BaseModule:
           # Load from modules/ directory
           pass
   ```

3. **Implement Orchestration Modules**:
   - Linear orchestrator (simple sequential)
   - Parallel orchestrator (concurrent tasks)
   - Adaptive orchestrator (changes based on results)

4. **Fix State Management**:
   - Use simple task chains instead of complex graphs
   - Store state in SQLite or Redis
   - Clear error propagation

## IMPORTANT CONTEXT

- **MikeyBee** prefers Python, modular design, no placeholders
- **Cortex_2** is the memory/knowledge system (working well)
- **Nexus_3** is the orchestration/execution system (being built)
- Both use launchctl for service management
- Both have MCP servers for Claude integration

## GITHUB SETUP (When Ready)

```bash
git init
git add .
git commit -m "Initial commit: Nexus_3 - Modular Orchestration System"
git remote add origin git@github.com:MikeyBeez/nexus_3.git
git branch -M main
git push -u origin main
```

## SUCCESS METRICS

- Modules can be hot-swapped without restart
- Tasks complete reliably (unlike Nexus_2)
- Clear error messages and recovery
- Can orchestrate complex multi-step operations
- Integrates seamlessly with Cortex_2

Remember: This is a WORKING system that prioritizes reliability over complexity!

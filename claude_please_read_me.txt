# CLAUDE_PLEASE_READ_ME.txt - Nexus_3 Project

CRITICAL: READ THIS FIRST WHEN CONTINUING NEXUS_3 DEVELOPMENT

## PROJECT STATUS (Updated)

Nexus_3 is a ground-up rewrite of Nexus_2, designed to be:
1. **Modular** like Cortex_2 - hot-swappable orchestration modules ✅
2. **Working** - fixes the broken graph operations from Nexus_2 ✅
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
- **Module system implementation**
- **Module loader with hot-swapping**
- **Execution queue from Nexus_2**
- **Command executor module**
- **Module management API endpoints**
- **Priority-based task queues**
- **Multi-worker execution**
- **GitHub repository created**

⚡ **Working Features**:
1. Submit tasks via REST API
2. Tasks execute through modular executors
3. Command execution with output capture
4. Real-time queue statistics
5. Module loading/unloading without restart
6. Priority queues (urgent/normal/batch)

❌ **TODO - Next Priorities**:
1. **More Executor Modules**:
   - Python executor (execute Python scripts)
   - SSH executor (remote commands)
   - API executor (HTTP requests)
   
2. **Orchestration Modules**:
   - Linear orchestrator (sequential workflow)
   - Parallel orchestrator (concurrent tasks)
   - Conditional orchestrator (if/then logic)
   
3. **Analyzer Modules**:
   - Goal analyzer (break down complex goals)
   - Dependency analyzer (task dependencies)

## ARCHITECTURE (IMPLEMENTED)

```
Nexus_3 (Orchestration OS)
├── Core Engine ✅
│   ├── Module Loader ✅
│   ├── Task Manager ✅
│   ├── Execution Queue ✅
│   └── Service Router ✅
├── Modules/
│   └── executors/
│       └── command_executor/ ✅
├── REST API (FastAPI) ✅
├── MCP Server (TypeScript)
└── Storage/
    └── In-memory for now ✅
```

## MODULE SYSTEM (IMPLEMENTED)

Each module has:

```yaml
# modules/executors/command_executor/manifest.yaml
id: command_executor
version: 1.0.0
type: executor
name: Command Executor
description: Executes system commands and shell scripts

metadata:
  author: MikeyBee
  tags: [executor, command, shell, subprocess]
  
capabilities:
  - command_execution
  - shell_scripts
  - timeout_handling
  - output_capture

config:
  max_retries: 3
  default_timeout_seconds: 300
  
entry_point: module.py
```

## KEY IMPROVEMENTS FROM NEXUS_2

1. **Modular Architecture**: Everything is a loadable module ✅
2. **Simpler State**: Task-based instead of complex graphs ✅
3. **Better Error Handling**: Each module handles its own errors ✅
4. **Hot-Swapping**: Modules can be loaded/unloaded at runtime ✅
5. **Priority Queues**: Urgent tasks execute first ✅

## API ENDPOINTS

```bash
# Task Management
POST   /tasks              # Create task
GET    /tasks              # List tasks
GET    /tasks/{id}         # Get task details
DELETE /tasks/{id}         # Cancel task

# Module Management (NEW)
GET    /modules            # List modules
POST   /modules/{id}/load  # Load module
POST   /modules/{id}/unload # Unload module
GET    /modules/{id}/status # Module status

# Queue Statistics (NEW)
GET    /queue/stats        # Real-time statistics

# Health & Status
GET    /health             # System health
GET    /services           # Service status
```

## TESTING

```bash
# Test execution queue
cd /Users/bard/Code/nexus_3
python tmp/test_execution_queue.py

# Submit a task via curl
curl -X POST http://localhost:8100/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "generation",
    "description": "List files",
    "parameters": {
      "command": "ls",
      "args": ["-la"],
      "capture_output": true
    }
  }'

# Check queue stats
curl http://localhost:8100/queue/stats
```

## COMMANDS TO REMEMBER

```bash
# Start services
cd /Users/bard/Code/nexus_3
make service-start    # Starts API as service
make check-services   # Check both Cortex_2 and Nexus_3

# Development
make dev              # Run in development mode
make test             # Run tests

# Module operations
curl -X GET http://localhost:8100/modules
curl -X POST http://localhost:8100/modules/command_executor/load
```

## CREATING NEW MODULES

1. **Create module directory**:
   ```bash
   mkdir -p modules/executors/my_executor
   ```

2. **Create manifest.yaml**:
   ```yaml
   id: my_executor
   version: 1.0.0
   type: executor
   name: My Executor
   description: Does something cool
   entry_point: module.py
   ```

3. **Create module.py**:
   ```python
   from nexus.modules.base import ExecutorModule
   
   class Module(ExecutorModule):
       async def initialize(self) -> bool:
           return True
       
       async def can_execute(self, task: Dict[str, Any]) -> bool:
           # Check if this executor can handle the task
           return True
       
       async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
           # Execute the task
           return {"status": "success", "result": "done"}
   ```

4. **Load the module**:
   ```bash
   curl -X POST http://localhost:8100/modules/my_executor/load
   ```

## INTEGRATION WITH CORTEX_2

- Cortex_2 runs on port 8000 (knowledge/memory)
- Nexus_3 runs on port 8100 (orchestration/execution)
- Both use launchctl for service management
- Both have MCP servers for Claude integration

## SUCCESS METRICS

- ✅ Modules can be hot-swapped without restart
- ✅ Tasks execute reliably (unlike Nexus_2)
- ✅ Clear error messages and recovery
- ✅ Can execute system commands
- ⏳ Can orchestrate complex multi-step operations
- ✅ Integrates with Cortex_2

Remember: This is a WORKING system that prioritizes reliability over complexity!

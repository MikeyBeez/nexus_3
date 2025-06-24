# Nexus_3 Architecture & Module System Design

## Overview

Nexus_3 is designed as a modular orchestration system, similar to how Cortex_2 handles cognitive modules. Each orchestration capability is packaged as a hot-swappable module.

## Module Types

### 1. Orchestrators
Control the flow of task execution:
- **Linear**: Sequential task execution
- **Parallel**: Concurrent task execution  
- **Adaptive**: Dynamic flow based on results
- **Conditional**: Branching logic
- **Loop**: Iterative execution

### 2. Analyzers
Break down complex goals:
- **Goal Analyzer**: Decomposes goals into tasks
- **Context Analyzer**: Understands current state
- **Dependency Analyzer**: Finds task dependencies
- **Resource Analyzer**: Estimates requirements

### 3. Executors
Perform actual work:
- **Code Executor**: Runs Python/JS code
- **Command Executor**: System commands
- **API Executor**: External API calls
- **Query Executor**: Database/GraphQL

### 4. Integrations
Connect to external services:
- **Cortex Integration**: Memory/knowledge
- **GitHub Integration**: Code operations
- **OpenAI Integration**: LLM calls
- **Database Integration**: Data operations

## Module Structure

```
modules/
├── orchestrators/
│   ├── linear_orchestrator/
│   │   ├── manifest.yaml
│   │   ├── orchestrator.py
│   │   ├── config.yaml
│   │   └── README.md
│   └── parallel_orchestrator/
│       ├── manifest.yaml
│       ├── orchestrator.py
│       └── workers.py
├── analyzers/
│   └── goal_analyzer/
│       ├── manifest.yaml
│       ├── analyzer.py
│       └── patterns.json
├── executors/
│   └── code_executor/
│       ├── manifest.yaml
│       ├── executor.py
│       └── sandbox.py
└── integrations/
    └── cortex_integration/
        ├── manifest.yaml
        └── client.py
```

## Module Manifest Format

```yaml
# Module identification
id: unique_module_id
version: 1.0.0
type: orchestrator|analyzer|executor|integration
name: Human Readable Name
description: What this module does

# Module metadata
metadata:
  author: MikeyBee
  created: 2024-01-15
  tags: [orchestration, async, advanced]
  category: core|experimental|community

# Dependencies
dependencies:
  modules:
    - task_manager: ">=1.0.0"
    - service_router: "~1.0.0"
  python:
    - httpx: ">=0.24.0"
    - pydantic: ">=2.0.0"

# Capabilities (what this module can do)
capabilities:
  - parallel_execution
  - error_recovery
  - state_persistence
  - streaming_results

# Requirements
requirements:
  memory_mb: 100
  cpu_cores: 1
  gpu: false

# Configuration schema
config_schema:
  type: object
  properties:
    max_workers:
      type: integer
      default: 5
    timeout_seconds:
      type: integer
      default: 300
    retry_policy:
      type: object
      properties:
        max_retries:
          type: integer
          default: 3
        backoff_seconds:
          type: number
          default: 1.0

# Entry points
entry_points:
  main: orchestrator.py
  setup: setup.py
  teardown: cleanup.py

# Module behavior
behavior:
  auto_load: false
  singleton: true
  priority: normal
  cache_results: true
```

## Base Module Classes

```python
# src/nexus/modules/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class ModuleContext(BaseModel):
    """Context passed to modules"""
    task_id: str
    input_data: Dict[str, Any]
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    parent_context: Optional[Dict[str, Any]] = None

class ModuleResult(BaseModel):
    """Result returned by modules"""
    success: bool
    output_data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    next_module: Optional[str] = None

class BaseModule(ABC):
    """Base class for all modules"""
    
    def __init__(self, manifest: Dict[str, Any], config: Dict[str, Any]):
        self.id = manifest['id']
        self.version = manifest['version']
        self.type = manifest['type']
        self.config = config
        self.manifest = manifest
        
    @abstractmethod
    async def setup(self) -> None:
        """Initialize module resources"""
        pass
        
    @abstractmethod
    async def execute(self, context: ModuleContext) -> ModuleResult:
        """Execute module logic"""
        pass
        
    @abstractmethod
    async def teardown(self) -> None:
        """Clean up module resources"""
        pass
        
    def validate_config(self) -> bool:
        """Validate configuration against schema"""
        # Use jsonschema to validate
        return True

class OrchestratorModule(BaseModule):
    """Base for orchestrator modules"""
    
    async def decompose_goal(self, goal: str) -> List[Dict[str, Any]]:
        """Break down goal into tasks"""
        pass
        
    async def route_task(self, task: Dict[str, Any]) -> str:
        """Determine which service handles task"""
        pass

class AnalyzerModule(BaseModule):
    """Base for analyzer modules"""
    
    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis"""
        pass

class ExecutorModule(BaseModule):
    """Base for executor modules"""
    
    async def can_execute(self, task_type: str) -> bool:
        """Check if this executor can handle the task"""
        pass
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the specific task"""
        pass

class IntegrationModule(BaseModule):
    """Base for integration modules"""
    
    async def connect(self) -> bool:
        """Establish connection to service"""
        pass
        
    async def disconnect(self) -> None:
        """Close connection to service"""
        pass
```

## Module Loader Implementation

```python
# src/nexus/modules/loader.py
import yaml
import importlib.util
from pathlib import Path
from typing import Dict, Optional

class ModuleLoader:
    """Loads and manages modules"""
    
    def __init__(self, modules_path: Path):
        self.modules_path = modules_path
        self.loaded_modules: Dict[str, BaseModule] = {}
        self.manifests: Dict[str, dict] = {}
        
    async def discover_modules(self) -> Dict[str, dict]:
        """Discover all available modules"""
        modules = {}
        
        for module_type in ['orchestrators', 'analyzers', 'executors', 'integrations']:
            type_path = self.modules_path / module_type
            if not type_path.exists():
                continue
                
            for module_dir in type_path.iterdir():
                if module_dir.is_dir():
                    manifest_path = module_dir / 'manifest.yaml'
                    if manifest_path.exists():
                        with open(manifest_path) as f:
                            manifest = yaml.safe_load(f)
                            modules[manifest['id']] = manifest
                            
        return modules
        
    async def load_module(self, module_id: str) -> BaseModule:
        """Load a specific module"""
        if module_id in self.loaded_modules:
            return self.loaded_modules[module_id]
            
        manifest = self.manifests.get(module_id)
        if not manifest:
            raise ValueError(f"Module {module_id} not found")
            
        # Load module code
        module_path = self._get_module_path(manifest)
        spec = importlib.util.spec_from_file_location(
            f"nexus_modules.{module_id}",
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Instantiate module class
        module_class = getattr(module, 'Module')
        instance = module_class(manifest, self._load_config(manifest))
        
        # Setup module
        await instance.setup()
        
        self.loaded_modules[module_id] = instance
        return instance
```

## Module Examples

### Linear Orchestrator Module

```python
# modules/orchestrators/linear_orchestrator/orchestrator.py
from nexus.modules.base import OrchestratorModule, ModuleContext, ModuleResult

class Module(OrchestratorModule):
    """Executes tasks in sequential order"""
    
    async def setup(self) -> None:
        """Initialize orchestrator"""
        self.task_queue = []
        
    async def execute(self, context: ModuleContext) -> ModuleResult:
        """Execute tasks sequentially"""
        goal = context.input_data.get('goal')
        
        # Decompose goal into tasks
        tasks = await self.decompose_goal(goal)
        
        results = []
        for task in tasks:
            # Execute each task
            result = await self._execute_task(task)
            results.append(result)
            
            # Stop on failure if configured
            if not result['success'] and self.config.get('stop_on_failure', True):
                return ModuleResult(
                    success=False,
                    output_data={'results': results},
                    error=f"Task failed: {task['id']}"
                )
                
        return ModuleResult(
            success=True,
            output_data={'results': results}
        )
        
    async def teardown(self) -> None:
        """Clean up resources"""
        self.task_queue.clear()
```

## Next Steps for Implementation

1. Create the module directory structure
2. Implement base module classes
3. Create module loader with hot-swap capability
4. Build core modules (linear, parallel orchestrators)
5. Add module discovery API endpoints
6. Create module marketplace/registry concept
7. Implement module dependency resolution
8. Add module versioning and updates
9. Create module development tools
10. Build module testing framework

This modular approach will make Nexus_3 highly extensible and maintainable!

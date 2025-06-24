"""Nexus_3 FastAPI Application"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import asyncio
from typing import Dict, List, Optional
import uuid
import os

from .config import settings
from .models import (
    TaskInfo, TaskStatus, TaskCreateRequest, TaskCreateResponse,
    TaskUpdateRequest, SystemStatus, ServiceStatus, ServiceType,
    OrchestrationRequest, OrchestrationResponse, TaskType
)
from .services.cortex_client import CortexClient
from .services.task_manager import TaskManager
from .services.execution_queue import ExecutionQueue, Priority
from .modules.base import ModuleLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
task_manager = TaskManager()
cortex_client = CortexClient(settings.cortex_api_url)
module_loader = ModuleLoader(os.path.join(os.path.dirname(__file__), '..', '..', 'modules'))
execution_queue = ExecutionQueue(module_loader, num_workers=3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Nexus_3...")
    app.state.start_time = datetime.now()
    
    # Start execution queue
    await execution_queue.start()
    
    # Start background services
    asyncio.create_task(task_manager.process_tasks())
    
    yield
    
    # Cleanup
    logger.info("Shutting down Nexus_3...")
    await execution_queue.stop()
    await task_manager.shutdown()

# Create FastAPI app
app = FastAPI(
    title="Nexus_3 API",
    description="AI Orchestration System - Modular and Hot-swappable",
    version=settings.version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Nexus_3",
        "version": settings.version,
        "description": "AI Orchestration System with Modular Execution",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "tasks": "/tasks",
            "orchestrate": "/orchestrate",
            "services": "/services",
            "modules": "/modules",
            "queue": "/queue"
        }
    }

# Health check
@app.get("/health", response_model=SystemStatus)
async def health_check():
    """System health check"""
    uptime = (datetime.now() - app.state.start_time).total_seconds()
    
    # Check Cortex service
    cortex_healthy = await cortex_client.health_check()
    
    # Get task statistics
    task_stats = task_manager.get_statistics()
    
    # Get queue statistics
    queue_stats = execution_queue.get_statistics()
    
    services = [
        ServiceStatus(
            name="cortex",
            type=ServiceType.CORTEX,
            status="operational" if cortex_healthy else "degraded",
            healthy=cortex_healthy,
            last_check=datetime.now(),
            metadata={"url": settings.cortex_api_url}
        ),
        ServiceStatus(
            name="task_manager",
            type=ServiceType.LOCAL,
            status="operational",
            healthy=True,
            last_check=datetime.now(),
            metadata={"active_tasks": task_stats.get("running", 0)}
        ),
        ServiceStatus(
            name="execution_queue",
            type=ServiceType.LOCAL,
            status="operational",
            healthy=True,
            last_check=datetime.now(),
            metadata=queue_stats
        )
    ]
    
    return SystemStatus(
        status="healthy" if all(s.healthy for s in services) else "degraded",
        version=settings.version,
        uptime_seconds=uptime,
        tasks=task_stats,
        services=services,
        timestamp=datetime.now()
    )

# Task management endpoints
@app.post("/tasks", response_model=TaskCreateResponse)
async def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    """Create a new task"""
    task_id = str(uuid.uuid4())
    
    task = TaskInfo(
        id=task_id,
        type=request.type,
        status=TaskStatus.PENDING,
        description=request.description,
        parameters=request.parameters,
        priority=request.priority,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Convert task to dict for execution
    task_dict = task.to_dict()
    task_dict['command'] = request.parameters.get('command')
    task_dict['args'] = request.parameters.get('args', [])
    task_dict['timeout_seconds'] = request.parameters.get('timeout_seconds', 300)
    task_dict['working_directory'] = request.parameters.get('working_directory')
    task_dict['environment'] = request.parameters.get('environment', {})
    
    # Add to execution queue
    priority = Priority.NORMAL
    if request.priority > 7:
        priority = Priority.URGENT
    elif request.priority < 3:
        priority = Priority.BATCH
        
    execution_queue.submit_task(task, priority)
    
    # Also add to task manager for tracking
    await task_manager.add_task(task)
    
    return TaskCreateResponse(
        id=task_id,
        status="created",
        message=f"Task {task_id} created and queued for execution"
    )

@app.get("/tasks", response_model=List[TaskInfo])
async def list_tasks(status: Optional[TaskStatus] = None, limit: int = 100):
    """List tasks with optional status filter"""
    # Get tasks from execution queue (more up-to-date)
    tasks = execution_queue.list_tasks(status=status, limit=limit)
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskInfo)
async def get_task(task_id: str):
    """Get task details"""
    task = execution_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskInfo)
async def update_task(task_id: str, request: TaskUpdateRequest):
    """Update task status or result"""
    task = await task_manager.update_task(task_id, request)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a task"""
    success = execution_queue.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    return {"status": "cancelled", "task_id": task_id}

# Queue statistics endpoint
@app.get("/queue/stats")
async def get_queue_stats():
    """Get execution queue statistics"""
    return execution_queue.get_statistics()

# Module management endpoints
@app.get("/modules")
async def list_modules():
    """List available and loaded modules"""
    available = module_loader.list_available_modules()
    loaded = [m.get_status() for m in module_loader.get_loaded_modules().values()]
    
    return {
        "available": available,
        "loaded": loaded
    }

@app.post("/modules/{module_id}/load")
async def load_module(module_id: str):
    """Load a module"""
    module = module_loader.load_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    await module.initialize()
    await module.activate()
    
    return {
        "status": "loaded",
        "module": module.get_status()
    }

@app.post("/modules/{module_id}/unload")
async def unload_module(module_id: str):
    """Unload a module"""
    success = await module_loader.unload_module(module_id)
    if not success:
        raise HTTPException(status_code=404, detail="Module not found or not loaded")
    
    return {
        "status": "unloaded",
        "module_id": module_id
    }

@app.get("/modules/{module_id}/status")
async def get_module_status(module_id: str):
    """Get module status"""
    module = module_loader.get_loaded_modules().get(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not loaded")
    
    return module.get_status()

# Orchestration endpoint
@app.post("/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(request: OrchestrationRequest):
    """Orchestrate a complex task across services"""
    # Create orchestration task
    orch_id = str(uuid.uuid4())
    
    # Simple orchestration logic for now
    response = OrchestrationResponse(
        id=orch_id,
        goal=request.goal,
        status=TaskStatus.RUNNING,
        steps=[]
    )
    
    # Step 1: Analyze goal with Cortex
    step1 = {
        "step_number": 1,
        "action": "analyze_goal",
        "service": "cortex",
        "parameters": {"text": request.goal}
    }
    
    try:
        # This would call Cortex in a real implementation
        analysis = await cortex_client.analyze_context(request.goal)
        step1["result"] = analysis
        step1["status"] = TaskStatus.COMPLETED
    except Exception as e:
        step1["status"] = TaskStatus.FAILED
        step1["result"] = {"error": str(e)}
    
    response.steps.append(step1)
    
    # Step 2: Create execution task if needed
    if request.context.get("execute_command"):
        task_request = TaskCreateRequest(
            type=TaskType.GENERATION,
            description=f"Execute: {request.goal}",
            parameters={
                "command": request.context.get("command"),
                "args": request.context.get("args", [])
            },
            priority=5
        )
        
        task_response = await create_task(task_request, BackgroundTasks())
        
        step2 = {
            "step_number": 2,
            "action": "execute_command",
            "service": "execution_queue",
            "parameters": {"task_id": task_response.id},
            "status": TaskStatus.COMPLETED,
            "result": {"task_id": task_response.id}
        }
        response.steps.append(step2)
    
    response.status = TaskStatus.COMPLETED
    response.final_result = {"message": "Orchestration completed", "steps": len(response.steps)}
    
    return response

# Service status endpoint
@app.get("/services", response_model=List[ServiceStatus])
async def list_services():
    """List all integrated services and their status"""
    services = []
    
    # Check Cortex
    cortex_healthy = await cortex_client.health_check()
    services.append(
        ServiceStatus(
            name="cortex",
            type=ServiceType.CORTEX,
            status="operational" if cortex_healthy else "unreachable",
            healthy=cortex_healthy,
            last_check=datetime.now(),
            metadata={
                "url": settings.cortex_api_url,
                "purpose": "Knowledge and memory management"
            }
        )
    )
    
    # Add execution queue status
    queue_stats = execution_queue.get_statistics()
    services.append(
        ServiceStatus(
            name="execution_queue",
            type=ServiceType.LOCAL,
            status="operational",
            healthy=True,
            last_check=datetime.now(),
            metadata={
                "workers": queue_stats["workers"],
                "queues": queue_stats["queues"],
                "purpose": "Task execution with modular executors"
            }
        )
    )
    
    # Add loaded modules
    for module_id, module in module_loader.get_loaded_modules().items():
        services.append(
            ServiceStatus(
                name=f"module:{module_id}",
                type=ServiceType.MODULE,
                status="operational" if module.is_active else "inactive",
                healthy=module.is_active,
                last_check=datetime.now(),
                metadata=module.get_status()
            )
        )
    
    return services

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)

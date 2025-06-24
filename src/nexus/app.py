"""Nexus_3 FastAPI Application"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import asyncio
from typing import Dict, List, Optional
import uuid

from .config import settings
from .models import (
    TaskInfo, TaskStatus, TaskCreateRequest, TaskCreateResponse,
    TaskUpdateRequest, SystemStatus, ServiceStatus, ServiceType,
    OrchestrationRequest, OrchestrationResponse
)
from .services.cortex_client import CortexClient
from .services.task_manager import TaskManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
task_manager = TaskManager()
cortex_client = CortexClient(settings.cortex_api_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Nexus_3...")
    app.state.start_time = datetime.now()
    
    # Start background services
    asyncio.create_task(task_manager.process_tasks())
    
    yield
    
    # Cleanup
    logger.info("Shutting down Nexus_3...")
    await task_manager.shutdown()

# Create FastAPI app
app = FastAPI(
    title="Nexus_3 API",
    description="AI Orchestration System - Simplified and Working",
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
        "description": "AI Orchestration System",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "tasks": "/tasks",
            "orchestrate": "/orchestrate",
            "services": "/services"
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
    
    # Add to task manager
    await task_manager.add_task(task)
    
    return TaskCreateResponse(
        id=task_id,
        status="created",
        message=f"Task {task_id} created and queued for processing"
    )

@app.get("/tasks", response_model=List[TaskInfo])
async def list_tasks(status: Optional[TaskStatus] = None, limit: int = 100):
    """List tasks with optional status filter"""
    tasks = await task_manager.list_tasks(status=status, limit=limit)
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskInfo)
async def get_task(task_id: str):
    """Get task details"""
    task = await task_manager.get_task(task_id)
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
    success = await task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    return {"status": "cancelled", "task_id": task_id}

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
    response.status = TaskStatus.COMPLETED
    response.final_result = {"message": "Orchestration completed"}
    
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
    
    # Add more services as integrated
    
    return services

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)

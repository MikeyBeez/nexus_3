"""API Response Models"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(str, Enum):
    ANALYSIS = "analysis"
    GENERATION = "generation"
    TRANSFORMATION = "transformation"
    ORCHESTRATION = "orchestration"

class ServiceType(str, Enum):
    CORTEX = "cortex"
    LOCAL = "local"
    EXTERNAL = "external"

# Request Models
class TaskCreateRequest(BaseModel):
    type: TaskType
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    timeout: Optional[int] = None

class TaskUpdateRequest(BaseModel):
    status: Optional[TaskStatus] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Response Models
class TaskInfo(BaseModel):
    id: str
    type: TaskType
    status: TaskStatus
    description: str
    parameters: Dict[str, Any]
    priority: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class TaskCreateResponse(BaseModel):
    id: str
    status: str
    message: str

class ServiceStatus(BaseModel):
    name: str
    type: ServiceType
    status: str
    healthy: bool
    last_check: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SystemStatus(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    tasks: Dict[str, int]  # status -> count
    services: List[ServiceStatus]
    timestamp: datetime

class OrchestrationRequest(BaseModel):
    goal: str
    context: Dict[str, Any] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    max_steps: int = Field(default=10, ge=1, le=50)

class OrchestrationStep(BaseModel):
    step_number: int
    action: str
    service: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    status: TaskStatus
    duration_ms: Optional[int] = None

class OrchestrationResponse(BaseModel):
    id: str
    goal: str
    status: TaskStatus
    steps: List[OrchestrationStep]
    total_duration_ms: Optional[int] = None
    final_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

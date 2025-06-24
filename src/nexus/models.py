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
    MODULE = "module"

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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for module execution"""
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "description": self.description,
            "parameters": self.parameters,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }

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

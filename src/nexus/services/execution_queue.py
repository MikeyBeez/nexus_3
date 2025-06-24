"""Enhanced Execution Queue with Module Support"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid
import threading
from collections import defaultdict

from ..models import TaskInfo, TaskStatus, TaskType
from ..modules.base import ModuleLoader, ExecutorModule

logger = logging.getLogger(__name__)

class Priority(Enum):
    URGENT = "urgent"
    NORMAL = "normal"
    BATCH = "batch"

class ExecutionQueue:
    """Advanced execution queue with modular executor support"""
    
    def __init__(self, module_loader: ModuleLoader, num_workers: int = 3):
        self.module_loader = module_loader
        self.num_workers = num_workers
        
        # Task storage
        self.tasks: Dict[str, TaskInfo] = {}
        
        # Priority queues
        self.task_queues: Dict[str, List[str]] = {
            Priority.URGENT.value: [],
            Priority.NORMAL.value: [],
            Priority.BATCH.value: []
        }
        
        # Queue lock for thread safety
        self.queue_lock = threading.Lock()
        
        # Workers
        self.workers: List['QueueWorker'] = []
        self.worker_tasks: List[asyncio.Task] = []
        self.running = False
        
        # Statistics
        self.stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "by_executor": defaultdict(lambda: {"completed": 0, "failed": 0})
        }
    
    async def start(self):
        """Start the execution queue and workers"""
        if self.running:
            logger.warning("Execution queue already running")
            return
        
        self.running = True
        
        # Load default executors
        await self._load_default_executors()
        
        # Start workers
        for i in range(self.num_workers):
            worker = QueueWorker(f"worker-{i}", self)
            self.workers.append(worker)
            
            task = asyncio.create_task(worker.run())
            self.worker_tasks.append(task)
        
        logger.info(f"Started execution queue with {self.num_workers} workers")
    
    async def stop(self):
        """Stop the execution queue"""
        if not self.running:
            return
        
        logger.info("Stopping execution queue...")
        self.running = False
        
        # Stop all workers
        for worker in self.workers:
            worker.running = False
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        self.workers.clear()
        self.worker_tasks.clear()
        
        logger.info("Execution queue stopped")
    
    async def _load_default_executors(self):
        """Load default executor modules"""
        # Load command executor
        command_executor = self.module_loader.load_module("command_executor")
        if command_executor:
            await command_executor.initialize()
            await command_executor.activate()
            logger.info("Loaded command executor")
    
    def submit_task(self, task: TaskInfo, priority: Priority = Priority.NORMAL) -> str:
        """Submit a task to the queue"""
        with self.queue_lock:
            # Store task
            self.tasks[task.id] = task
            
            # Add to appropriate queue
            self.task_queues[priority.value].append(task.id)
            
            # Update stats
            self.stats["total_submitted"] += 1
            
            logger.info(f"Task {task.id} submitted to {priority.value} queue")
            return task.id
    
    def get_next_task(self) -> Optional[str]:
        """Get the next task from priority queues"""
        with self.queue_lock:
            # Check queues in priority order
            for priority in [Priority.URGENT, Priority.NORMAL, Priority.BATCH]:
                queue = self.task_queues[priority.value]
                if queue:
                    task_id = queue.pop(0)
                    return task_id
            return None
    
    async def execute_task(self, task_id: str, worker_id: str) -> Dict[str, Any]:
        """Execute a task using appropriate executor module"""
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "error": "Task not found"}
        
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            # Find executor that can handle this task
            executor = await self._find_executor(task)
            if not executor:
                raise Exception("No executor available for task type")
            
            # Execute the task
            logger.info(f"Worker {worker_id} executing task {task_id} with {executor.id}")
            
            result = await executor.execute_task(task.to_dict())
            
            # Update task based on result
            if result.get("status") == "success":
                task.status = TaskStatus.COMPLETED
                task.result = result
                self.stats["total_completed"] += 1
                self.stats["by_executor"][executor.id]["completed"] += 1
            else:
                task.status = TaskStatus.FAILED
                task.error = result.get("error", "Unknown error")
                task.result = result
                self.stats["total_failed"] += 1
                self.stats["by_executor"][executor.id]["failed"] += 1
            
            task.completed_at = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            self.stats["total_failed"] += 1
            
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _find_executor(self, task: TaskInfo) -> Optional[ExecutorModule]:
        """Find an executor module that can handle the task"""
        # Get all loaded executor modules
        for module_id, module in self.module_loader.get_loaded_modules().items():
            if isinstance(module, ExecutorModule) and module.is_active:
                if await module.can_execute(task.to_dict()):
                    return module
        
        return None
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: Optional[TaskStatus] = None, limit: int = 100) -> List[TaskInfo]:
        """List tasks with optional filtering"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        with self.queue_lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.PENDING:
                # Remove from queue
                for priority, queue in self.task_queues.items():
                    if task_id in queue:
                        queue.remove(task_id)
                        break
                
                # Update status
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                
                logger.info(f"Task {task_id} cancelled")
                return True
            
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.queue_lock:
            queue_counts = {
                priority: len(queue) 
                for priority, queue in self.task_queues.items()
            }
        
        # Count tasks by status
        status_counts = defaultdict(int)
        for task in self.tasks.values():
            status_counts[task.status.value] += 1
        
        # Worker status
        active_workers = len([w for w in self.workers if w.current_task])
        
        return {
            "queues": queue_counts,
            "tasks": dict(status_counts),
            "workers": {
                "total": len(self.workers),
                "active": active_workers,
                "idle": len(self.workers) - active_workers
            },
            "totals": {
                "submitted": self.stats["total_submitted"],
                "completed": self.stats["total_completed"],
                "failed": self.stats["total_failed"]
            },
            "by_executor": dict(self.stats["by_executor"])
        }

class QueueWorker:
    """Worker that processes tasks from the queue"""
    
    def __init__(self, worker_id: str, queue: ExecutionQueue):
        self.worker_id = worker_id
        self.queue = queue
        self.running = True
        self.current_task = None
    
    async def run(self):
        """Main worker loop"""
        logger.info(f"Worker {self.worker_id} started")
        
        while self.running and self.queue.running:
            try:
                # Get next task
                task_id = self.queue.get_next_task()
                
                if task_id:
                    self.current_task = task_id
                    await self.queue.execute_task(task_id, self.worker_id)
                    self.current_task = None
                else:
                    # No tasks, wait a bit
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                self.current_task = None
                await asyncio.sleep(1)
        
        logger.info(f"Worker {self.worker_id} stopped")

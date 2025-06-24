"""Task Manager Service"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

from ..models import TaskInfo, TaskStatus, TaskUpdateRequest

logger = logging.getLogger(__name__)

class TaskManager:
    """Manages task execution and lifecycle"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running = True
        self.workers = []
        self.lock = asyncio.Lock()
    
    async def add_task(self, task: TaskInfo) -> None:
        """Add a task to the manager"""
        async with self.lock:
            self.tasks[task.id] = task
            await self.task_queue.put(task.id)
            logger.info(f"Task {task.id} added to queue")
    
    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    async def list_tasks(self, status: Optional[TaskStatus] = None, limit: int = 100) -> List[TaskInfo]:
        """List tasks with optional filtering"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    async def update_task(self, task_id: str, update: TaskUpdateRequest) -> Optional[TaskInfo]:
        """Update task status or result"""
        async with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            if update.status:
                task.status = update.status
                if update.status == TaskStatus.RUNNING and not task.started_at:
                    task.started_at = datetime.now()
                elif update.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.completed_at = datetime.now()
            
            if update.result is not None:
                task.result = update.result
            
            if update.error:
                task.error = update.error
            
            task.updated_at = datetime.now()
            
            logger.info(f"Task {task_id} updated: status={task.status}")
            return task
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        async with self.lock:
            task = self.tasks.get(task_id)
            if not task or task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return False
            
            task.status = TaskStatus.CANCELLED
            task.updated_at = datetime.now()
            task.completed_at = datetime.now()
            
            logger.info(f"Task {task_id} cancelled")
            return True
    
    def get_statistics(self) -> Dict[str, int]:
        """Get task statistics by status"""
        stats = defaultdict(int)
        for task in self.tasks.values():
            stats[task.status.value] += 1
        return dict(stats)
    
    async def process_tasks(self):
        """Main task processing loop"""
        logger.info("Starting task processor")
        
        while self.running:
            try:
                # Get task from queue with timeout
                task_id = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                task = self.tasks.get(task_id)
                if not task or task.status != TaskStatus.PENDING:
                    continue
                
                # Update task status
                await self.update_task(task_id, TaskUpdateRequest(status=TaskStatus.RUNNING))
                
                # Process task based on type
                try:
                    result = await self._execute_task(task)
                    await self.update_task(
                        task_id, 
                        TaskUpdateRequest(
                            status=TaskStatus.COMPLETED,
                            result=result
                        )
                    )
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    await self.update_task(
                        task_id,
                        TaskUpdateRequest(
                            status=TaskStatus.FAILED,
                            error=str(e)
                        )
                    )
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Task processor error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: TaskInfo) -> Dict[str, Any]:
        """Execute a specific task"""
        logger.info(f"Executing task {task.id} of type {task.type}")
        
        # Simulate task execution
        await asyncio.sleep(2)
        
        # Return mock result based on task type
        return {
            "status": "success",
            "task_id": task.id,
            "type": task.type.value,
            "message": f"Task {task.description} completed",
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Shutdown the task manager"""
        logger.info("Shutting down task manager")
        self.running = False
        
        # Cancel remaining tasks
        while not self.task_queue.empty():
            try:
                task_id = self.task_queue.get_nowait()
                await self.cancel_task(task_id)
            except asyncio.QueueEmpty:
                break

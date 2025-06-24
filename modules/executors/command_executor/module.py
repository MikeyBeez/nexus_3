"""Command Executor Module - Executes system commands"""
import asyncio
import subprocess
import os
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from nexus.modules.base import ExecutorModule, ModuleManifest

logger = logging.getLogger(__name__)

class Module(ExecutorModule):
    """Command executor that runs system commands and scripts"""
    
    def __init__(self, manifest: ModuleManifest):
        super().__init__(manifest)
        self.active_processes: Dict[str, subprocess.Popen] = {}
        
    async def initialize(self) -> bool:
        """Initialize the command executor"""
        logger.info(f"Initializing {self.name}")
        return True
    
    async def shutdown(self) -> bool:
        """Shutdown the executor and cleanup processes"""
        logger.info(f"Shutting down {self.name}")
        
        # Terminate any active processes
        for task_id, process in self.active_processes.items():
            if process.poll() is None:  # Process still running
                logger.warning(f"Terminating active process for task {task_id}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        self.active_processes.clear()
        return True
    
    async def can_execute(self, task: Dict[str, Any]) -> bool:
        """Check if this executor can handle the task"""
        # Can execute if task has a command
        return task.get('command') is not None
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute based on context - delegates to execute_task"""
        task = context.get('task')
        if not task:
            return {
                "status": "error",
                "error": "No task provided in context"
            }
        
        return await self.execute_task(task)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command task"""
        if not self.is_active:
            return {
                "status": "error",
                "error": "Module is not active"
            }
        
        task_id = task.get('id', 'unknown')
        command = task.get('command')
        args = task.get('args', [])
        
        if not command:
            return {
                "status": "error",
                "error": "No command specified"
            }
        
        # Build full command
        cmd = [command]
        if args:
            cmd.extend(args)
        
        # Get execution parameters
        timeout = task.get('timeout_seconds', self.config.get('default_timeout_seconds', 300))
        working_dir = task.get('working_directory', os.getcwd())
        environment = task.get('environment', {})
        capture_output = task.get('capture_output', self.config.get('capture_output', True))
        use_shell = task.get('shell', self.config.get('shell', False))
        
        # Setup environment
        env = os.environ.copy()
        if environment:
            env.update(environment)
        
        logger.info(f"Executing command for task {task_id}: {' '.join(cmd)}")
        
        try:
            start_time = time.time()
            
            if use_shell:
                # Join command for shell execution
                cmd_str = ' '.join(cmd)
                result = await asyncio.create_subprocess_shell(
                    cmd_str,
                    stdout=asyncio.subprocess.PIPE if capture_output else None,
                    stderr=asyncio.subprocess.PIPE if capture_output else None,
                    cwd=working_dir,
                    env=env
                )
            else:
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE if capture_output else None,
                    stderr=asyncio.subprocess.PIPE if capture_output else None,
                    cwd=working_dir,
                    env=env
                )
            
            # Store process reference
            self.active_processes[task_id] = result
            
            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(),
                    timeout=timeout
                )
                
                execution_time = time.time() - start_time
                
                # Decode output if captured
                stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
                stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
                
                # Remove from active processes
                self.active_processes.pop(task_id, None)
                
                if result.returncode == 0:
                    logger.info(f"Task {task_id} completed successfully in {execution_time:.2f}s")
                    return {
                        "status": "success",
                        "exit_code": result.returncode,
                        "stdout": stdout_text,
                        "stderr": stderr_text,
                        "execution_time": execution_time,
                        "completed_at": datetime.now().isoformat()
                    }
                else:
                    logger.error(f"Task {task_id} failed with exit code {result.returncode}")
                    return {
                        "status": "failed",
                        "exit_code": result.returncode,
                        "stdout": stdout_text,
                        "stderr": stderr_text,
                        "execution_time": execution_time,
                        "error": f"Command exited with code {result.returncode}",
                        "completed_at": datetime.now().isoformat()
                    }
                    
            except asyncio.TimeoutError:
                # Kill the process
                result.terminate()
                try:
                    await asyncio.wait_for(result.wait(), timeout=5)
                except asyncio.TimeoutError:
                    result.kill()
                    await result.wait()
                
                self.active_processes.pop(task_id, None)
                
                logger.error(f"Task {task_id} timed out after {timeout}s")
                return {
                    "status": "failed",
                    "error": f"Command timed out after {timeout} seconds",
                    "execution_time": timeout,
                    "completed_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Task {task_id} execution error: {e}")
            self.active_processes.pop(task_id, None)
            
            return {
                "status": "failed",
                "error": f"Execution error: {str(e)}",
                "completed_at": datetime.now().isoformat()
            }
    
    def get_active_tasks(self) -> List[str]:
        """Get list of currently executing task IDs"""
        # Clean up completed processes
        completed = []
        for task_id, process in self.active_processes.items():
            if process.poll() is not None:
                completed.append(task_id)
        
        for task_id in completed:
            self.active_processes.pop(task_id, None)
        
        return list(self.active_processes.keys())

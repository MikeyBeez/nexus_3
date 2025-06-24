"""Command Executor Module - Executes system commands"""
import os
import subprocess
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import shlex

from nexus.modules.base import BaseModule

logger = logging.getLogger(__name__)


class CommandExecutor(BaseModule):
    """Executor module that runs system commands"""
    
    async def setup(self):
        """Initialize the command executor"""
        self.default_timeout = self.config.get('default_timeout', 300)
        self.max_timeout = self.config.get('max_timeout', 3600)
        self.capture_output = self.config.get('capture_output', True)
        self.use_shell = self.config.get('shell', False)
        logger.info(f"Command executor initialized with timeout={self.default_timeout}s")
    
    async def teardown(self):
        """Clean up resources"""
        pass
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command based on context
        
        Expected context:
        - command: str or List[str] - Command to execute
        - args: List[str] - Additional arguments (optional)
        - timeout: int - Command timeout in seconds (optional)
        - working_directory: str - Working directory (optional)
        - environment: Dict[str, str] - Environment variables (optional)
        - capture_output: bool - Whether to capture output (optional)
        """
        # Extract command
        command = context.get('command')
        if not command:
            raise ValueError("No command provided in context")
        
        # Build command list
        if isinstance(command, str):
            if self.use_shell:
                cmd = command
            else:
                cmd = shlex.split(command)
        else:
            cmd = command
        
        # Add additional arguments if provided
        args = context.get('args', [])
        if args and not self.use_shell:
            if isinstance(cmd, list):
                cmd.extend(args)
            else:
                cmd = [cmd] + args
        
        # Get execution parameters
        timeout = min(
            context.get('timeout', self.default_timeout),
            self.max_timeout
        )
        working_dir = context.get('working_directory', os.getcwd())
        capture = context.get('capture_output', self.capture_output)
        
        # Prepare environment
        env = os.environ.copy()
        custom_env = context.get('environment', {})
        if custom_env:
            env.update(custom_env)
        
        # Log execution details
        logger.info(f"Executing command: {cmd}")
        logger.debug(f"Working directory: {working_dir}")
        logger.debug(f"Timeout: {timeout}s")
        
        # Execute command
        try:
            if asyncio.get_event_loop().is_running():
                # Async execution
                result = await self._execute_async(
                    cmd, working_dir, env, timeout, capture
                )
            else:
                # Sync execution fallback
                result = self._execute_sync(
                    cmd, working_dir, env, timeout, capture
                )
            
            return result
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out after {timeout}s")
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Command timed out after {timeout} seconds",
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": e.stderr.decode() if e.stderr else "",
                "timed_out": True
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "exit_code": -1,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "timed_out": False
            }
    
    async def _execute_async(self, cmd, working_dir, env, timeout, capture):
        """Execute command asynchronously"""
        if self.use_shell and isinstance(cmd, list):
            cmd = ' '.join(cmd)
        
        proc = await asyncio.create_subprocess_shell(
            cmd if self.use_shell else None,
            *cmd if not self.use_shell else [],
            stdout=asyncio.subprocess.PIPE if capture else None,
            stderr=asyncio.subprocess.PIPE if capture else None,
            cwd=working_dir,
            env=env
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            
            return {
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "error": None if proc.returncode == 0 else f"Process exited with code {proc.returncode}",
                "timed_out": False
            }
            
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise subprocess.TimeoutExpired(cmd, timeout)
    
    def _execute_sync(self, cmd, working_dir, env, timeout, capture):
        """Execute command synchronously"""
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            env=env,
            capture_output=capture,
            text=True,
            timeout=timeout,
            shell=self.use_shell
        )
        
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout if capture else "",
            "stderr": result.stderr if capture else "",
            "error": None if result.returncode == 0 else f"Process exited with code {result.returncode}",
            "timed_out": False
        }


# Module class name for loader
Module = CommandExecutor

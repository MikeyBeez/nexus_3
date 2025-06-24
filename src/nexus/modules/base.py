"""Base Module System for Nexus_3"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import yaml
import importlib.util
import os
import logging

logger = logging.getLogger(__name__)

class ModuleManifest:
    """Module manifest data"""
    def __init__(self, manifest_data: Dict[str, Any]):
        self.id = manifest_data['id']
        self.version = manifest_data['version']
        self.type = manifest_data['type']
        self.name = manifest_data['name']
        self.description = manifest_data.get('description', '')
        self.metadata = manifest_data.get('metadata', {})
        self.capabilities = manifest_data.get('capabilities', [])
        self.dependencies = manifest_data.get('dependencies', [])
        self.config = manifest_data.get('config', {})
        self.entry_point = manifest_data.get('entry_point', 'module.py')

class BaseModule(ABC):
    """Base class for all Nexus modules"""
    
    def __init__(self, manifest: ModuleManifest):
        self.manifest = manifest
        self.id = manifest.id
        self.version = manifest.version
        self.type = manifest.type
        self.name = manifest.name
        self.config = manifest.config.copy()
        self.loaded_at = datetime.now()
        self.is_active = False
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the module"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the module"""
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute module logic"""
        pass
    
    async def activate(self) -> bool:
        """Activate the module"""
        if not self.is_active:
            self.is_active = True
            logger.info(f"Module {self.id} activated")
        return True
    
    async def deactivate(self) -> bool:
        """Deactivate the module"""
        if self.is_active:
            self.is_active = False
            logger.info(f"Module {self.id} deactivated")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "is_active": self.is_active,
            "loaded_at": self.loaded_at.isoformat(),
            "capabilities": self.manifest.capabilities
        }
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """Update module configuration"""
        self.config.update(config)
        logger.info(f"Module {self.id} config updated")
        return True

class ExecutorModule(BaseModule):
    """Base class for executor modules that run tasks"""
    
    @abstractmethod
    async def can_execute(self, task: Dict[str, Any]) -> bool:
        """Check if this executor can handle the task"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task"""
        pass

class ModuleLoader:
    """Dynamic module loader"""
    
    def __init__(self, modules_path: str):
        self.modules_path = modules_path
        self.loaded_modules: Dict[str, BaseModule] = {}
        
    def load_manifest(self, module_path: str) -> Optional[ModuleManifest]:
        """Load module manifest from YAML"""
        manifest_path = os.path.join(module_path, 'manifest.yaml')
        if not os.path.exists(manifest_path):
            logger.error(f"Manifest not found: {manifest_path}")
            return None
            
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f)
            return ModuleManifest(manifest_data)
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            return None
    
    def load_module(self, module_id: str) -> Optional[BaseModule]:
        """Load a module by ID"""
        if module_id in self.loaded_modules:
            logger.info(f"Module {module_id} already loaded")
            return self.loaded_modules[module_id]
        
        # Find module directory
        module_path = None
        for root, dirs, files in os.walk(self.modules_path):
            if 'manifest.yaml' in files:
                manifest = self.load_manifest(root)
                if manifest and manifest.id == module_id:
                    module_path = root
                    break
        
        if not module_path:
            logger.error(f"Module {module_id} not found")
            return None
        
        # Load manifest
        manifest = self.load_manifest(module_path)
        if not manifest:
            return None
        
        # Load module code
        try:
            entry_point = os.path.join(module_path, manifest.entry_point)
            spec = importlib.util.spec_from_file_location(module_id, entry_point)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find module class (should be named Module)
            if not hasattr(module, 'Module'):
                logger.error(f"Module class not found in {entry_point}")
                return None
            
            # Instantiate module
            module_instance = module.Module(manifest)
            self.loaded_modules[module_id] = module_instance
            
            logger.info(f"Module {module_id} loaded successfully")
            return module_instance
            
        except Exception as e:
            logger.error(f"Failed to load module {module_id}: {e}")
            return None
    
    async def unload_module(self, module_id: str) -> bool:
        """Unload a module"""
        if module_id not in self.loaded_modules:
            logger.warning(f"Module {module_id} not loaded")
            return False
        
        module = self.loaded_modules[module_id]
        
        # Deactivate and shutdown
        await module.deactivate()
        await module.shutdown()
        
        # Remove from loaded modules
        del self.loaded_modules[module_id]
        
        logger.info(f"Module {module_id} unloaded")
        return True
    
    def list_available_modules(self) -> List[Dict[str, Any]]:
        """List all available modules"""
        modules = []
        
        for root, dirs, files in os.walk(self.modules_path):
            if 'manifest.yaml' in files:
                manifest = self.load_manifest(root)
                if manifest:
                    modules.append({
                        "id": manifest.id,
                        "name": manifest.name,
                        "type": manifest.type,
                        "version": manifest.version,
                        "description": manifest.description,
                        "loaded": manifest.id in self.loaded_modules
                    })
        
        return modules
    
    def get_loaded_modules(self) -> Dict[str, BaseModule]:
        """Get all loaded modules"""
        return self.loaded_modules.copy()

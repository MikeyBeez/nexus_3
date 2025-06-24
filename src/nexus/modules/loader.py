"""Module loader for Nexus_3"""
import os
import yaml
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Optional, List, Type
from .base import BaseModule, ModuleManifest

logger = logging.getLogger(__name__)


class ModuleLoader:
    """Loads and manages Nexus modules"""
    
    def __init__(self, modules_dir: str = None):
        self.modules_dir = Path(modules_dir or os.environ.get(
            "NEXUS_MODULES_DIR", 
            "/Users/bard/Code/nexus_3/modules"
        ))
        self.loaded_modules: Dict[str, BaseModule] = {}
        self.available_modules: Dict[str, ModuleManifest] = {}
        
    def scan_modules(self) -> Dict[str, ModuleManifest]:
        """Scan modules directory for available modules"""
        self.available_modules.clear()
        
        for module_type in ["orchestrators", "analyzers", "executors", "integrations"]:
            type_dir = self.modules_dir / module_type
            if not type_dir.exists():
                continue
                
            for module_dir in type_dir.iterdir():
                if not module_dir.is_dir():
                    continue
                    
                manifest_path = module_dir / "manifest.yaml"
                if manifest_path.exists():
                    try:
                        manifest = self._load_manifest(manifest_path)
                        self.available_modules[manifest.id] = manifest
                        logger.info(f"Found module: {manifest.id} ({manifest.name})")
                    except Exception as e:
                        logger.error(f"Failed to load manifest from {manifest_path}: {e}")
        
        return self.available_modules
    
    def _load_manifest(self, manifest_path: Path) -> ModuleManifest:
        """Load module manifest from YAML file"""
        with open(manifest_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return ModuleManifest(
            id=data['id'],
            version=data['version'],
            type=data['type'],
            name=data['name'],
            description=data['description'],
            metadata=data.get('metadata', {}),
            capabilities=data.get('capabilities', []),
            dependencies=data.get('dependencies', []),
            config=data.get('config', {}),
            entry_point=data['entry_point']
        )
    
    async def load_module(self, module_id: str) -> Optional[BaseModule]:
        """Load a module by ID"""
        # Check if already loaded
        if module_id in self.loaded_modules:
            logger.info(f"Module {module_id} already loaded")
            return self.loaded_modules[module_id]
        
        # Check if module exists
        if module_id not in self.available_modules:
            logger.error(f"Module {module_id} not found")
            return None
        
        manifest = self.available_modules[module_id]
        
        # Check dependencies
        for dep in manifest.dependencies:
            if dep not in self.loaded_modules:
                logger.info(f"Loading dependency {dep} for {module_id}")
                dep_module = await self.load_module(dep)
                if not dep_module:
                    logger.error(f"Failed to load dependency {dep}")
                    return None
        
        # Load the module
        try:
            module_dir = self.modules_dir / manifest.type / module_id
            module_path = module_dir / manifest.entry_point
            
            # Dynamic import
            spec = importlib.util.spec_from_file_location(module_id, module_path)
            module_lib = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module_lib)
            
            # Find the module class (assumes it's named Module)
            module_class = getattr(module_lib, 'Module', None)
            if not module_class:
                # Try to find any class that inherits from BaseModule
                for name, obj in module_lib.__dict__.items():
                    if isinstance(obj, type) and issubclass(obj, BaseModule) and obj != BaseModule:
                        module_class = obj
                        break
            
            if not module_class:
                raise RuntimeError(f"No module class found in {module_path}")
            
            # Create instance
            module_instance = module_class(manifest)
            
            # Initialize
            if await module_instance.initialize():
                self.loaded_modules[module_id] = module_instance
                logger.info(f"Successfully loaded module {module_id}")
                return module_instance
            else:
                logger.error(f"Failed to initialize module {module_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load module {module_id}: {e}")
            return None
    
    async def unload_module(self, module_id: str, force: bool = False) -> bool:
        """Unload a module"""
        if module_id not in self.loaded_modules:
            logger.warning(f"Module {module_id} not loaded")
            return True
        
        module = self.loaded_modules[module_id]
        
        # Check if other modules depend on this one
        if not force:
            for other_id, other_module in self.loaded_modules.items():
                if other_id != module_id and module_id in other_module.manifest.dependencies:
                    logger.error(f"Cannot unload {module_id}: {other_id} depends on it")
                    return False
        
        # Cleanup the module
        try:
            await module.cleanup()
            del self.loaded_modules[module_id]
            logger.info(f"Successfully unloaded module {module_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload module {module_id}: {e}")
            return False
    
    def get_loaded_modules(self, module_type: Optional[str] = None) -> List[BaseModule]:
        """Get all loaded modules, optionally filtered by type"""
        modules = list(self.loaded_modules.values())
        if module_type:
            modules = [m for m in modules if m.type == module_type]
        return modules
    
    def get_module(self, module_id: str) -> Optional[BaseModule]:
        """Get a loaded module by ID"""
        return self.loaded_modules.get(module_id)
    
    def find_modules_with_capabilities(self, capabilities: List[str]) -> List[BaseModule]:
        """Find loaded modules that have all specified capabilities"""
        matching_modules = []
        for module in self.loaded_modules.values():
            if module.matches_capabilities(capabilities):
                matching_modules.append(module)
        return matching_modules
    
    async def reload_module(self, module_id: str) -> Optional[BaseModule]:
        """Reload a module (unload and load again)"""
        # First unload
        if module_id in self.loaded_modules:
            await self.unload_module(module_id, force=True)
        
        # Rescan to pick up any manifest changes
        self.scan_modules()
        
        # Load again
        return await self.load_module(module_id)
    
    def get_module_stats(self) -> Dict[str, Any]:
        """Get statistics for all loaded modules"""
        stats = {
            "available_modules": len(self.available_modules),
            "loaded_modules": len(self.loaded_modules),
            "modules_by_type": {},
            "module_stats": {}
        }
        
        # Count by type
        for module in self.loaded_modules.values():
            module_type = module.type
            stats["modules_by_type"][module_type] = stats["modules_by_type"].get(module_type, 0) + 1
            stats["module_stats"][module.id] = module.get_stats()
        
        return stats

"""Cortex API Client"""
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CortexClient:
    """Client for interacting with Cortex_2 API"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def health_check(self) -> bool:
        """Check if Cortex is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Cortex health check failed: {e}")
            return False
    
    async def analyze_context(self, text: str) -> Dict[str, Any]:
        """Analyze text context using Cortex"""
        try:
            response = await self.client.post(
                f"{self.base_url}/context/analyze",
                json={"text": text}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return {"error": str(e)}
    
    async def query_knowledge_graph(self, query_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Query the knowledge graph"""
        try:
            response = await self.client.post(
                f"{self.base_url}/knowledge-graph/query",
                json={"query_type": query_type, "parameters": parameters}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Knowledge graph query failed: {e}")
            return {"error": str(e)}
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage from Cortex"""
        try:
            response = await self.client.get(f"{self.base_url}/resources/memory")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Memory usage query failed: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

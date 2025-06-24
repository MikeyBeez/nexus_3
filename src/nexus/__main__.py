"""Main entry point for Nexus_3"""
import uvicorn
from .app import app
from .config import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )

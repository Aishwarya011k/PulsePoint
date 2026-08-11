#!/usr/bin/env python3
"""Entry point to run the FastAPI server."""
import uvicorn
import os
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )

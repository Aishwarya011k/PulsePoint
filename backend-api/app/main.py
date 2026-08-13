"""Main FastAPI application."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from app.database import Base, engine
from app.routes_auth import router as auth_router
from app.routes_targets import router as targets_router
from app.routes_internal import router as internal_router
from app.websocket_manager import manager


def run_startup_migrations():
    inspector = inspect(engine)
    if 'targets' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('targets')]
        with engine.begin() as conn:
            if 'public_slug' not in columns:
                conn.execute(text("ALTER TABLE targets ADD COLUMN public_slug VARCHAR(128) UNIQUE"))
            if 'is_public' not in columns:
                conn.execute(text("ALTER TABLE targets ADD COLUMN is_public BOOLEAN DEFAULT FALSE NOT NULL"))

# Create database tables and run lightweight migrations
Base.metadata.create_all(bind=engine)
run_startup_migrations()

# Initialize FastAPI app
app = FastAPI(
    title="PulsePoint Backend API",
    description="Phase 1 API for the PulsePoint monitoring platform",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(targets_router)
app.include_router(internal_router)


@app.websocket("/ws/targets")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "PulsePoint Backend API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

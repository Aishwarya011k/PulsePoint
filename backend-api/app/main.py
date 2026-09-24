"""Main FastAPI application."""
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.database import Base, engine
from app.metrics import REQUEST_LATENCY, REQUESTS, metrics_app
from app.models import Group
from app.routes_auth import router as auth_router
from app.routes_internal import router as internal_router
from app.routes_groups import router as groups_router
from app.routes_incidents import router as incidents_router
from app.routes_targets import router as targets_router
from app.websocket_manager import manager


def run_startup_migrations():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if 'groups' not in table_names:
        Group.__table__.create(bind=engine)
    if 'targets' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('targets')]
        with engine.begin() as conn:
            if 'public_slug' not in columns:
                conn.execute(text("ALTER TABLE targets ADD COLUMN public_slug VARCHAR(128) UNIQUE"))
            if 'is_public' not in columns:
                conn.execute(text("ALTER TABLE targets ADD COLUMN is_public BOOLEAN DEFAULT FALSE NOT NULL"))
            if 'group_id' not in columns:
                conn.execute(text("ALTER TABLE targets ADD COLUMN group_id INTEGER REFERENCES groups(id)"))
    if 'incidents' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('incidents')]
        with engine.begin() as conn:
            if 'postmortem_note' not in columns:
                conn.execute(text("ALTER TABLE incidents ADD COLUMN postmortem_note TEXT"))
            if 'postmortem_author' not in columns:
                conn.execute(text("ALTER TABLE incidents ADD COLUMN postmortem_author VARCHAR(255)"))
            if 'postmortem_updated_at' not in columns:
                conn.execute(text("ALTER TABLE incidents ADD COLUMN postmortem_updated_at DATETIME"))

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
    allow_origins=["http://localhost:3000", "http://localhost:30080"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observe_requests(request, call_next):
    """Record request volume and latency without changing response behavior."""
    started = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(time.perf_counter() - started)
    return response

# Include routers
app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(incidents_router)
app.include_router(targets_router)
app.include_router(internal_router)
app.mount("/metrics", metrics_app())


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

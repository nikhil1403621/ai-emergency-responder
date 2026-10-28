from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from app.database import init_db, get_db
from app.api.incidents import router as incidents_router
from app.api.units import router as units_router
from app.api.assess import router as assess_router
from app.services.websocket_manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and seed initial units
    init_db()
    yield


app = FastAPI(
    title="AI-Based Emergency Response System API",
    description=(
        "Academic prototype for incident reporting, AI-assisted triage, "
        "dispatcher-approved assignment, and live status tracking."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for client apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(incidents_router)
app.include_router(units_router)
app.include_router(assess_router)


@app.get("/health", tags=["Health"])
async def health_check():
    db_status = "connected"
    try:
        with get_db() as conn:
            conn.execute("SELECT 1;").fetchone()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "service": "AI-Based Emergency Response System",
        "version": "1.0.0",
        "mode": "academic_demonstration",
        "disclaimer": "Prototype for demonstration only. Not connected to real emergency services.",
        "database": db_status,
        "active_websocket_clients": len(ws_manager.active_connections),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.websocket("/ws/incidents")
async def websocket_incidents_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial welcome message
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to Emergency Response Live Dispatch WebSocket stream.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        while True:
            # Keep connection open and receive any client pings
            data = await websocket.receive_text()
            # If client sends ping, respond with pong
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# Serve frontend client static files if directory exists
client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "client")
if os.path.exists(client_dir):
    app.mount("/", StaticFiles(directory=client_dir, html=True), name="client")

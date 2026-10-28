from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.schemas.unit import UnitResponse, UnitLocationUpdate, UnitStatus
from app.services.duplicate_detector import haversine_distance_km
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/units", tags=["Response Units"])


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("", response_model=List[UnitResponse])
async def list_units(
    unit_type: Optional[str] = Query(None, description="Filter by unit type"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    query = "SELECT * FROM response_units WHERE 1=1"
    params = []
    if unit_type:
        query += " AND unit_type = ?"
        params.append(unit_type)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY id ASC"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [UnitResponse(**dict(r)) for r in rows]


@router.get("/nearby", response_model=List[UnitResponse])
async def get_nearby_units(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    unit_type: Optional[str] = Query(None, description="Preferred unit type"),
    max_distance_km: float = Query(50.0, ge=1.0, le=200.0)
):
    query = "SELECT * FROM response_units WHERE 1=1"
    params = []
    if unit_type:
        query += " AND unit_type = ?"
        params.append(unit_type)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]

    nearby_list = []
    for u in rows:
        dist = haversine_distance_km(latitude, longitude, u["latitude"], u["longitude"])
        if dist <= max_distance_km:
            # Estimate ETA: assume 45 km/h urban speed + 2 min dispatch reaction
            eta_mins = max(1, int(round((dist / 45.0) * 60) + 2))
            u["distance_km"] = dist
            u["estimated_eta_minutes"] = eta_mins
            nearby_list.append(UnitResponse(**u))

    # Sort primarily by proximity, and prioritize available units
    nearby_list.sort(key=lambda item: (0 if item.status == "available" else 1, item.distance_km))
    return nearby_list


@router.patch("/{unit_id}/location", response_model=UnitResponse)
async def update_unit_location(unit_id: str, payload: UnitLocationUpdate):
    current_time = now_iso()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM response_units WHERE id = ?", (unit_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Unit '{unit_id}' not found.")

        # Update unit current coordinates
        cursor.execute("""
            UPDATE response_units
            SET latitude = ?, longitude = ?, last_updated = ?
            WHERE id = ?
        """, (payload.latitude, payload.longitude, current_time, unit_id))

        # Store in unit locations audit table
        loc_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO unit_locations (
                id, unit_id, latitude, longitude, heading, speed_kmh, is_simulated, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            loc_id,
            unit_id,
            payload.latitude,
            payload.longitude,
            payload.heading,
            payload.speed_kmh,
            1 if payload.is_simulated else 0,
            current_time
        ))

        cursor.execute("SELECT * FROM response_units WHERE id = ?", (unit_id,))
        updated_unit = dict(cursor.fetchone())

    # WebSocket broadcast
    await ws_manager.broadcast({
        "type": "unit_location_updated",
        "unit_id": unit_id,
        "call_sign": updated_unit["call_sign"],
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "is_simulated": payload.is_simulated,
        "timestamp": current_time
    })

    return UnitResponse(**updated_unit)


@router.patch("/{unit_id}/status", response_model=UnitResponse)
async def update_unit_status(unit_id: str, status: UnitStatus):
    current_time = now_iso()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM response_units WHERE id = ?", (unit_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Unit '{unit_id}' not found.")

        cursor.execute("""
            UPDATE response_units
            SET status = ?, last_updated = ?
            WHERE id = ?
        """, (status.value, current_time, unit_id))

        cursor.execute("SELECT * FROM response_units WHERE id = ?", (unit_id,))
        updated_unit = dict(cursor.fetchone())

    await ws_manager.broadcast({
        "type": "unit_status_updated",
        "unit_id": unit_id,
        "status": status.value,
        "timestamp": current_time
    })

    return UnitResponse(**updated_unit)

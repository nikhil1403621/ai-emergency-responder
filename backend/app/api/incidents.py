from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
import uuid
import json
from datetime import datetime, timezone

from app.database import get_db
from app.schemas.incident import (
    IncidentCreate, IncidentResponse, IncidentStatusUpdate,
    IncidentAssignRequest, IncidentEventResponse, AssessmentResponse, DuplicateCandidate
)
from app.services.classifier import classify_incident
from app.services.duplicate_detector import find_duplicate_candidates
from app.services.lifecycle import validate_transition
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(payload: IncidentCreate):
    incident_id = str(uuid.uuid4())
    current_time = now_iso()

    # 1. Run AI baseline assessment
    assessment_data = classify_incident(payload.description)
    assessment_id = str(uuid.uuid4())

    with get_db() as conn:
        cursor = conn.cursor()

        # Query recent incidents for duplicate detection
        cursor.execute("SELECT id, description, latitude, longitude, created_at, status FROM incidents ORDER BY created_at DESC LIMIT 50;")
        recent_records = [dict(r) for r in cursor.fetchall()]
        duplicate_candidates = find_duplicate_candidates(
            new_description=payload.description,
            new_lat=payload.latitude,
            new_lon=payload.longitude,
            existing_incidents=recent_records
        )

        # 2. Insert incident
        cursor.execute("""
            INSERT INTO incidents (
                id, description, latitude, longitude, address_hint,
                category, urgency, status, reporter_name, reporter_contact,
                requires_review, assigned_unit_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id,
            payload.description,
            payload.latitude,
            payload.longitude,
            payload.address_hint,
            assessment_data["suggested_category"],
            assessment_data["suggested_urgency"],
            "reported",
            payload.reporter_name,
            payload.reporter_contact,
            1 if assessment_data["requires_review"] else 0,
            None,
            current_time,
            current_time
        ))

        # 3. Insert assessment
        cursor.execute("""
            INSERT INTO incident_assessments (
                id, incident_id, model_version, suggested_category,
                suggested_urgency, confidence, uncertainty, requires_review,
                reasoning, matched_keywords, recommended_unit_type, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_id,
            incident_id,
            assessment_data["model_version"],
            assessment_data["suggested_category"],
            assessment_data["suggested_urgency"],
            assessment_data["confidence"],
            assessment_data["uncertainty"],
            1 if assessment_data["requires_review"] else 0,
            assessment_data["reasoning"],
            json.dumps(assessment_data["matched_keywords"]),
            assessment_data["recommended_unit_type"],
            current_time
        ))

        # 4. Record initial event in event history
        event_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO incident_events (
                id, incident_id, event_type, actor_role, actor_id,
                from_status, to_status, details, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            incident_id,
            "incident_created",
            "citizen",
            payload.reporter_name or "anonymous",
            None,
            "reported",
            f"Emergency reported. AI triage recommendation: {assessment_data['suggested_category']} ({assessment_data['suggested_urgency']}).",
            current_time
        ))

        if duplicate_candidates:
            dup_event_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO incident_events (
                    id, incident_id, event_type, actor_role, actor_id,
                    from_status, to_status, details, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dup_event_id,
                incident_id,
                "duplicate_warning",
                "system_ai",
                "duplicate_detector",
                "reported",
                "reported",
                f"Flagged {len(duplicate_candidates)} potential duplicate reports for dispatcher verification.",
                current_time
            ))

    # WebSocket broadcast
    await ws_manager.broadcast({
        "type": "incident_created",
        "incident_id": incident_id,
        "category": assessment_data["suggested_category"],
        "urgency": assessment_data["suggested_urgency"],
        "status": "reported",
        "description": payload.description,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "created_at": current_time
    })

    return IncidentResponse(
        id=incident_id,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address_hint=payload.address_hint,
        category=assessment_data["suggested_category"],
        urgency=assessment_data["suggested_urgency"],
        status="reported",
        reporter_name=payload.reporter_name,
        reporter_contact=payload.reporter_contact,
        requires_review=assessment_data["requires_review"],
        assigned_unit_id=None,
        created_at=current_time,
        updated_at=current_time,
        assessment=AssessmentResponse(
            id=assessment_id,
            incident_id=incident_id,
            model_version=assessment_data["model_version"],
            suggested_category=assessment_data["suggested_category"],
            suggested_urgency=assessment_data["suggested_urgency"],
            confidence=assessment_data["confidence"],
            uncertainty=assessment_data["uncertainty"],
            requires_review=assessment_data["requires_review"],
            reasoning=assessment_data["reasoning"],
            matched_keywords=assessment_data["matched_keywords"],
            recommended_unit_type=assessment_data["recommended_unit_type"],
            created_at=current_time
        ),
        duplicate_candidates=[DuplicateCandidate(**c) for c in duplicate_candidates]
    )


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    urgency: Optional[str] = Query(None, description="Filter by urgency"),
    search: Optional[str] = Query(None, description="Search description text"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    query = "SELECT * FROM incidents WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    if urgency:
        query += " AND urgency = ?"
        params.append(urgency)
    if search:
        query += " AND description LIKE ?"
        params.append(f"%{search}%")

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    results = []
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        for row in rows:
            inc = dict(row)
            # Fetch latest assessment
            cursor.execute("""
                SELECT * FROM incident_assessments
                WHERE incident_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, (inc["id"],))
            ass_row = cursor.fetchone()
            assessment = None
            if ass_row:
                ass_dict = dict(ass_row)
                keywords = json.loads(ass_dict["matched_keywords"]) if ass_dict["matched_keywords"] else []
                assessment = AssessmentResponse(
                    id=ass_dict["id"],
                    incident_id=ass_dict["incident_id"],
                    model_version=ass_dict["model_version"],
                    suggested_category=ass_dict["suggested_category"],
                    suggested_urgency=ass_dict["suggested_urgency"],
                    confidence=ass_dict["confidence"],
                    uncertainty=ass_dict["uncertainty"],
                    requires_review=bool(ass_dict["requires_review"]),
                    reasoning=ass_dict["reasoning"],
                    matched_keywords=keywords,
                    recommended_unit_type=ass_dict["recommended_unit_type"],
                    created_at=ass_dict["created_at"]
                )

            results.append(IncidentResponse(
                id=inc["id"],
                description=inc["description"],
                latitude=inc["latitude"],
                longitude=inc["longitude"],
                address_hint=inc["address_hint"],
                category=inc["category"],
                urgency=inc["urgency"],
                status=inc["status"],
                reporter_name=inc["reporter_name"],
                reporter_contact=inc["reporter_contact"],
                requires_review=bool(inc["requires_review"]),
                assigned_unit_id=inc["assigned_unit_id"],
                created_at=inc["created_at"],
                updated_at=inc["updated_at"],
                assessment=assessment
            ))

    return results


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Incident with ID '{incident_id}' not found.")

        inc = dict(row)

        # Assessment
        cursor.execute("""
            SELECT * FROM incident_assessments
            WHERE incident_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (incident_id,))
        ass_row = cursor.fetchone()
        assessment = None
        if ass_row:
            ass_dict = dict(ass_row)
            keywords = json.loads(ass_dict["matched_keywords"]) if ass_dict["matched_keywords"] else []
            assessment = AssessmentResponse(
                id=ass_dict["id"],
                incident_id=ass_dict["incident_id"],
                model_version=ass_dict["model_version"],
                suggested_category=ass_dict["suggested_category"],
                suggested_urgency=ass_dict["suggested_urgency"],
                confidence=ass_dict["confidence"],
                uncertainty=ass_dict["uncertainty"],
                requires_review=bool(ass_dict["requires_review"]),
                reasoning=ass_dict["reasoning"],
                matched_keywords=keywords,
                recommended_unit_type=ass_dict["recommended_unit_type"],
                created_at=ass_dict["created_at"]
            )

        # Duplicate candidates among other incidents
        cursor.execute("SELECT id, description, latitude, longitude, created_at, status FROM incidents WHERE id != ? ORDER BY created_at DESC LIMIT 50;", (incident_id,))
        other_records = [dict(r) for r in cursor.fetchall()]
        duplicate_candidates = find_duplicate_candidates(
            new_description=inc["description"],
            new_lat=inc["latitude"],
            new_lon=inc["longitude"],
            existing_incidents=other_records
        )

        return IncidentResponse(
            id=inc["id"],
            description=inc["description"],
            latitude=inc["latitude"],
            longitude=inc["longitude"],
            address_hint=inc["address_hint"],
            category=inc["category"],
            urgency=inc["urgency"],
            status=inc["status"],
            reporter_name=inc["reporter_name"],
            reporter_contact=inc["reporter_contact"],
            requires_review=bool(inc["requires_review"]),
            assigned_unit_id=inc["assigned_unit_id"],
            created_at=inc["created_at"],
            updated_at=inc["updated_at"],
            assessment=assessment,
            duplicate_candidates=[DuplicateCandidate(**c) for c in duplicate_candidates]
        )


@router.get("/{incident_id}/events", response_model=List[IncidentEventResponse])
async def get_incident_events(incident_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

        cursor.execute("SELECT * FROM incident_events WHERE incident_id = ? ORDER BY timestamp ASC", (incident_id,))
        rows = cursor.fetchall()
        return [IncidentEventResponse(**dict(r)) for r in rows]


@router.patch("/{incident_id}/status", response_model=IncidentResponse)
async def update_incident_status(incident_id: str, payload: IncidentStatusUpdate):
    current_time = now_iso()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

        inc = dict(row)
        current_status = inc["status"]
        target_status = payload.status.value

        # Validate lifecycle rule
        try:
            validate_transition(current_status, target_status)
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err))

        # Update status
        cursor.execute("""
            UPDATE incidents
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (target_status, current_time, incident_id))

        # If incident resolved/closed/cancelled, free assigned unit
        if target_status in ["resolved", "closed", "cancelled"] and inc["assigned_unit_id"]:
            cursor.execute("""
                UPDATE response_units
                SET status = 'available', assigned_incident_id = NULL, last_updated = ?
                WHERE id = ?
            """, (current_time, inc["assigned_unit_id"]))

        # Log transition event
        event_id = str(uuid.uuid4())
        details = payload.notes or f"Status changed from '{current_status}' to '{target_status}' by {payload.actor_role} ({payload.actor_id})."
        cursor.execute("""
            INSERT INTO incident_events (
                id, incident_id, event_type, actor_role, actor_id,
                from_status, to_status, details, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            incident_id,
            "status_changed",
            payload.actor_role,
            payload.actor_id,
            current_status,
            target_status,
            details,
            current_time
        ))

    # WebSocket broadcast
    await ws_manager.broadcast({
        "type": "status_changed",
        "incident_id": incident_id,
        "from_status": current_status,
        "to_status": target_status,
        "actor_role": payload.actor_role,
        "actor_id": payload.actor_id,
        "timestamp": current_time
    })

    return await get_incident(incident_id)


@router.post("/{incident_id}/assign")
async def assign_unit_to_incident(incident_id: str, payload: IncidentAssignRequest):
    current_time = now_iso()
    with get_db() as conn:
        cursor = conn.cursor()
        # Verify incident
        cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        inc_row = cursor.fetchone()
        if not inc_row:
            raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
        inc = dict(inc_row)

        if inc["status"] in ["closed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot assign unit to an incident that is already {inc['status']}.")

        # Verify unit
        cursor.execute("SELECT * FROM response_units WHERE id = ?", (payload.unit_id,))
        unit_row = cursor.fetchone()
        if not unit_row:
            raise HTTPException(status_code=404, detail=f"Response unit '{payload.unit_id}' not found.")
        unit = dict(unit_row)

        if unit["status"] not in ["available", "dispatched"]:
            # Note: Allow dispatch or return note if already engaged
            pass

        # Update assignment records
        assignment_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO dispatch_assignments (
                id, incident_id, unit_id, dispatcher_id, dispatcher_notes, assigned_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'active')
        """, (
            assignment_id,
            incident_id,
            payload.unit_id,
            payload.dispatcher_id,
            payload.notes,
            current_time
        ))

        # Advance incident status if in early phase
        next_status = "dispatched"
        if inc["status"] in ["reported", "under_review", "assessed"]:
            cursor.execute("""
                UPDATE incidents
                SET assigned_unit_id = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (payload.unit_id, next_status, current_time, incident_id))
        else:
            cursor.execute("""
                UPDATE incidents
                SET assigned_unit_id = ?, updated_at = ?
                WHERE id = ?
            """, (payload.unit_id, current_time, incident_id))

        # Update unit record
        cursor.execute("""
            UPDATE response_units
            SET status = 'dispatched', assigned_incident_id = ?, last_updated = ?
            WHERE id = ?
        """, (incident_id, current_time, payload.unit_id))

        # Event log
        event_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO incident_events (
                id, incident_id, event_type, actor_role, actor_id,
                from_status, to_status, details, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            incident_id,
            "unit_assigned",
            "dispatcher",
            payload.dispatcher_id,
            inc["status"],
            next_status,
            f"Dispatcher '{payload.dispatcher_id}' assigned unit '{unit['call_sign']}' ({payload.unit_id}). Notes: {payload.notes or 'None'}",
            current_time
        ))

    # WebSocket broadcast
    await ws_manager.broadcast({
        "type": "unit_assigned",
        "incident_id": incident_id,
        "unit_id": payload.unit_id,
        "unit_call_sign": unit["call_sign"],
        "dispatcher_id": payload.dispatcher_id,
        "new_incident_status": next_status,
        "timestamp": current_time
    })

    return {
        "status": "success",
        "message": f"Unit {unit['call_sign']} successfully assigned to incident {incident_id}.",
        "assignment_id": assignment_id,
        "incident_id": incident_id,
        "unit_id": payload.unit_id
    }

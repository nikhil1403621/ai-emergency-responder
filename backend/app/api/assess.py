from fastapi import APIRouter, HTTPException
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.schemas.incident import AssessmentResponse
from app.services.classifier import classify_incident
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/incidents", tags=["Assessment"])


class AssessRequest(BaseModel):
    override_description: Optional[str] = None


@router.post("/{incident_id}/assess", response_model=AssessmentResponse)
async def assess_incident(incident_id: str, payload: Optional[AssessRequest] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

        incident = dict(row)
        text_to_assess = payload.override_description if payload and payload.override_description else incident["description"]

        # Run classifier
        assessment_data = classify_incident(text_to_assess)
        assessment_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()

        # Update incident record category and urgency if unassigned
        cursor.execute("""
            UPDATE incidents
            SET category = ?, urgency = ?, requires_review = ?, updated_at = ?
            WHERE id = ?
        """, (
            assessment_data["suggested_category"],
            assessment_data["suggested_urgency"],
            1 if assessment_data["requires_review"] else 0,
            current_time,
            incident_id
        ))

        # Insert assessment record
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

        # Log event
        event_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO incident_events (
                id, incident_id, event_type, actor_role, actor_id,
                from_status, to_status, details, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            incident_id,
            "incident_assessed",
            "system_ai",
            "triage_classifier",
            incident["status"],
            incident["status"],
            f"Triage refreshed: category='{assessment_data['suggested_category']}', urgency='{assessment_data['suggested_urgency']}', confidence={assessment_data['confidence']}.",
            current_time
        ))

    # WebSocket update
    await ws_manager.broadcast({
        "type": "incident_assessed",
        "incident_id": incident_id,
        "category": assessment_data["suggested_category"],
        "urgency": assessment_data["suggested_urgency"],
        "confidence": assessment_data["confidence"],
        "uncertainty": assessment_data["uncertainty"],
        "timestamp": current_time
    })

    return AssessmentResponse(
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
    )

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IncidentCategory(str, Enum):
    MEDICAL_EMERGENCY = "medical_emergency"
    FIRE = "fire"
    ROAD_ACCIDENT = "road_accident"
    CRIME_SECURITY = "crime_security"
    NATURAL_DISASTER = "natural_disaster"
    INFRASTRUCTURE_HAZARD = "infrastructure_hazard"
    OTHER_UNCERTAIN = "other_uncertain"


class IncidentUrgency(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    UNDER_REVIEW = "under_review"
    ASSESSED = "assessed"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    ASSISTANCE_IN_PROGRESS = "assistance_in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"
    REOPENED = "reopened"


class IncidentCreate(BaseModel):
    description: str = Field(..., min_length=10, max_length=2000, description="Description of the emergency incident")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude coordinate between -90 and 90")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude coordinate between -180 and 180")
    address_hint: Optional[str] = Field(None, max_length=255, description="Street address or location landmark")
    reporter_name: Optional[str] = Field(None, max_length=100)
    reporter_contact: Optional[str] = Field(None, max_length=50)


class AssessmentResponse(BaseModel):
    id: str
    incident_id: str
    model_version: str
    suggested_category: str
    suggested_urgency: str
    confidence: float
    uncertainty: float
    requires_review: bool
    reasoning: str
    matched_keywords: List[str]
    recommended_unit_type: str
    created_at: str


class DuplicateCandidate(BaseModel):
    incident_id: str
    description: str
    similarity_score: float
    distance_km: Optional[float] = None
    created_at: str
    status: str


class IncidentResponse(BaseModel):
    id: str
    description: str
    latitude: Optional[float]
    longitude: Optional[float]
    address_hint: Optional[str]
    category: str
    urgency: str
    status: str
    reporter_name: Optional[str]
    reporter_contact: Optional[str]
    requires_review: bool
    assigned_unit_id: Optional[str]
    created_at: str
    updated_at: str
    assessment: Optional[AssessmentResponse] = None
    duplicate_candidates: Optional[List[DuplicateCandidate]] = None


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus
    actor_role: str = Field("dispatcher", description="Role executing the update: citizen, dispatcher, responder")
    actor_id: str = Field("dispatcher_01", description="Identifier of the operator or responder")
    notes: Optional[str] = Field(None, max_length=500)


class IncidentAssignRequest(BaseModel):
    unit_id: str = Field(..., description="Target response unit ID")
    dispatcher_id: str = Field(..., description="ID of the approving dispatcher")
    notes: Optional[str] = Field(None, max_length=500, description="Dispatch instructions or notes")


class IncidentEventResponse(BaseModel):
    id: str
    incident_id: str
    event_type: str
    actor_role: str
    actor_id: str
    from_status: Optional[str]
    to_status: Optional[str]
    details: str
    timestamp: str

"""Data structures representing immutable Incident Lifecycle Events."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class IncidentEventModel:
    id: str
    incident_id: str
    event_type: str
    actor_role: str
    actor_id: str
    from_status: Optional[str]
    to_status: Optional[str]
    details: str
    timestamp: str

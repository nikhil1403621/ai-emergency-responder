"""Data structures representing Incident records in SQLite / PostgreSQL."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class IncidentModel:
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

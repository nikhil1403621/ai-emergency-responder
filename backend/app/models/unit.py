"""Data structures representing Response Units in the fleet."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResponseUnitModel:
    id: str
    call_sign: str
    unit_type: str
    status: str
    latitude: float
    longitude: float
    base_station: str
    assigned_incident_id: Optional[str]
    last_updated: str

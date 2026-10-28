from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class UnitType(str, Enum):
    AMBULANCE = "ambulance"
    FIRE_ENGINE = "fire_engine"
    PATROL_CAR = "patrol_car"
    RESCUE_TEAM = "rescue_team"
    UTILITY_TRUCK = "utility_truck"


class UnitStatus(str, Enum):
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    MAINTENANCE = "maintenance"


class UnitResponse(BaseModel):
    id: str
    call_sign: str
    unit_type: str
    status: str
    latitude: float
    longitude: float
    base_station: str
    assigned_incident_id: Optional[str] = None
    last_updated: str
    distance_km: Optional[float] = None
    estimated_eta_minutes: Optional[int] = None


class UnitLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    heading: Optional[float] = Field(None, ge=0.0, le=360.0)
    speed_kmh: Optional[float] = Field(None, ge=0.0, le=200.0)
    is_simulated: bool = Field(True, description="Flag indicating simulated vs physical GPS feed")

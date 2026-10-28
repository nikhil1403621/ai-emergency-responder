import pytest
import os
import tempfile
from fastapi.testclient import TestClient

# Use a temporary database for test isolation
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_PATH"] = temp_db.name

from app.main import app
from app.database import init_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    yield
    try:
        os.remove(temp_db.name)
    except Exception:
        pass


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AI-Based Emergency Response System"
    assert "disclaimer" in data
    assert data["database"] == "connected"


def test_create_valid_incident(client):
    payload = {
        "description": "Multi-vehicle collision on highway near exit 4 with injured passenger bleeding",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "address_hint": "Exit 4, Expressway",
        "reporter_name": "Citizen John",
        "reporter_contact": "+1-555-0199"
    }
    response = client.post("/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "reported"
    assert data["assessment"] is not None
    assert data["assessment"]["model_version"] == "v1.0-rule-baseline"
    assert "road_accident" in data["category"] or "medical_emergency" in data["category"]
    assert data["assessment"]["recommended_unit_type"] in ["ambulance", "patrol_car"]


def test_create_incident_validation_rejects_too_short(client):
    payload = {
        "description": "Help me",  # < 10 characters
        "latitude": 12.9716,
        "longitude": 77.5946
    }
    response = client.post("/incidents", json=payload)
    assert response.status_code == 422  # Unprocessable Entity validation error


def test_create_incident_validation_rejects_invalid_coordinates(client):
    payload = {
        "description": "Fire burning rapidly in an abandoned warehouse building",
        "latitude": 125.0,  # Invalid (> 90)
        "longitude": 77.5946
    }
    response = client.post("/incidents", json=payload)
    assert response.status_code == 422

    payload["latitude"] = 12.0
    payload["longitude"] = 250.0  # Invalid (> 180)
    response = client.post("/incidents", json=payload)
    assert response.status_code == 422


def test_list_and_get_incidents(client):
    list_resp = client.get("/incidents")
    assert list_resp.status_code == 200
    incidents = list_resp.json()
    assert len(incidents) >= 1

    first_id = incidents[0]["id"]
    get_resp = client.get(f"/incidents/{first_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == first_id

    events_resp = client.get(f"/incidents/{first_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) >= 1
    assert events[0]["event_type"] == "incident_created"


def test_units_and_nearby_search(client):
    units_resp = client.get("/units")
    assert units_resp.status_code == 200
    units = units_resp.json()
    assert len(units) >= 8

    # Query nearby units
    nearby_resp = client.get("/units/nearby?latitude=12.9716&longitude=77.5946&max_distance_km=20")
    assert nearby_resp.status_code == 200
    nearby = nearby_resp.json()
    assert len(nearby) > 0
    assert "distance_km" in nearby[0]
    assert "estimated_eta_minutes" in nearby[0]
    # Check that distance is sorted ascending
    for i in range(len(nearby) - 1):
        if nearby[i].get("status") == "available" and nearby[i+1].get("status") == "available":
            assert nearby[i]["distance_km"] <= nearby[i+1]["distance_km"]


def test_dispatch_assignment_workflow(client):
    # Create new incident
    create_resp = client.post("/incidents", json={
        "description": "Structure fire with visible flames and black smoke from 2nd floor",
        "latitude": 12.9650,
        "longitude": 77.5850
    })
    incident_id = create_resp.json()["id"]

    # Assign Unit
    assign_payload = {
        "unit_id": "UNIT-FIRE-201",
        "dispatcher_id": "DISP-OPERATOR-9",
        "notes": "Proceed with siren, primary water tender deployed"
    }
    assign_resp = client.post(f"/incidents/{incident_id}/assign", json=assign_payload)
    assert assign_resp.status_code == 200
    data = assign_resp.json()
    assert data["status"] == "success"

    # Verify incident updated
    inc_resp = client.get(f"/incidents/{incident_id}")
    assert inc_resp.json()["status"] == "dispatched"
    assert inc_resp.json()["assigned_unit_id"] == "UNIT-FIRE-201"

    # Verify unit status
    unit_resp = client.get("/units?unit_type=fire_engine")
    unit_201 = next(u for u in unit_resp.json() if u["id"] == "UNIT-FIRE-201")
    assert unit_201["status"] == "dispatched"
    assert unit_201["assigned_incident_id"] == incident_id


def test_unit_location_update(client):
    payload = {
        "latitude": 12.9700,
        "longitude": 77.5900,
        "heading": 90.0,
        "speed_kmh": 45.0,
        "is_simulated": True
    }
    resp = client.patch("/units/UNIT-AMB-101/location", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["latitude"] == 12.9700
    assert data["longitude"] == 77.5900

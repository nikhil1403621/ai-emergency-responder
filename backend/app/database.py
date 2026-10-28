import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emergency_response.db")
DB_PATH = os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Incidents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            address_hint TEXT,
            category TEXT NOT NULL DEFAULT 'other_uncertain',
            urgency TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'reported',
            reporter_name TEXT,
            reporter_contact TEXT,
            requires_review INTEGER NOT NULL DEFAULT 1,
            assigned_unit_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        # 2. Incident AI Assessments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_assessments (
            id TEXT PRIMARY KEY,
            incident_id TEXT NOT NULL,
            model_version TEXT NOT NULL,
            suggested_category TEXT NOT NULL,
            suggested_urgency TEXT NOT NULL,
            confidence REAL NOT NULL,
            uncertainty REAL NOT NULL,
            requires_review INTEGER NOT NULL,
            reasoning TEXT NOT NULL,
            matched_keywords TEXT NOT NULL,
            recommended_unit_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
        );
        """)

        # 3. Response Units table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS response_units (
            id TEXT PRIMARY KEY,
            call_sign TEXT NOT NULL,
            unit_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            base_station TEXT NOT NULL,
            assigned_incident_id TEXT,
            last_updated TEXT NOT NULL
        );
        """)

        # 4. Dispatch Assignments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispatch_assignments (
            id TEXT PRIMARY KEY,
            incident_id TEXT NOT NULL,
            unit_id TEXT NOT NULL,
            dispatcher_id TEXT NOT NULL,
            dispatcher_notes TEXT,
            assigned_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE,
            FOREIGN KEY (unit_id) REFERENCES response_units(id)
        );
        """)

        # 5. Incident Events table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS incident_events (
            id TEXT PRIMARY KEY,
            incident_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            from_status TEXT,
            to_status TEXT,
            details TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
        );
        """)

        # 6. Unit Locations history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS unit_locations (
            id TEXT PRIMARY KEY,
            unit_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            heading REAL,
            speed_kmh REAL,
            is_simulated INTEGER NOT NULL DEFAULT 1,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (unit_id) REFERENCES response_units(id) ON DELETE CASCADE
        );
        """)

        # Seed initial response units if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM response_units;")
        count = cursor.fetchone()["count"]
        if count == 0:
            seed_units = [
                ("UNIT-AMB-101", "Medic Ambulance 101", "ambulance", "available", 12.9716, 77.5946, "Central Medical Center", None, "2026-10-28T00:00:00Z"),
                ("UNIT-AMB-102", "Trauma Rescue 102", "ambulance", "available", 12.9850, 77.6050, "East Side General", None, "2026-10-28T00:00:00Z"),
                ("UNIT-FIRE-201", "Engine 201 Heavy Ladder", "fire_engine", "available", 12.9650, 77.5850, "Downtown Fire Station 4", None, "2026-10-28T00:00:00Z"),
                ("UNIT-FIRE-202", "Rescue Squad 202", "fire_engine", "available", 12.9900, 77.5700, "North Fire House", None, "2026-10-28T00:00:00Z"),
                ("UNIT-POL-301", "Patrol Cruiser 301", "patrol_car", "available", 12.9750, 77.6100, "Metropolitan Precinct 1", None, "2026-10-28T00:00:00Z"),
                ("UNIT-POL-302", "Rapid Response 302", "patrol_car", "available", 12.9550, 77.5950, "South Sector Precinct 5", None, "2026-10-28T00:00:00Z"),
                ("UNIT-RESC-401", "Disaster Rescue Team 401", "rescue_team", "available", 12.9600, 77.6200, "Emergency Operations Depot", None, "2026-10-28T00:00:00Z"),
                ("UNIT-UTIL-501", "Hazard Utility Truck 501", "utility_truck", "available", 12.9800, 77.5600, "Municipal Works Yard", None, "2026-10-28T00:00:00Z"),
            ]
            cursor.executemany("""
                INSERT INTO response_units (id, call_sign, unit_type, status, latitude, longitude, base_station, assigned_incident_id, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, seed_units)

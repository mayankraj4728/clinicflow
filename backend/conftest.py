"""Pytest fixtures for the ClinicFlow backend test suite.

The DATABASE_URL is overridden *before* the application is imported so the
tests run against an isolated SQLite database and never touch PostgreSQL.
"""

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_clinicflow.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import Base, engine, SessionLocal
from app import models  # noqa: F401  (ensures models are registered on Base)


@pytest.fixture(scope="session", autouse=True)
def database():
    """Create the schema once for the whole session, drop it at the end."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Truncate the appointments table between tests for isolation."""
    db = SessionLocal()
    try:
        db.query(models.Appointment).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture()
def sample_appointment(client):
    """Create one appointment and return its JSON representation."""
    response = client.post(
        "/api/appointments",
        json={
            "patient_name": "Aarav Sharma",
            "doctor": "Dr. Meera Iyer",
            "department": "Cardiology",
            "appointment_type": "CONSULTATION",
        },
    )
    assert response.status_code == 201
    return response.json()

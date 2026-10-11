"""API tests for the ClinicFlow backend.

Covers health/readiness probes and the full appointment CRUD lifecycle plus
the stats aggregation endpoint.
"""


def test_health(client):
    assert client.get("/health").json() == {"status": "UP"}


def test_root(client):
    body = client.get("/").json()
    assert body["service"] == "ClinicFlow API"
    assert body["docs"] == "/docs"


def test_ready_checks_database(client):
    assert client.get("/ready").json() == {"status": "READY"}


def test_create_appointment(client):
    response = client.post(
        "/api/appointments",
        json={
            "patient_name": "Priya Nair",
            "doctor": "Dr. Rajesh Gupta",
            "department": "Dermatology",
            "appointment_type": "FOLLOW_UP",
            "reason": "Routine skin check",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["patient_name"] == "Priya Nair"
    assert body["status"] == "SCHEDULED"
    assert body["id"] > 0


def test_create_requires_patient_name(client):
    response = client.post("/api/appointments", json={"doctor": "Dr. X"})
    assert response.status_code == 422


def test_rejects_invalid_status(client):
    response = client.post(
        "/api/appointments",
        json={"patient_name": "Test Patient", "status": "NOT_A_STATUS"},
    )
    assert response.status_code == 422


def test_list_appointments(client, sample_appointment):
    response = client.get("/api/appointments")
    assert response.status_code == 200
    appointments = response.json()
    assert isinstance(appointments, list)
    assert any(a["id"] == sample_appointment["id"] for a in appointments)


def test_get_appointment_by_id(client, sample_appointment):
    response = client.get(f"/api/appointments/{sample_appointment['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_appointment["id"]


def test_get_missing_appointment_returns_404(client):
    assert client.get("/api/appointments/999999").status_code == 404


def test_update_appointment_status(client, sample_appointment):
    response = client.put(
        f"/api/appointments/{sample_appointment['id']}",
        json={"status": "COMPLETED", "doctor": "Dr. Meera Iyer"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


def test_update_missing_appointment_returns_404(client):
    assert client.put("/api/appointments/999999", json={"status": "CANCELLED"}).status_code == 404


def test_delete_appointment(client, sample_appointment):
    deleted = client.delete(f"/api/appointments/{sample_appointment['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/appointments/{sample_appointment['id']}").status_code == 404


def test_stats_reflects_statuses(client):
    client.post("/api/appointments", json={"patient_name": "One", "status": "SCHEDULED"})
    client.post("/api/appointments", json={"patient_name": "Two", "status": "COMPLETED"})
    client.post("/api/appointments", json={"patient_name": "Three", "status": "CANCELLED"})

    stats = client.get("/api/appointments/stats").json()
    assert stats["total"] == 3
    assert stats["scheduled"] == 1
    assert stats["completed"] == 1
    assert stats["cancelled"] == 1

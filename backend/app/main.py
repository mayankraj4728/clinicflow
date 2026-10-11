from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator

from .config import settings
from .db import Base, engine, get_db
from .models import Appointment
from .schemas import AppointmentCreate, AppointmentOut, AppointmentUpdate, StatsOut

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
# Expose Prometheus metrics on /metrics for the observability stack.
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.on_event("startup")
def startup() -> None:
    # Production containers run Alembic before Uvicorn starts; create_all keeps
    # local runs and the test suite self-contained.
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict:
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health")
def health() -> dict:
    """Liveness probe: is the process up?"""
    return {"status": "UP"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    """Readiness probe: can we actually reach the database?"""
    db.execute(select(func.count(Appointment.id)))
    return {"status": "READY"}


@app.get("/api/appointments", response_model=list[AppointmentOut])
def list_appointments(db: Session = Depends(get_db)):
    """Return every appointment, newest first."""
    return list(db.scalars(select(Appointment).order_by(Appointment.id.desc())))


@app.get("/api/appointments/stats", response_model=StatsOut)
def appointment_stats(db: Session = Depends(get_db)):
    """Aggregate appointment counts per status for the dashboard KPI cards."""
    rows = db.execute(
        select(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status)
    ).all()
    counts = {status_value: count for status_value, count in rows}
    return StatsOut(
        total=sum(counts.values()),
        scheduled=counts.get("SCHEDULED", 0),
        checkedIn=counts.get("CHECKED_IN", 0),
        completed=counts.get("COMPLETED", 0),
        cancelled=counts.get("CANCELLED", 0),
    )


@app.get("/api/appointments/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@app.post(
    "/api/appointments",
    response_model=AppointmentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    appointment = Appointment(**payload.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@app.put("/api/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(appointment, key, value)
    db.commit()
    db.refresh(appointment)
    return appointment


@app.delete(
    "/api/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(appointment)
    db.commit()

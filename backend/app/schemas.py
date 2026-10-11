from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AppointmentStatus = Literal["SCHEDULED", "CHECKED_IN", "COMPLETED", "CANCELLED"]
AppointmentType = Literal["CONSULTATION", "FOLLOW_UP", "EMERGENCY", "SCREENING"]


class AppointmentCreate(BaseModel):
    """Payload accepted when booking a new appointment."""

    patient_name: str = Field(min_length=1, max_length=150)
    patient_email: str = Field(default="", max_length=150)
    doctor: str = Field(default="Unassigned", max_length=150)
    department: str = Field(default="General Medicine", max_length=100)
    appointment_type: AppointmentType = "CONSULTATION"
    reason: str = ""
    status: AppointmentStatus = "SCHEDULED"


class AppointmentUpdate(BaseModel):
    """Partial update payload - every field is optional."""

    patient_name: str | None = Field(default=None, min_length=1, max_length=150)
    patient_email: str | None = Field(default=None, max_length=150)
    doctor: str | None = Field(default=None, max_length=150)
    department: str | None = Field(default=None, max_length=100)
    appointment_type: AppointmentType | None = None
    reason: str | None = None
    status: AppointmentStatus | None = None


class AppointmentOut(AppointmentCreate):
    """Appointment returned by the API."""

    id: int
    scheduled_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    """Aggregated appointment counts used by the dashboard KPI cards."""

    total: int
    scheduled: int
    checkedIn: int
    completed: int
    cancelled: int

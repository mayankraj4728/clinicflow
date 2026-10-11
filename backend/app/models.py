from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Appointment(Base):
    """A single patient appointment in the clinic scheduling system."""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    patient_email: Mapped[str] = mapped_column(String(150), default="")
    doctor: Mapped[str] = mapped_column(String(150), default="Unassigned")
    department: Mapped[str] = mapped_column(String(100), default="General Medicine")
    appointment_type: Mapped[str] = mapped_column(String(30), default="CONSULTATION")
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="SCHEDULED")
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

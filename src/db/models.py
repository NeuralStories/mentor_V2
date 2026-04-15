from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from src.db.database import Base

class DBWorkerProfile(Base):
    __tablename__ = "workers"

    worker_id = Column(String, primary_key=True, index=True)
    name = Column(String, default="")
    department = Column(String, index=True)
    role = Column(String, default="")
    location = Column(String, default="")
    hire_date = Column(String, nullable=True)
    manager = Column(String, default="")
    access_level = Column(String, default="all")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBEscalationTicket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String, primary_key=True, index=True)
    worker_id = Column(String, index=True)
    category = Column(String, index=True)
    urgency = Column(String)
    reason = Column(Text)
    status = Column(String, default="open")
    assigned_to = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

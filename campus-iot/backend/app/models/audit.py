"""
Audit log model - Tracks who changed what and when
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(50), nullable=False)  # create, update, delete, acknowledge, etc.
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    before_data = Column(JSONB, nullable=True)
    after_data = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

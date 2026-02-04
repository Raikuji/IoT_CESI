"""
Anomaly model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=True)
    anomaly_type = Column(String(50), nullable=False)  # spike, stuck, drift
    message = Column(Text)
    severity = Column(String(20), default="warning")
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

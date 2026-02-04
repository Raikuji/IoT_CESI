"""
Alert models
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)
    type = Column(String(50), nullable=False)
    message = Column(Text)
    severity = Column(String(20), default="warning")
    is_acknowledged = Column(Boolean, default=False)
    escalation_level = Column(Integer, default=0)
    escalated_from_alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Relationships
    sensor = relationship("Sensor", back_populates="alerts")
    rule = relationship("AlertRule", back_populates="alerts")


class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=True)
    sensor_type = Column(String(50), nullable=True)
    room_id = Column(String(50), nullable=True)
    condition = Column(String(20), nullable=False)  # >, <, ==, >=, <=
    threshold = Column(Float, nullable=False)
    message = Column(Text)
    severity = Column(String(20), default="warning")
    is_active = Column(Boolean, default=True)
    active_days = Column(JSONB, default=list)
    active_time_start = Column(String(5), nullable=True)  # HH:MM
    active_time_end = Column(String(5), nullable=True)    # HH:MM
    cooldown_minutes = Column(Integer, default=5)
    escalation_minutes = Column(Integer, nullable=True)
    escalation_severity = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sensor = relationship("Sensor", back_populates="alert_rules")
    alerts = relationship("Alert", back_populates="rule")

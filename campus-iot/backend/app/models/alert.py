"""
Alert models
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    type = Column(String(50), nullable=False)
    message = Column(Text)
    severity = Column(String(20), default="warning")
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Relationships
    sensor = relationship("Sensor", back_populates="alerts")


class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    condition = Column(String(20), nullable=False)  # >, <, ==, >=, <=
    threshold = Column(Float, nullable=False)
    message = Column(Text)
    severity = Column(String(20), default="warning")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sensor = relationship("Sensor", back_populates="alert_rules")

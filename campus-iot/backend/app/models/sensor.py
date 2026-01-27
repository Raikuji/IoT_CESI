"""
Sensor models
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    location = Column(String(100), default="C101")
    unit = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    data = relationship("SensorData", back_populates="sensor")
    alerts = relationship("Alert", back_populates="sensor")
    alert_rules = relationship("AlertRule", back_populates="sensor")


class SensorData(Base):
    __tablename__ = "sensor_data"
    
    time = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())
    sensor_id = Column(Integer, ForeignKey("sensors.id"), primary_key=True)
    value = Column(Float, nullable=False)
    
    # Relationships
    sensor = relationship("Sensor", back_populates="data")

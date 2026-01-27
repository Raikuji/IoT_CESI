"""
Actuator models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class Actuator(Base):
    __tablename__ = "actuators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    location = Column(String(100), default="C101")
    current_value = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    commands = relationship("ActuatorCommand", back_populates="actuator")


class ActuatorCommand(Base):
    __tablename__ = "actuator_commands"
    
    id = Column(Integer, primary_key=True, index=True)
    actuator_id = Column(Integer, ForeignKey("actuators.id"))
    command_value = Column(Integer, nullable=False)
    source = Column(String(50), default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    actuator = relationship("Actuator", back_populates="commands")

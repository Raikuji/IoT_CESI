"""
Settings and Preferences models - Synced to Supabase
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from db.database import Base


class PlacedSensor(Base):
    """Sensors placed on the building plan by users"""
    __tablename__ = "placed_sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(50), nullable=False, index=True)
    sensor_type = Column(String(50), nullable=False, index=True)
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)
    position_z = Column(Float, default=0)
    name = Column(String(100), nullable=True)
    current_value = Column(Float, nullable=True)
    status = Column(String(20), default="pending")
    placed_by_user_id = Column(Integer, nullable=True)
    placed_by_email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_update = Column(DateTime(timezone=True), nullable=True)


class SystemSetting(Base):
    """Global system settings"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")
    category = Column(String(50), default="general", index=True)
    description = Column(Text, nullable=True)
    updated_by_user_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserPreference(Base):
    """User-specific preferences"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    theme = Column(String(20), default="dark")
    default_floor = Column(String(20), default="RDC")
    notifications_enabled = Column(Boolean, default=True)
    email_alerts = Column(Boolean, default=False)
    sound_alerts = Column(Boolean, default=True)
    dashboard_layout = Column(JSONB, default={})
    favorite_rooms = Column(JSONB, default=[])
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

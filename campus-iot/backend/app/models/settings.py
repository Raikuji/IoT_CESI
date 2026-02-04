"""
Settings and Preferences models - Synced to Supabase
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
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


class SensorEnergySetting(Base):
    """Energy settings per placed sensor"""
    __tablename__ = "sensor_energy_settings"

    id = Column(Integer, primary_key=True, index=True)
    placed_sensor_id = Column(Integer, ForeignKey("placed_sensors.id"), nullable=False, unique=True, index=True)
    energy_enabled = Column(Boolean, default=False)
    refresh_interval = Column(Integer, default=120)
    refresh_interval_night = Column(Integer, default=300)
    disable_live = Column(Boolean, default=True)
    profile = Column(String(20), default="normal")
    schedule_enabled = Column(Boolean, default=False)
    schedule_profile = Column(String(20), default="eco")
    schedule_days = Column(JSONB, default=[])
    schedule_start = Column(String(10), default="22:00")
    schedule_end = Column(String(10), default="06:00")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

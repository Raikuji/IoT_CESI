"""
Integration models: webhooks & exports
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from db.database import Base


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(200), nullable=True)
    event_types = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExportConfig(Base):
    __tablename__ = "export_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    resource = Column(String(50), nullable=False)  # alerts, sensors, anomalies
    format = Column(String(10), default="csv")    # csv, json
    interval_minutes = Column(Integer, default=1440)
    time_window_hours = Column(Integer, default=24)
    target = Column(String(20), default="file")   # file, webhook
    webhook_id = Column(Integer, ForeignKey("webhook_endpoints.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

"""
Integration schemas
"""
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List


class WebhookBase(BaseModel):
    name: str
    url: HttpUrl
    secret: Optional[str] = None
    event_types: List[str] = []
    is_active: Optional[bool] = True


class WebhookCreate(WebhookBase):
    pass


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    secret: Optional[str] = None
    event_types: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookResponse(WebhookBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExportConfigBase(BaseModel):
    name: str
    resource: str
    format: str = "csv"
    interval_minutes: int = 1440
    time_window_hours: int = 24
    target: str = "file"
    webhook_id: Optional[int] = None
    is_active: Optional[bool] = True


class ExportConfigCreate(ExportConfigBase):
    pass


class ExportConfigUpdate(BaseModel):
    name: Optional[str] = None
    resource: Optional[str] = None
    format: Optional[str] = None
    interval_minutes: Optional[int] = None
    time_window_hours: Optional[int] = None
    target: Optional[str] = None
    webhook_id: Optional[int] = None
    is_active: Optional[bool] = None


class ExportConfigResponse(ExportConfigBase):
    id: int
    last_run_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

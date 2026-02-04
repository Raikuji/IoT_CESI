"""
Integrations API (webhooks + exports)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db import get_db
from api.auth import get_current_admin
from models.integration import WebhookEndpoint, ExportConfig
from schemas.integration import (
    WebhookCreate, WebhookUpdate, WebhookResponse,
    ExportConfigCreate, ExportConfigUpdate, ExportConfigResponse
)
from services.webhook_service import dispatch_webhooks
from services.export_service import run_export

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# Webhooks
@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(current_user=Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(WebhookEndpoint).order_by(WebhookEndpoint.created_at.desc()).all()


@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(
    data: WebhookCreate,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    endpoint = WebhookEndpoint(**data.model_dump(mode="json"))
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


@router.patch("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    data: WebhookUpdate,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook introuvable")

    for key, value in data.model_dump(exclude_unset=True, mode="json").items():
        setattr(endpoint, key, value)

    db.commit()
    db.refresh(endpoint)
    return endpoint


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook introuvable")
    db.delete(endpoint)
    db.commit()
    return {"success": True}


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook introuvable")

    payload = {
        "event": "webhook.test",
        "message": "Test de webhook Campus IoT"
    }
    dispatch_webhooks(db, "webhook.test", payload)
    return {"success": True}


# Exports
@router.get("/exports", response_model=List[ExportConfigResponse])
async def list_exports(current_user=Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(ExportConfig).order_by(ExportConfig.created_at.desc()).all()


@router.post("/exports", response_model=ExportConfigResponse)
async def create_export(
    data: ExportConfigCreate,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    config = ExportConfig(**data.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.patch("/exports/{export_id}", response_model=ExportConfigResponse)
async def update_export(
    export_id: int,
    data: ExportConfigUpdate,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    config = db.query(ExportConfig).filter(ExportConfig.id == export_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Export introuvable")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(config, key, value)

    db.commit()
    db.refresh(config)
    return config


@router.delete("/exports/{export_id}")
async def delete_export(
    export_id: int,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    config = db.query(ExportConfig).filter(ExportConfig.id == export_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Export introuvable")
    db.delete(config)
    db.commit()
    return {"success": True}


@router.post("/exports/{export_id}/run")
async def run_export_now(
    export_id: int,
    current_user=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    config = db.query(ExportConfig).filter(ExportConfig.id == export_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Export introuvable")

    result = run_export(db, config)
    return {"success": True, "export": result}

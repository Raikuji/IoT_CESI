"""
Backups API - admin only
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List

from api.auth import get_current_admin
from services.backup_service import list_backups, run_backup, restore_backup, cleanup_old_backups

router = APIRouter(prefix="/backups", tags=["Backups"])


class BackupResponse(BaseModel):
    name: str
    size: int
    created_at: str


@router.get("", response_model=List[BackupResponse])
async def get_backups(current_user=Depends(get_current_admin)):
    return list_backups()


@router.post("/run")
async def create_backup(current_user=Depends(get_current_admin)):
    try:
        result = run_backup()
        return {"success": True, "backup": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{filename}")
async def restore_backup_file(
    filename: str,
    confirm: bool = Query(default=False),
    current_user=Depends(get_current_admin)
):
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation requise")
    try:
        result = restore_backup(filename)
        return {"success": True, "backup": result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup introuvable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_backups(
    retention_days: int = Query(default=7, ge=1),
    current_user=Depends(get_current_admin)
):
    deleted = cleanup_old_backups(retention_days)
    return {"success": True, "deleted": deleted}

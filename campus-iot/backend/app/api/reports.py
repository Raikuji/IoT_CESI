"""
Report Issue API - Allows users to report problems in rooms via QR code scanning
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter(prefix="/reports", tags=["Reports"])

# In-memory storage (replace with database in production)
reports_db = []

class ReportCreate(BaseModel):
    room_id: str
    room_name: Optional[str] = None
    issue_type: str
    urgency: str = "medium"  # low, medium, high
    description: Optional[str] = None
    has_photo: bool = False

class Report(BaseModel):
    ticket_id: str
    room_id: str
    room_name: Optional[str]
    issue_type: str
    urgency: str
    description: Optional[str]
    has_photo: bool
    status: str = "open"  # open, in_progress, resolved
    created_at: str
    updated_at: Optional[str] = None
    assigned_to: Optional[str] = None

class ReportUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None

@router.post("", response_model=Report)
async def create_report(report: ReportCreate):
    """
    Create a new issue report for a room.
    Called when users scan QR code and submit a problem.
    """
    # Generate ticket ID
    now = datetime.now()
    prefix = report.room_id[:2] if report.room_id else "XX"
    ticket_id = f"{prefix}-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    
    new_report = Report(
        ticket_id=ticket_id,
        room_id=report.room_id,
        room_name=report.room_name,
        issue_type=report.issue_type,
        urgency=report.urgency,
        description=report.description,
        has_photo=report.has_photo,
        status="open",
        created_at=now.isoformat()
    )
    
    reports_db.append(new_report.dict())
    
    # TODO: Send WebSocket notification to admins
    # TODO: Send email notification if urgent
    
    return new_report

@router.get("", response_model=List[Report])
async def get_reports(
    status: Optional[str] = None,
    room_id: Optional[str] = None,
    urgency: Optional[str] = None,
    limit: int = 50
):
    """
    Get all reports with optional filtering.
    """
    filtered = reports_db.copy()
    
    if status:
        filtered = [r for r in filtered if r.get("status") == status]
    if room_id:
        filtered = [r for r in filtered if r.get("room_id") == room_id]
    if urgency:
        filtered = [r for r in filtered if r.get("urgency") == urgency]
    
    # Sort by creation date descending
    filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return filtered[:limit]

@router.get("/{ticket_id}", response_model=Report)
async def get_report(ticket_id: str):
    """
    Get a specific report by ticket ID.
    """
    for report in reports_db:
        if report.get("ticket_id") == ticket_id:
            return report
    raise HTTPException(status_code=404, detail="Report not found")

@router.patch("/{ticket_id}", response_model=Report)
async def update_report(ticket_id: str, update: ReportUpdate):
    """
    Update a report status or assignment.
    """
    for i, report in enumerate(reports_db):
        if report.get("ticket_id") == ticket_id:
            if update.status:
                reports_db[i]["status"] = update.status
            if update.assigned_to:
                reports_db[i]["assigned_to"] = update.assigned_to
            reports_db[i]["updated_at"] = datetime.now().isoformat()
            return reports_db[i]
    raise HTTPException(status_code=404, detail="Report not found")

@router.get("/stats/summary")
async def get_reports_summary():
    """
    Get summary statistics of reports.
    """
    total = len(reports_db)
    by_status = {
        "open": len([r for r in reports_db if r.get("status") == "open"]),
        "in_progress": len([r for r in reports_db if r.get("status") == "in_progress"]),
        "resolved": len([r for r in reports_db if r.get("status") == "resolved"])
    }
    by_urgency = {
        "high": len([r for r in reports_db if r.get("urgency") == "high"]),
        "medium": len([r for r in reports_db if r.get("urgency") == "medium"]),
        "low": len([r for r in reports_db if r.get("urgency") == "low"])
    }
    by_type = {}
    for report in reports_db:
        issue_type = report.get("issue_type", "other")
        by_type[issue_type] = by_type.get(issue_type, 0) + 1
    
    return {
        "total": total,
        "by_status": by_status,
        "by_urgency": by_urgency,
        "by_type": by_type
    }

"""
Export service for scheduled exports
"""
import os
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List

from config import settings
from models import Alert, Sensor, SensorData, Anomaly
from models.integration import ExportConfig, WebhookEndpoint
from services.webhook_service import send_webhook

EXPORT_DIR = os.getenv("EXPORT_DIR", "/app/exports")


def ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)


def _fetch_data(db, resource: str, hours: int) -> List[Dict]:
    since = datetime.utcnow() - timedelta(hours=hours)
    if resource == "alerts":
        rows = db.query(Alert).filter(Alert.created_at >= since).all()
        return [
            {
                "id": r.id,
                "sensor_id": r.sensor_id,
                "type": r.type,
                "message": r.message,
                "severity": r.severity,
                "is_acknowledged": r.is_acknowledged,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in rows
        ]
    if resource == "anomalies":
        rows = db.query(Anomaly).filter(Anomaly.created_at >= since).all()
        return [
            {
                "id": r.id,
                "sensor_id": r.sensor_id,
                "anomaly_type": r.anomaly_type,
                "message": r.message,
                "severity": r.severity,
                "metadata": r.metadata,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in rows
        ]
    if resource == "sensors":
        rows = db.query(Sensor).all()
        data = []
        for s in rows:
            latest = db.query(SensorData).filter(SensorData.sensor_id == s.id).order_by(SensorData.time.desc()).first()
            data.append({
                "id": s.id,
                "name": s.name,
                "type": s.type,
                "location": s.location,
                "latest_value": latest.value if latest else None,
                "latest_time": latest.time.isoformat() if latest and latest.time else None
            })
        return data
    return []


def _write_csv(path: str, rows: List[Dict]):
    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: str, rows: List[Dict]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def run_export(db, config: ExportConfig) -> Dict:
    ensure_export_dir()
    data = _fetch_data(db, config.resource, config.time_window_hours)
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"export-{config.name}-{timestamp}.{config.format}"
    filepath = os.path.join(EXPORT_DIR, filename)

    if config.format == "json":
        _write_json(filepath, data)
    else:
        _write_csv(filepath, data)

    # Optional webhook target
    if config.target == "webhook" and config.webhook_id:
        endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == config.webhook_id).first()
        payload = {
            "event": "export.ready",
            "config_id": config.id,
            "name": config.name,
            "resource": config.resource,
            "format": config.format,
            "created_at": datetime.utcnow().isoformat(),
            "data": data
        }
        if endpoint:
            send_webhook(endpoint, "export.ready", payload)

    return {"name": filename, "path": filepath, "count": len(data)}


def run_due_exports(db) -> int:
    now = datetime.utcnow()
    configs = db.query(ExportConfig).filter(ExportConfig.is_active == True).all()
    ran = 0
    for cfg in configs:
        last = cfg.last_run_at
        if last and (now - last.replace(tzinfo=None)).total_seconds() < cfg.interval_minutes * 60:
            continue
        run_export(db, cfg)
        cfg.last_run_at = now
        db.commit()
        ran += 1
    return ran

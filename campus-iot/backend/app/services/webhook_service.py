"""
Webhook delivery service
"""
import hmac
import hashlib
import json
import logging
from typing import List, Dict
import httpx

from models.integration import WebhookEndpoint

logger = logging.getLogger(__name__)


def _sign_payload(secret: str, payload: Dict) -> str:
    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()


def _discord_payload(event_type: str, payload: Dict) -> Dict:
    message = payload.get("message") or payload.get("description") or ""
    room = payload.get("room_id") or payload.get("room") or "—"
    severity = payload.get("severity") or "—"
    sensor_id = payload.get("sensor_id")
    event_label = {
        "alert.triggered": "Alerte déclenchée",
        "alert.escalated": "Alerte escaladée",
        "anomaly.detected": "Anomalie détectée",
        "export.ready": "Export prêt",
        "webhook.test": "Test webhook"
    }.get(event_type, event_type)
    emoji = {
        "alert.triggered": "🚨",
        "alert.escalated": "🔥",
        "anomaly.detected": "⚠️",
        "export.ready": "📦",
        "webhook.test": "✅"
    }.get(event_type, "🔔")

    fields = [
        {"name": "Salle", "value": str(room), "inline": True},
        {"name": "Sévérité", "value": str(severity), "inline": True}
    ]
    if sensor_id is not None:
        fields.append({"name": "Capteur", "value": f"#{sensor_id}", "inline": True})

    embed = {
        "title": f"{emoji} {event_label}",
        "description": message or "—",
        "fields": fields
    }

    return {
        "username": "Campus IoT",
        "embeds": [embed]
    }


def send_webhook(endpoint: WebhookEndpoint, event_type: str, payload: Dict):
    if not endpoint.is_active:
        return
    if endpoint.event_types and event_type not in endpoint.event_types and event_type != "webhook.test":
        return

    headers = {
        "Content-Type": "application/json",
        "X-Campus-Event": event_type
    }
    if endpoint.secret:
        headers["X-Campus-Signature"] = _sign_payload(endpoint.secret, payload)

    try:
        json_payload = payload
        if "discord.com/api/webhooks" in endpoint.url:
            json_payload = _discord_payload(event_type, payload)
        with httpx.Client(timeout=5.0) as client:
            response = client.post(endpoint.url, json=json_payload, headers=headers)
            if response.status_code >= 400:
                logger.warning(
                    "Webhook delivery failed (%s) for %s: %s",
                    response.status_code,
                    endpoint.url,
                    response.text
                )
    except Exception as exc:
        logger.exception("Webhook delivery error for %s: %s", endpoint.url, exc)
        return


def dispatch_webhooks(db, event_type: str, payload: Dict):
    endpoints: List[WebhookEndpoint] = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.is_active == True
    ).all()

    for endpoint in endpoints:
        send_webhook(endpoint, event_type, payload)

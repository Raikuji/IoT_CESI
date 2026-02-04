"""
Webhook delivery service
"""
import hmac
import hashlib
import json
from typing import List, Dict
import httpx

from models.integration import WebhookEndpoint


def _sign_payload(secret: str, payload: Dict) -> str:
    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()


def send_webhook(endpoint: WebhookEndpoint, event_type: str, payload: Dict):
    if not endpoint.is_active:
        return
    if endpoint.event_types and event_type not in endpoint.event_types:
        return

    headers = {
        "Content-Type": "application/json",
        "X-Campus-Event": event_type
    }
    if endpoint.secret:
        headers["X-Campus-Signature"] = _sign_payload(endpoint.secret, payload)

    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(endpoint.url, json=payload, headers=headers)
    except Exception:
        return


def dispatch_webhooks(db, event_type: str, payload: Dict):
    endpoints: List[WebhookEndpoint] = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.is_active == True
    ).all()

    for endpoint in endpoints:
        send_webhook(endpoint, event_type, payload)
